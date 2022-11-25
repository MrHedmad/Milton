import datetime
import logging
import re
from email.message import EmailMessage

import aiosmtplib
import discord
import markdown
from aiosqlite import IntegrityError
from discord import Embed, Forbidden, Interaction, Member, Role, app_commands, ui
from discord.ext.commands import GroupCog

from milton.core.bot import Milton
from milton.core.config import CONFIG
from milton.core.errors import MiltonError

log = logging.getLogger(__name__)


class NotSubscribedError(MiltonError):
    """The user is not subscribed to the announcements"""

    pass


class RoleDoesNotExistError(MiltonError):
    """The role does not exist anymore"""

    pass


class RoleAlreadyAnnouncerError(MiltonError):
    pass


class RoleNotAllowedError(MiltonError):
    """The role mentioned is not allowed to send announcements."""

    pass


class InvalidEmailError(MiltonError):
    """Raised when an email is not valid"""

    pass


class GuildMissingAnnouncementChannel(MiltonError):
    pass


class UserCannotSendAnnouncements(MiltonError):
    pass


EMAIL_VALIDATION = re.compile(
    r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"""
)

MILTON_EMAIL_FOOTER = "\n\n".join(
    (
        "",
        "~~~~~~~~~~~~~~~~~~",
        "This email was sent by a bot. Please do not reply to it.",
        "For any additional information, refer to the user mentioned above.",
        "",
        "If you believe that you are receiving these messages by error, and "
        "cannot contact the sender, feel free to block this email address.",
    )
)


class AnnouncementModal(ui.Modal, title="New Announcement"):
    announcement_title = ui.TextInput(label="Title", placeholder="Announcement Title")
    announcement_body = ui.TextInput(
        label="Message",
        placeholder="Type something...",
        max_length=2500,
        style=discord.TextStyle.paragraph,
    )

    async def on_submit(self, interaction: Interaction, /) -> None:
        await interaction.response.send_message(
            "Got it! Will announce soon!", ephemeral=True
        )
        await _send_announcement(
            interaction.client, interaction=interaction, announcement=self
        )

    async def on_error(self, interaction: Interaction, error: Exception, /) -> None:
        return await super().on_error(interaction, error)


async def _unsubscribe(bot: Milton, member_id: int, guild_id: int):
    """Call the DB to unsubscribe a certain member from announcements"""
    await bot.db.execute(
        (
            "DELETE FROM announcement_user_data WHERE "
            "guild_id = :guild_id AND user_id = :member_id"
        ),
        (guild_id, member_id),
    )
    await bot.db.commit()


async def _subscribe(bot: Milton, member_id: int, guild_id: int, email: str):
    """Call the DB to subscribe a certain member from announcements"""
    match = EMAIL_VALIDATION.match(email)
    if not match:
        raise InvalidEmailError(f"Invalid email: {email}")

    email = match.group()

    await bot.db.execute(
        (
            "DELETE FROM announcement_user_data WHERE "
            "guild_id = :guild_id AND user_id = :member_id"
        ),
        (guild_id, member_id),
    )
    await bot.db.execute(
        (
            "INSERT INTO announcement_user_data "
            "(user_id, guild_id, user_email) "
            "VALUES (:member_id, :guild_id, :email)"
        ),
        (member_id, guild_id, email),
    )
    await bot.db.commit()


async def _add_announce_role(bot: Milton, role_id: int, guild_id: int):
    try:
        await bot.db.execute(
            (
                "INSERT INTO announcement_roles "
                "(guild_id, role) "
                "VALUES (:guild_id, :role_id)"
            ),
            (guild_id, role_id),
        )
        await bot.db.commit()
    except IntegrityError:
        # The role already exists, we violated the "UNIQUE" constraint on 'role'
        raise RoleAlreadyAnnouncerError()


async def _remove_announce_role(bot: Milton, role: int, guild_id: int):
    await bot.db.execute(
        (
            "DELETE FROM announcement_roles WHERE "
            "guild_id = :guild_id AND role = :role"
        ),
        (guild_id, role),
    )
    await bot.db.commit()


async def _send_announcement(
    bot: Milton, interaction: Interaction, announcement: AnnouncementModal
):
    """Send an announcement."""
    # This function does not check if the sender is authorized to send the announcement.
    # It also does NOT check if the guild has an announcement channel set.
    # It will probably fail horribly if called out-of-context
    guild_id = interaction.guild_id
    # 1. Generate an embed
    announcement_embed = (
        Embed(
            title=announcement.announcement_title.value,
            description=announcement.announcement_body.value,
            timestamp=datetime.datetime.utcnow(),
            color=discord.Color.og_blurple(),
        )
        .set_author(
            name=interaction.user.display_name, icon_url=interaction.user.avatar.url
        )
        .set_footer(text="Milton Announcements service")
    )
    # 2. Send the embed to the announcement channel for the guild
    async with bot.db.execute(
        (
            "SELECT announcement_channel FROM announcement_guild_config WHERE "
            "guild_id = :guild_id"
        ),
        (guild_id,),
    ) as cursor:
        announcement_channel_id = await cursor.fetchone()

    assert (
        announcement_channel_id is not None
    ), "Failed to fetch target announcement channel"
    announcement_channel = await bot.fetch_channel(announcement_channel_id[0])
    await announcement_channel.send(embed=announcement_embed)

    if CONFIG.announcements.email is None or CONFIG.announcements.password is None:
        log.error(
            "ERROR: Cannot send emails without a password/email combo. Skipping send."
        )
        await interaction.response.edit_message(
            content=(
                "I sent the message on Discord, but I could not send emails. "
                "Contact your local administrator!"
            )
        )
        return

    # 3. Generate an email
    async with bot.db.execute(
        ("SELECT user_email FROM announcement_user_data WHERE " "guild_id = :guild_id"),
        (guild_id,),
    ) as cursor:
        recipients = await cursor.fetchall()

    if not recipients:
        await interaction.response.edit_message(
            content="I sent the message on Discord, but there is no-one to send emails to!"
        )
        return

    recipients = ", ".join(map(lambda x: x[0], recipients))

    content = (
        f"Announcement from `{interaction.user.display_name}` in server `{interaction.guild.name}`:\n\n"
        + announcement.announcement_body.value
        + "\n\n"
        + MILTON_EMAIL_FOOTER
    )

    mail = EmailMessage()
    mail.set_content(content)
    mail.add_alternative(markdown.markdown(content), subtype="html")
    mail["From"] = CONFIG.announcements.email
    mail["To"] = recipients
    mail["Subject"] = announcement.announcement_title.value

    # 4. Connect to the email server and send the email
    await aiosmtplib.send(
        message=mail,
        sender=CONFIG.announcements.email,
        hostname=CONFIG.announcements.hostname,
        username=CONFIG.announcements.email,
        password=CONFIG.announcements.password,
        port=CONFIG.announcements.port,
    )
    # 5. Update the interaction to say that everything went smoothly.
    await interaction.followup.send(content="Announcement complete!", ephemeral=True)


async def _set_announcement_channel(bot: Milton, interaction: Interaction):
    guild_id = interaction.guild_id
    channel_id = interaction.channel_id
    await bot.db.execute(
        ("DELETE FROM announcement_guild_config WHERE " "guild_id = :guild_id"),
        (guild_id,),
    )
    await bot.db.execute(
        (
            "INSERT INTO announcement_guild_config "
            "(guild_id, announcement_channel) "
            "VALUES (:guild_id, :channel_id)"
        ),
        (guild_id, channel_id),
    )
    await bot.db.commit()


async def _unset_announcement_channel(bot: Milton, interaction: Interaction):
    guild_id = interaction.guild_id
    await bot.db.execute(
        "DELETE FROM announcement_guild_config WHERE guild_id = :guild_id",
        (guild_id,),
    )
    await bot.db.commit()


@app_commands.guild_only
class AnnouncementsCog(GroupCog, name="announcement"):
    def __init__(self, bot: Milton) -> None:
        self.bot: Milton = bot

    @app_commands.command(name="subscribe")
    async def subscribe(self, interaction: Interaction, email: str):
        """Subscribe (or change your email) to the email announcements for this guild."""
        try:
            await _subscribe(
                bot=self.bot,
                member_id=interaction.user.id,
                guild_id=interaction.guild_id,
                email=email,
            )
        except InvalidEmailError:
            await interaction.response.send_message(
                "Sorry, the email you used does not seem to be valid."
            )
            return

        await interaction.response.send_message(
            "You have subscribed to the announcements. Congrats!"
        )

    @app_commands.command(name="unsubscribe")
    async def unsubscribe(self, interaction: Interaction):
        """Unsubscribe yourself from this guild's email announcements."""
        try:
            await _unsubscribe(
                bot=self.bot,
                member_id=interaction.user.id,
                guild_id=interaction.guild_id,
            )
        except NotSubscribedError:
            await interaction.response.send_message(
                "You are not subscribed. There's nothing to unsubscribe from!"
            )
            return

        await interaction.response.send_message(
            "You've successfully unsubscribed from email notifications."
        )

    @app_commands.command(name="sudosub")
    @app_commands.checks.has_permissions(administrator=True)
    async def sudo_subscribe(
        self, interaction: Interaction, member: Member, email: str
    ):
        """Force someone to subscribe to the announcements for this guild."""
        try:
            await _subscribe(
                bot=self.bot,
                member_id=member.id,
                guild_id=interaction.guild_id,
                email=email,
            )
        except InvalidEmailError:
            await interaction.response.send_message(
                "Sorry, the email you used does not seem to be valid."
            )
            return

        await interaction.response.send_message(
            f"You've forced {member.mention} to subscribe to the email announcements with email `{email}`."
        )

        dm_channel = member.dm_channel or await member.create_dm()

        try:
            await dm_channel.send(
                (
                    f"Hey! Just a notification that '{interaction.user.mention}' "
                    "has subscribed you to e-mail announcements for the server "
                    f"'{interaction.guild.name}' with email {email}.\n\n"
                    f"If this email is wrong, use `{self.qualified_name} subscribe` command, inside "
                    "the mentioned guild with your correct email. \n"
                    f"If you wish to unsubscribe, use the `{self.qualified_name} unsubscribe` "
                    "command inside the mentioned guild. Thank you!"
                )
            )
        except Forbidden:
            log.warn(
                "Tried to send a warning message to a user, but they cannot be messaged."
            )
            return

    @app_commands.command(name="sudounsub")
    @app_commands.checks.has_permissions(administrator=True)
    async def sudo_unsubscribe(self, interaction: Interaction, member: Member):
        """Force someone to unsubscribe to the announcements for this guild."""
        try:
            await _unsubscribe(
                bot=self.bot, member_id=member.id, guild_id=interaction.guild_id
            )
        except NotSubscribedError:
            await interaction.response.send_message(
                f"{member.mention} is not subscribed."
            )
            return

        await interaction.response.send_message(
            f"You've forced {member.mention} to unsubscribe to the email announcements."
        )

        dm_channel = member.dm_channel or await member.create_dm()

        try:
            await dm_channel.send(
                (
                    f"Hey! Just a notification that '{interaction.user.mention}' "
                    "has unsubscribed you to e-mail announcements for the server "
                    f"'{interaction.guild.name}'.\n\n"
                    f"If you wish to re-subscribe, use the `{self.qualified_name} subscribe` "
                    "command inside the mentioned guild. Thank you!"
                )
            )
        except Forbidden:
            log.warn("Tried to warn a user, but I cannot send a message to them.")
            return

    @app_commands.command(name="addrole")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_announce_role(self, interaction: Interaction, role: Role):
        """Add a role that can send announcements."""
        try:
            await _add_announce_role(
                self.bot, role_id=role.id, guild_id=interaction.guild_id
            )
        except RoleAlreadyAnnouncerError:
            await interaction.response.send_message(
                f"{role.mention} is already an announcer role!"
            )
            return

        await interaction.response.send_message(
            f"Added {role.mention} as an announcer role!"
        )

    @app_commands.command(name="removerole")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_announce_role(self, interaction: Interaction, role: Role):
        """Remove a role that can send announcements."""
        try:
            await _remove_announce_role(
                self.bot, role=role.id, guild_id=interaction.guild_id
            )
        except RoleNotAllowedError:
            await interaction.response.send_message(
                f"{role.mention} is not an announcer role."
            )
            return

        await interaction.response.send_message(
            f"Removed {role.mention} from announcer roles."
        )

    @app_commands.command(name="info")
    async def announcement_info(self, interaction: Interaction):
        """Print some information regarding announcements."""
        guild_id = interaction.guild_id
        user_id = interaction.user.id

        async with self.bot.db.execute(
            (
                "SELECT user_email FROM announcement_user_data "
                "WHERE guild_id = :guild_id AND user_id = :user_id"
            ),
            (guild_id, user_id),
        ) as cursor:
            email = await cursor.fetchone()

        if email is None:
            await interaction.response.send_message(
                "You are not receiving announcements for this guild."
            )
            return

        await interaction.response.send_message(
            f"You are registered for announcements with email `{email[0]}`."
        )

    @app_commands.command(name="send")
    async def send_announcement(self, interaction: Interaction):
        """Send an announcement (if you have permission!)"""
        # TODO: Fill Me
        guild_id = interaction.guild_id
        has_permission = False

        async with self.bot.db.execute(
            "SELECT role FROM announcement_roles WHERE guild_id = :guild_id",
            (guild_id,),
        ) as cursor:
            roles = await cursor.fetchall()
            if roles is None:
                await interaction.response.send_message(
                    "No roles may send announcements in this server."
                )
                return

        roles = list(map(lambda x: x[0], roles))
        user_roles = list(map(lambda x: x.id, interaction.user.roles))

        has_permission = bool([i for i in user_roles if i in roles])

        if not has_permission:
            await interaction.response.send_message(
                "You are not permitted to send announcements."
            )
            return

        async with self.bot.db.execute(
            "SELECT announcement_channel FROM announcement_guild_config WHERE guild_id = :guild_id",
            (guild_id,),
        ) as cursor:
            channel_id = await cursor.fetchone()

        if channel_id is None:
            await interaction.response.send_message(
                "This guild has not set an announcement channel."
            )
            return

        modal = AnnouncementModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="here")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_announcement_channel(self, interaction: Interaction):
        """Set this channel as the announcement channel."""
        ## TODO: What if we cannot write in this channel?
        # With admin permissions this is not a problem, but meh?
        await _set_announcement_channel(self.bot, interaction)
        await interaction.response.send_message("I will announce here from now on.")

    @app_commands.command(name="silence")
    @app_commands.checks.has_permissions(administrator=True)
    async def stop_announcements(self, interaction: Interaction):
        """Stop announcing for this guild."""
        await _unset_announcement_channel(self.bot, interaction)
        await interaction.response.send_message(
            "I will stop announcing for this guild."
        )


async def setup(bot):
    await bot.add_cog(AnnouncementsCog(bot))

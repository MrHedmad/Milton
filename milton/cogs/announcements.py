import logging

from discord import Interaction, Member, Role, app_commands, ui
from discord.ext.commands import GroupCog

from milton.core.bot import Milton
from milton.core.errors import MiltonError

log = logging.getLogger(__name__)


class NotSubscribedError(MiltonError):
    """The user is not subscribed to the announcements"""


class RoleDoesNotExistError(MiltonError):
    """The role does not exist anymore"""


class RoleNotAllowedError(MiltonError):
    """The role mentioned is not allowed to send announcements."""


class AnnouncementModal(ui.Modal, title="New Announcement"):
    announcement_title = ui.TextInput(label="Title", placeholder="Announcement Title")
    announcement_body = ui.TextInput(
        label="Message", placeholder="Type something...", max_length=2500
    )

    async def on_submit(self, interaction: Interaction, /) -> None:
        await interaction.response.send_message("Got it! Will announce soon!")
        await _send_announcement(interaction.client, announcement=self)

    async def on_error(self, interaction: Interaction, error: Exception, /) -> None:
        return await super().on_error(interaction, error)


async def _unsubscribe(bot: Milton, member_id: int, guild_id: int):
    """Call the DB to unsubscribe a certain member from announcements"""
    pass


async def _subscribe(bot: Milton, member_id: int, guild_id: int, email: str):
    """Call the DB to subscribe a certain member from announcements"""
    pass


async def _add_announce_role(bot: Milton, role_id: int, guild_id: int):
    pass


async def _remove_announce_role(bot: Milton, role: int, guild_id: int):
    pass


async def _send_announcement(bot: Milton, announcement: AnnouncementModal):
    """Send an announcement."""
    pass


async def _send_admin_status(bot: Milton, interaction: Interaction):
    pass


async def _send_user_status(bot: Milton, interaction: Interaction):
    pass


@app_commands.guild_only
class AnnouncementsCog(GroupCog, name="announcement"):
    def __init__(self, bot: Milton) -> None:
        self.bot: Milton = bot

    @app_commands.command(name="subscribe")
    async def subscribe(self, interaction: Interaction, email: str):
        """Subscribe (or change your email) to the email announcements for this guild."""
        await _subscribe(
            bot=self.bot,
            member_id=interaction.user.id,
            guild_id=interaction.guild_id,
            email=email,
        )

        await interaction.response.send_message(
            "You have subscribed to the announcements. Congrats!"
        )

    @app_commands.commands(name="unsubscribe")
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
        await _subscribe(
            bot=self.bot,
            member_id=member.id,
            guild_id=interaction.guild_id,
            email=email,
        )

        await interaction.response.send_message(
            f"You've forced {member.mention} to subscribe to the email announcements with email {email}."
        )

        dm_channel = member.dm_channel or await member.create_dm()

        await dm_channel.send(
            (
                f"Hey! Just a notification that '{interaction.user.mention}' "
                "has subscribed you to e-mail announcements for the server "
                f"'{interaction.guild.name}' with email {email}.\n\n"
                f"If this email is wrong, use `{self.name} subscribe` command, inside "
                "the mentioned guild with your correct email. \n"
                f"If you wish to unsubscribe, use the `{self.name} unsubscribe` "
                "command inside the mentioned guild. Thank you!"
            )
        )

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

        await dm_channel.send(
            (
                f"Hey! Just a notification that '{interaction.user.mention}' "
                "has unsubscribed you to e-mail announcements for the server "
                f"'{interaction.guild.name}'.\n\n"
                f"If you wish to re-subscribe, use the `{self.name} subscribe` "
                "command inside the mentioned guild. Thank you!"
            )
        )

    @app_commands.command(name="addrole")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_announce_role(self, interaction: Interaction, role: Role):
        """Add a role that can send announcements."""
        await _add_announce_role(
            self.bot, role_id=role.id, guild_id=interaction.guild_id
        )

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
        if interaction.user.resolved_permissions.administrator:
            await _send_admin_status(self.bot, interaction)
            return

        await _send_user_status(self.bot, interaction)

    @app_commands.command(name="send")
    async def send_announcement(self, interaction: Interaction):
        """Send an announcement (if you have permission!)"""
        # TODO: Fill Me
        has_permission = True

        if not has_permission:
            await interaction.response.send_message(
                "I'm sorry, you may not send announcements.", ephemeral=True
            )

        guild_supports_announcements = True

        if not guild_supports_announcements:
            await interaction.response.send_message(
                "Sorry! You can announce, but nobody told me where to announce...",
                ephemeral=True,
            )

        modal = AnnouncementModal()
        await interaction.response.send_modal(modal)

    @app_commands.command(name="here")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_announcement_channel(self, interaction: Interaction):
        """Set this channel as the announcement channel."""
        pass

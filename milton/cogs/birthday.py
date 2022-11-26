# Implements the birthday cog
# TODO: This is bad and I cannot be bothered to make it better!
import datetime as dt
import logging
from datetime import datetime
from typing import Optional

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from milton.core.bot import Milton
from milton.core.config import CONFIG
from milton.utils import tasks
from milton.utils.enums import Months
from milton.utils.paginator import Paginator
from milton.utils.tools import unwrap

log = logging.getLogger(__name__)


def birth_from_str(date: Optional[str]) -> Optional[dt.datetime]:
    """Returns a datetime object by parsing a date

    A wrapper to handle the optional presence of a year.

    Args:
        date: string that can be parsed in a date by strptime. If None, this
            function returns None.
    """
    if date:
        if len(date) == 5:
            # This is a date without a year
            birthday = dt.datetime.strptime(date, "%d-%m")
            birthday = birthday.replace(year=1)
        else:
            birthday = dt.datetime.strptime(date, "%d-%m-%Y")

        return birthday
    return None


def time_to_bday(date: Optional[str]) -> Optional[int]:
    """Returns the time from now to the next date in days.

    Args:
        Date: A parseable string to check.
    """
    now = datetime.now()
    if date := birth_from_str(date):
        date = date.replace(year=now.year)
        diff = date - now

        if diff.days < 0:
            return (now.replace(year=(now.year + 1)) - now).days + diff.days
        return diff.days


def calculate_age(date: Optional[str]) -> Optional[int]:
    """Returns the age of the person given their birthday

    Args:
        date: A parseable string to check.
    """
    born = birth_from_str(date)
    today = dt.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def is_today(this: dt.date, other: dt.date) -> bool:
    """Checks if the two dates point to the same day"""
    return all((this.day == other.day, this.month == other.month))


def clean_date(date: Optional[str]):
    """This shouldn't have been necessary..."""
    if not date:
        return date

    if len(date) in (5, 9):
        return date
    else:
        output = []
        for item in date.split("-"):
            if len(item) == 1:
                item = f"0{item}"
            output.append(item)
        return "-".join(output)


@app_commands.guild_only
class BirthdayCog(commands.GroupCog, name="birthday"):
    """Cog for implementing the birthday commands and notifications"""

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            try:
                interaction.response.send_message(
                    "I'm sorry, you don't have permission to do this."
                )
            except discord.InteractionResponded:
                interaction.followup.send(
                    "I'm sorry, but you don't have permission to do this."
                )
            return

        raise error

    def __init__(self, bot: Milton) -> None:
        self.bot: Milton = bot
        self.check_birthdays_task.start()

    def cog_unload(self):
        self.check_birthdays_task.stop()

    @tasks.loop(at=dt.time(hour=CONFIG.birthday.when), hours=24)
    async def check_birthdays_task(self):
        """Tasks the checking of the birthdays in a loop"""
        log.info("Checking today's birthdays...")

        async with self.bot.db.execute(
            "SELECT guild_id, bday_shout_channel FROM guild_config"
        ) as cursor:
            async for row in cursor:
                if row[1] is not None:
                    await self.check_birthdays(row[0])

    @check_birthdays_task.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()

    async def check_birthdays(self, guild_id: int):
        """Checks if it's someone's birthday and sends the respective messages

        Takes a guild_id of a guild THAT HAS SET THE SHOUT CHANNEL!!
        """
        async with self.bot.db.execute(
            f"SELECT bday_shout_channel FROM guild_config WHERE guild_id = :guild_id",
            (guild_id,),
        ) as cursor:
            shout_channel_id = await cursor.fetchone()

        shout_channel_id = unwrap(shout_channel_id)

        assert shout_channel_id is not None

        out = []
        today = dt.date.today()

        async with self.bot.db.execute(
            f"SELECT user_id, year, day, month FROM birthdays WHERE guild_id = :guild_id",
            (guild_id,),
        ) as cursor:
            async for row in cursor:
                user_id, year, day, month = row

                if year:
                    date = f"{day:02}-{month:02}-{year:04}"
                else:
                    date = f"{day:02}-{month:02}"

                birthday = birth_from_str(date).date()

                if not is_today(today, birthday):
                    continue

                if not year:
                    # This is a date without a year.
                    out.append(f"Happy birthday to you, <@!{user_id}>!!")
                else:
                    # This is a date with a year
                    age = today.year - birthday.year

                    if age == 0:
                        ending = "You seem to have been born today. Congratulations!"
                    elif age < 0:
                        ending = f"You must be a time traveler! You will be born in {-age} years!"
                    else:
                        ending = f"You just turned {age}!!"

                    out.append(f"Happy birthday to you, <@!{user_id}>!! " + ending)

        if len(out) != 0:
            shout_channel = self.bot.get_channel(int(shout_channel_id))
            if shout_channel:
                await shout_channel.send(content="\n".join(out))
            else:
                log.error(
                    (
                        f"I could not fetch the shout channel for guild {guild_id}"
                        " maybe the channel got deleted? Removing the shout channel"
                        " for this guild."
                    )
                )
                await self.bot.db.execute(
                    f"UPDATE guild_config SET bday_shout_channel = NULL WHERE guild_id = :guild_id",
                    (guild_id,),
                )
                await self.bot.db.commit()

    @app_commands.command(name="show")
    async def get_birthdays(self, interaction: Interaction):
        """Get birthdays registered in this guild."""
        do_paginate = False  # This is horrible but I want to get it over with
        out = Paginator(
            prefix="```",
            suffix="```",
            force_embed=True,
            title=f"Here are the birthdays for **{interaction.guild.name}**",
        )

        if not interaction.guild:
            interaction.response.send_message("You must run this in a server.")
            return

        guild_id = str(interaction.guild.id)
        guild = interaction.guild

        birthdays = []
        async with self.bot.db.execute(
            f"SELECT user_id, year, day, month FROM birthdays WHERE guild_id = :guild_id",
            (guild_id,),
        ) as cursor:
            async for row in cursor:
                if row[1] is None:
                    # This has no year
                    birthdays.append((row[0], f"{row[2]:02}-{row[3]:02}"))
                else:
                    birthdays.append((row[0], f"{row[2]:02}-{row[3]:02}-{row[1]:04}"))

        if not birthdays:
            await interaction.response.send_message(
                "Nobody registered a birthday in this server, sorry."
            )
            return

        birthdays = sorted(birthdays, key=lambda x: time_to_bday(x[1]))

        for entry in birthdays:
            user_id = int(entry[0])
            date = clean_date(entry[1])

            dateobj = birth_from_str(date)

            user = guild.get_member(user_id)
            if not (user is not None and date is not None):
                continue
            username = user.display_name
            if len(username) > 20:
                username = username[:20] + "..."
            do_paginate = True
            if dateobj.year == 1:
                out.add_line(f"{username:<25}{date} (-{time_to_bday(date)} days)")
            else:
                out.add_line(
                    f"{username:<25}{date} (Age {calculate_age(date)},"
                    f" -{time_to_bday(date)} days)"
                )

        if do_paginate:
            await out.paginate(interaction)
        else:
            await interaction.response.send_message(
                "Nobody registered a birthday in this server, sorry."
            )

    @app_commands.command(name="set")
    async def register(
        self,
        interaction: Interaction,
        month: Months,
        day: app_commands.Range[int, 1, 31],
        year: app_commands.Range[int, 1000, 9999] = None,
    ):
        """Registers a new birthday for yourself."""
        if not interaction.guild:
            interaction.response.send_message(
                "You must use this in a guild.", ephemeral=True
            )
            return

        month = month.value

        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        try:
            if year:
                birth_from_str(f"{day:02}-{month:02}-{year:04}")
            else:
                birth_from_str(f"{day:02}-{month:02}")

        except ValueError:
            log.debug("Inputted birthday is not parseable to a date.")
            await interaction.response.send_message(
                "Oh, silly! That isn't a real day!", ephemeral=True
            )
            return

        log.debug(f"Updating birthday of user {user_id} in guild {guild_id}")

        await self.bot.db.execute(
            ("DELETE FROM birthdays WHERE guild_id = :guild_id AND user_id = :user_id"),
            (guild_id, user_id),
        )
        await self.bot.db.commit()

        await self.bot.db.execute(
            (
                "INSERT INTO birthdays "
                "(guild_id, user_id, year, day, month) "
                "VALUES (:guild_id, :user_id, :year, :day, :month) "
            ),
            (guild_id, user_id, year, day, month),
        )
        await self.bot.db.commit()

        await interaction.response.send_message(
            "Huzzah! I will now remember your birthday."
        )

    @app_commands.command()
    async def remove(self, interaction):
        """Removes the birthday date from yourself."""
        if not interaction.guild:
            interaction.response.send_message(
                "You must use this in a guild.", ephemeral=True
            )

        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        log.debug(f"Removing birthday of user {user_id} in guild {guild_id}")

        await self.bot.db.execute(
            "DELETE FROM birthdays WHERE guild_id = :guild_id AND user_id = :user_id",
            (guild_id, user_id),
        )
        await self.bot.db.commit()

        await interaction.response.send_message(
            "Sure! I forgot your birthday for this server. Bye!"
        )

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def here(self, interaction: Interaction):
        """Set the channel where to scream the birthdays.

        Requires the Administrator permissions to use.
        Overwrites any previously set channel.
        """
        if not interaction.guild:
            interaction.response.send_message(
                "You must use this in a guild.", ephemeral=True
            )

        guild_id = str(interaction.guild.id)
        channel_id = str(interaction.channel.id)

        log.debug(
            f"Setting birthday shout channel for guild {guild_id} to {channel_id}"
        )

        await self.bot.db.execute(
            (
                "INSERT INTO guild_config "
                "(guild_id, bday_shout_channel) "
                "VALUES (:guild_id, :channel_id) "
                "ON CONFLICT (guild_id) DO UPDATE SET bday_shout_channel = :channel_id WHERE guild_id = :guild_id"
            ),
            (guild_id, channel_id),
        )
        await self.bot.db.commit()

        await interaction.response.send_message(
            (
                "I will shout out the birthdays in this channel from now on!"
                " You can use `birthday silence` to make me shut up."
                " (I will no longer shout in any previously set channels)"
            )
        )

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def silence(self, interaction: Interaction):
        """Make the bot stop shouting in chat.

        Essentially removes the channel set through 'bday here'.
        Works in any channel, not necessarily that being screamed at.
        """
        if not interaction.guild:
            interaction.response.send_message(
                "You must use this in a guild.", ephemeral=True
            )

        guild_id = str(interaction.guild.id)

        log.debug(f"Removing birthday shout channel for guild {guild_id}")

        await self.bot.db.execute(
            (
                "UPDATE OR IGNORE birthdays SET bday_shout_channel = NULL "
                "WHERE guild_id = :guild_id"
            ),
            (guild_id,),
        )
        await self.bot.db.commit()

        await interaction.response.send_message(
            ("I will be silent about birthdays from now on.")
        )

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def check(self, interaction: Interaction):
        """Force the bot to check now for today's birthdays.

        Does not affect the normal check loop.
        """
        if not interaction.guild:
            interaction.response.send_message(
                "You must use this in a guild.", ephemeral=True
            )

        guild_id = str(interaction.guild.id)

        async with self.bot.db.execute(
            f"SELECT bday_shout_channel FROM guild_config WHERE guild_id = :guild_id",
            (guild_id,),
        ) as cursor:
            shout_channel = await cursor.fetchone()

        shout_channel = unwrap(shout_channel)

        if shout_channel is not None:
            await interaction.response.send_message(
                "Checking birthdays, please wait.", ephemeral=True
            )
            await self.check_birthdays(guild_id)
        else:
            await interaction.response.send_message(
                "Sorry, you did not set a shout channel.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(BirthdayCog(bot))

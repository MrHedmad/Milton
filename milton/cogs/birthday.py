# Implements the birthday cog
import asyncio
import datetime as dt
import logging

from discord.ext import commands
from discord.ext import tasks

from milton.config import CONFIG
from milton.utils.database import DB
from milton.utils.errors import UserInputError
from milton.utils.paginator import Paginator

log = logging.getLogger(__name__)


def birth_from_str(date: str) -> dt.datetime:
    """Returns a datetime object by parsing a date

    A wrapper to handle the optional presence of a year
    """
    if len(date) == 5:
        # This is a date without a year
        birthday = dt.datetime.strptime(date, "%d-%m")
    else:
        birthday = dt.datetime.strptime(date, "%d-%m-%Y")

    return birthday


def is_today(this: dt.date, other: dt.date) -> bool:
    """Checks if the two dates point to the same day"""
    return all((this.day == other.day, this.month == other.month))


class BirthdayCog(commands.Cog):
    """Cog for implementing the birthday commands and notifications"""

    def __init__(self, bot) -> None:
        self.bot = bot
        # Keep track if the initial temporal realignment has been done
        self.inital_shift = False

        self.check_birthdays_task.start()

    def cog_unload(self):
        self.check_birthdays_task.stop()

    @tasks.loop(hours=24)
    async def check_birthdays_task(self):
        """Tasks the checking of the birthdays in a loop"""
        # Syncronize with the correct time
        if not self.inital_shift:
            log.info("Realigning birthday checks...")
            now = dt.datetime.now()
            # When was the check today?
            check_today = dt.datetime.now().replace(
                hour=CONFIG.birthday.when, second=0, microsecond=0
            )

            if now > check_today:
                log.debug("The check today was already passed. Waiting tomorrow")
                # We already passed today's check. Check tomorrow.
                # Need to wait (24*60*60) seconds (86400) - the delta
                to_wait = 86400 - (now - check_today).seconds

            else:
                log.debug("The check today still hasn't happened. Waiting to it")
                to_wait = (now - check_today).seconds

            hours = to_wait // (60 * 60)
            seconds = to_wait % (60)
            log.debug(f"Waiting {to_wait} seconds, aka {hours}:{seconds}")
            await asyncio.sleep(to_wait)

            self.inital_shift = True

        for guild_id in DB.find(["birthday", "guilds"]):

            shout_channel = DB.find(["birthday", "shout_channels", guild_id])
            if isinstance(shout_channel, int):
                await self.check_birthdays(guild_id)

    @check_birthdays_task.before_loop
    async def before_cli(self):
        await self.bot.wait_until_ready()

    async def check_birthdays(self, guild_id: int):
        """Checks if it's someone's birthday and sends the respective messages

        Takes a guild_id of a guild THAT HAS SET THE SHOUT CHANNEL!!
        """
        guild_id = str(guild_id)
        shout_channel_id = DB.find(["birthday", "shout_channels", guild_id])
        assert not isinstance(shout_channel_id, dict)

        out = Paginator()
        today = dt.date.today()

        for user_id, date in DB.find(["birthday", "guilds", guild_id, "dates"]).items():
            if not date:
                continue

            birthday = birth_from_str(date).date()

            if not is_today(today, birthday):
                continue

            if birthday.year == 1900:
                # This is (probably) a date without a year.
                out.add_line(f"Happy birthday to you, <@!{user_id}>!!")
            else:
                # This is a date with a year
                age = today.year - birthday.year

                if age == 0:
                    ending = "You seem to have been born today. Congratulations!"
                elif age < 0:
                    ending = f"You must be a time traveler! You will be born in {-age} years!"
                else:
                    ending = f"You just turned {age}!!"

                out.add_line(f"Happy birthday to you, <@!{user_id}>!! " + ending)

        if len(out.pages) != 0:
            shout_channel = self.bot.get_channel(int(shout_channel_id))
            if shout_channel:
                await out.paginate(shout_channel)
            else:
                log.error(
                    (
                        f"I could not fetch the shout channel for guild {guild_id}"
                        " maybe the channel got deleted? Removing the shout channel"
                        " for this guild."
                    )
                )

                DB.update(["birthday", "shout_channels", guild_id], None)

    @commands.guild_only()
    @commands.group(
        name="bday",
        aliases=("bdays", "birthday", "birthdays"),
        invoke_without_command=True,
    )
    async def birthday_group(self, ctx):
        """Group of the birthday commands.

        With no additional commands, sends the list of upcoming birthdays of
        people who have registered a birthday in this specific server.
        """
        do_paginate = False  # This is horrible but I want to get it over with
        out = Paginator(prefix="```", suffix="```")
        out.add_line("Here are the birthdays for this server:")

        guild_id = str(ctx.guild.id)
        guild = self.bot.get_guild(int(guild_id))
        birthdays = DB.find(["birthday", "guilds", guild_id, "dates"])
        # Remember that birthdays is a dict of user_id: date

        for user_id, date in birthdays.items():
            user_id = int(user_id)
            user = guild.get_member(user_id)
            if not (user is not None and date is not None):
                continue
            username = user.display_name
            do_paginate = True
            out.add_line(f"{username:<20} {date}")

        if do_paginate:
            await out.paginate(ctx)
        else:
            await ctx.send("Nobody registered a birthday in this server, sorry.")

    @birthday_group.command(aliases=("add", "set"))
    async def register(self, ctx, date: str):
        """Registers a new birthday for yourself.

        The date is a string like DD-MM-YYYY OR DD-MM.
        Birthdays are NOT encrypted in any way.
        If the day or month are single-digits, it must be padded with a
        leading 0. TODO: Needs to be checked

        Example usage:

            $bday register 25-04-1993
            $bday register 01-01
        """
        try:
            birth_from_str(date)
        except ValueError:
            raise UserInputError(
                (
                    "I cannot parse the date, sorry. Supported formats are DD-MM "
                    "and DD-MM-YYYY. Remember that single digits **must** be padded!"
                )
            )

        # If we get to here, the datetime is parseable.
        # I'm saving it as STR just because so I dont have to add a new type
        # in the parser for the dictionary

        guild_id = str(ctx.message.guild.id)
        user_id = str(ctx.message.author.id)

        log.debug(f"Updating birthday of user {user_id} in guild {guild_id}")

        DB.update(["birthday", "guilds", guild_id, "dates", user_id], date)

        await ctx.send("Huzzah! I will now remember your birthday.")

    @birthday_group.command()
    async def remove(self, ctx):
        """Removes the birthday date for yourself."""
        guild_id = str(ctx.message.guild.id)
        user_id = str(ctx.message.author.id)

        log.debug(f"Removing birthday of user {user_id} in guild {guild_id}")

        DB.update(["birthday", "guilds", guild_id, "dates", user_id], None)

        await ctx.send("Sure! I forgot your birthday for this server. Bye!")

    @commands.has_permissions(administrator=True)
    @birthday_group.command()
    async def here(self, ctx):
        """Set the channel where to scream the birthdays.

        Requires the Administrator permissions to use.
        Overwrites any previously set channel.
        """
        guild_id = str(ctx.message.guild.id)
        channel_id = str(ctx.channel.id)

        log.debug(
            f"Setting birthday shout channel for guild {guild_id} to {channel_id}"
        )

        DB.update(["birthday", "shout_channels", guild_id], channel_id)

        await ctx.send(
            (
                "I will shoutout the birthdays in this channel from now on!"
                " You can use `birthday silence` to make me shut up."
                " (I will no longer shout in any previously set channels)"
            )
        )

    @commands.has_permissions(administrator=True)
    @birthday_group.command()
    async def silence(self, ctx):
        """Make the bot stop shouting in chat.

        Essentially removes the channel set through 'bday here'.
        Works in any channel, not necessarily that being screamed at.
        """
        guild_id = str(ctx.message.guild.id)
        channel_id = str(ctx.channel.id)

        log.debug(f"Removing birthday shout channel for guild {guild_id}")

        DB.update(["birthday", "shout_channels", guild_id], None)

        await ctx.send(("I will be silent about birthdays from now on."))

    @commands.has_permissions(administrator=True)
    @birthday_group.command()
    async def check(self, ctx):
        """Force the bot to check now for today's birthdays.

        Does not affect the normal check loop.
        """
        await ctx.send("Checking for birthdays...")
        guild_id = str(ctx.guild.id)
        shout_channel = DB.find(["birthday", "shout_channels", guild_id])
        if not isinstance(shout_channel, dict) and shout_channel is not None:
            await self.check_birthdays(guild_id)
        else:
            await ctx.send("Sorry, you did not set a shout channel.")


def setup(bot):
    bot.add_cog(BirthdayCog(bot))
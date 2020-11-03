import datetime as dt
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands
from discord.ext import tasks

from milton.bot import Milton
from milton.config import CONFIG
from milton.utils import checks
from milton.utils import tasks
from milton.utils.paginator import Paginator
from milton.utils.tools import get_random_line


log = logging.getLogger(__name__)


class Toys(commands.Cog, name="Toys"):
    """Cog for implementing toy functions"""

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, dice):
        """Roll some dice, like 1d20, or 100d1000!"""

        out = Paginator()

        try:
            number, sides = [abs(int(x)) for x in dice.split("d")]
        except (IndexError, ValueError):
            out.add_line("Cannot parse message. Please restate. Try: $roll 1d20")
            return await out.paginate(ctx)

        if number > 100:
            out.add_line("I'm sorry, I cannot roll that many dice.")
            return await out.paginate(ctx)

        if sides > 50000:
            out.add_line("I'm sorry, I cannot roll dice that big.")
            return await out.paginate(ctx)

        message = "Rolling {}: ".format((str(number) + "d" + str(sides)))

        results = []
        sign = ""
        for _ in range(0, number):
            result = random.randint(1, sides)
            results.append(result)
            if result == sides:
                result = "**" + str(result) + "**"
            else:
                result = str(result)
            message += sign + result
            sign = " + "

        summation = sum(results)
        message += f" = **{summation}**"
        out.add_line(message)
        return await out.paginate(ctx)

    @commands.command()
    async def fact(self, ctx):
        """Send a totally accurate fact"""
        embed = discord.Embed(
            description=get_random_line("./milton/resources/facts.txt")
        )
        await ctx.send(embed=embed)


class BanBazza(commands.Cog):
    """Ban Bazza l'8 Novembre"""

    def __init__(self, bot) -> None:
        self.bot = bot
        self.ban_bazza.start()

    def cog_unload(self):
        self.ban_bazza.stop()

    @tasks.loop(at=dt.time(hour=10), hours=24)
    async def ban_bazza(self):
        """Ban Bazza the 8th of November. He asked for it!"""
        today = dt.date.today()
        home = self.bot.get_channel(311200788858798080)
        bazza_id = 485910756324540437
        target = dt.date(2020, 11, 8)
        if target == today:
            # Banning Bazza
            bazza_user = self.bot.get_user(bazza_id)
            if bazza_user:
                await self.bot.ban(bazza_user, reason="Tanti Auguri Bazza!!!")
                await home.send("Bazza é stato bannato! Yay!")
            self.stop()
            return

        delta = today - target
        await home.send(f"BAN BAZZA L'8 NOVEMBRE\nCountdown: {delta.days}")

    @ban_bazza.before_loop
    async def bazza_before(self):
        await self.bot.wait_until_ready()
        bazza_id = 485910756324540437
        home = self.bot.get_channel(311200788858798080)
        await home.send(
            embed=discord.Embed(
                title="Ban Bazza Reminder",
                description=f"Pronto a ricordare a @<{bazza_id}> che deve essere Bannato l'8 Novembre. Prova `bzban`",
            )
        )

    @commands.command(name="bzban", aliases=("banbazza", "bazzaban"))
    @commands.check_any(checks.in_guild(311200788858798080), checks.in_test_guild())
    async def bazza_check(self, ctx):
        """Remind Bazza when He will be banned"""
        target = dt.date(2020, 11, 8)
        today = dt.date.today()
        delta = today - target
        await ctx.send(f"BAN BAZZA L'8 NOVEMBRE\nCountdown: {delta.days}")


def setup(bot):
    bot.add_cog(Toys(bot))
    bot.add_cog(BanBazza(bot))

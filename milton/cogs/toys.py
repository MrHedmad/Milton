import datetime as dt
import logging
import random
from pathlib import Path

import discord
from discord.ext import commands
from discord.ext.commands.context import Context

from milton.core.bot import Milton
from milton.core.config import CONFIG
from milton.core.errors import MiltonInputError
from milton.utils.paginator import Paginator
from milton.utils.tools import get_random_line


log = logging.getLogger(__name__)


class Toys(commands.Cog, name="Toys"):
    """Cog that hosts toy commands."""

    def __init__(self, bot: Milton) -> None:
        self.bot: Milton = bot

    @commands.command()
    async def roll(self, ctx: Context, dice: str):
        """Roll some dice, like 1d20, or 100d1000!

        Accepts any combination of `<nr. dice>d<faces>`, up to 100 dice with
        50000 faces.
        """
        out = Paginator()

        try:
            number, sides = [abs(int(x)) for x in dice.split("d")]
        except (IndexError, ValueError):
            raise MiltonInputError(
                "Cannot parse message. Please restate. Try: $roll 1d20"
            )

        if number > 100:
            raise MiltonInputError("I'm sorry, I cannot roll that many dice.")

        if sides > 50000:
            raise MiltonInputError("I'm sorry, I cannot roll dice that big.")

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
    async def fact(self, ctx: Context):
        """Send a totally accurate fact.

        Fact is guaranteed(tm) to be 99.8% accurate.
        """
        embed = discord.Embed(
            description=get_random_line("./milton/resources/facts.txt")
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Toys(bot))

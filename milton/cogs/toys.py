import logging
import random
from pathlib import Path

import discord
from discord.ext import commands
from discord.ext import tasks

from milton.bot import Milton
from milton.config import CONFIG
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


def setup(bot):
    bot.add_cog(Toys(bot))

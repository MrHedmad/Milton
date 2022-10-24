import importlib.resources as pkg_resources
import logging
import random

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from milton.core.bot import Milton
from milton.utils.paginator import Paginator
from milton.utils.tools import get_random_line

log = logging.getLogger(__name__)


class Toys(commands.Cog, name="Toys"):
    """Cog that hosts toy commands."""

    def __init__(self, bot: Milton) -> None:
        self.bot: Milton = bot

    @app_commands.command()
    async def roll(
        self,
        interaction: Interaction,
        number: app_commands.Range[int, 1, 100],
        sides: app_commands.Range[int, 1, 50000],
    ):
        """Roll some dice, like 1d20, or 100d1000!

        Accepts any combination of `<nr. dice>d<faces>`, up to 100 dice with
        50000 faces.
        """
        out = Paginator()

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
        return await out.paginate(interaction)

    @app_commands.command()
    async def fact(self, interaction: Interaction):
        """Send a totally accurate fact.

        Fact is guaranteed(tm) to be 99.8% accurate.
        """
        with pkg_resources.path("milton.resources", "facts.txt") as path:
            embed = discord.Embed(description=get_random_line(path))
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Toys(bot))

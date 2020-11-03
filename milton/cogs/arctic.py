"""Commands related to the Arctic Guild Discord Server"""
import asyncio
from difflib import get_close_matches
from pathlib import Path
from string import capwords
from typing import List

import discord
import ujson
from discord.ext import commands

from milton.utils.checks import in_channel
from milton.utils.checks import in_test_guild
from milton.utils.errors import UserInputError
from milton.utils.tools import glob_word


class ArcticCog(commands.Cog):
    """A cog hosting all the commands related to the Arctic Guild!"""

    def __init__(self, bot):
        self.bot: commands.Bot = bot

    async def cog_check(self, ctx):
        """Cog-wide check to see if the guild is the correct one."""
        allowed_guilds = [
            # The Arctic
            100652581096804352,
            # Milton Test Guild
            574203165495525387,
        ]
        try:
            return ctx.message.guild.id in allowed_guilds
        except:
            return False

    # HIDE AND SEEK
    @commands.command()
    @commands.check_any(in_channel(616404320253902898), in_test_guild())
    async def seek(self, ctx, *, query=None):
        """Get the link for a hide&seek map. Try $seek list"""

        with Path("./milton/resources/hideseek.json").open("r") as stream:
            locations = ujson.load(stream)

        if query is None:
            raise UserInputError("You did not specify a query!")

        # guess the match
        flat = {}
        for city, quarter in locations.items():
            for name, data in quarter.items():
                flat[city + " " + name] = data

        if query.startswith("list"):
            # The user is requesting a list.
            formatted = ""
            for city, quarter in locations.items():
                formatted += "**" + capwords(city) + "**:\n\t"
                for name in quarter:
                    formatted += capwords(name) + ", "
                formatted = formatted[:-2] + "\n"
            return await ctx.send(
                ("Here's a list of places you can search:\n" + formatted)
            )

        match = glob_word(query, flat, cutoff=0.8)

        try:
            hit = flat[match]
        except KeyError:
            close_match = capwords(get_close_matches(query, flat, 1, 0)[0])
            sent = await ctx.send(
                f'I\'m sorry, but I cannot find "{match}". Did you mean "{close_match}"?'
            )
            # Cleanup a failed command
            await asyncio.sleep(5)
            await sent.delete()
            await ctx.message.delete()
            return

        embed = discord.Embed(
            title=("Hide and Seek Location - " + capwords(match)), url=hit["link"]
        )
        embed.set_image(url=hit["image"])

        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(ArcticCog(bot))

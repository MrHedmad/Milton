import aiohttp
from discord.ext import commands

from milton.bot import Milton
from milton.utils.paginator import Paginator
from milton.utils.tools import fetch


class DebugCog(commands.Cog, name="Debug"):
    def __init__(self, bot) -> None:
        self.bot = bot

    def cog_check(self, ctx):
        # This cog is restricted for the author of the bot.
        # It contains error-prone functions that shouldn't be exposed
        # to the end user
        return self.bot.is_owner(ctx.author)

    @commands.command()
    async def test(self, ctx):
        """Sends a test message in order to try pagination."""

        out = Paginator(title="Powered by www.baconipsum.com")
        endpt = "https://baconipsum.com/api/"

        # This should probably be asyncronous
        response = await fetch(
            self.bot.http_session,
            endpt,
            params={
                "type": "meat-and-filler",
                "paras": 15,
                "start-with-lorem": 1,
                "format": "text",
            },
        )

        for line in response.split("\n"):
            out.add_line(line)

        await out.paginate(ctx)


def setup(bot: Milton):
    bot.add_cog(DebugCog(bot))

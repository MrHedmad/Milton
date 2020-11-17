from discord.ext import commands
from discord.ext.commands.context import Context

from milton.bot import Milton
from milton.utils.paginator import Paginator
from milton.utils.tools import fetch


class DebugCog(commands.Cog, name="Debug"):
    """"""

    def __init__(self, bot) -> None:
        self.bot = bot

    def cog_check(self, ctx: Context):
        # Assure that these commands may only be executed from the owner of the
        # bot.
        return self.bot.is_owner(ctx.author)

    @commands.command()
    async def test(self, ctx: Context):
        """Sends a test message in order to try pagination.

        The contents are retrieved from a remote sever, baconipsum.com, which
        generates meaty fillers.
        """
        out = Paginator(title="Powered by www.baconipsum.com")
        endpt = "https://baconipsum.com/api/"

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

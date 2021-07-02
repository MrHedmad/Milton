import pprint

from discord.abc import User
from discord.ext import commands
from discord.ext.commands.context import Context

from milton.core.bot import Milton
from milton.core.database import MiltonUser
from milton.core.errors import MiltonInputError
from milton.utils.paginator import Paginator
from milton.utils.tools import fetch
from milton.utils.tools import id_from_mention


class DebugCog(commands.Cog, name="Debug"):
    """"""

    def __init__(self, bot) -> None:
        self.bot: Milton = bot

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
        endpoint = "https://baconipsum.com/api/"

        response = await fetch(
            self.bot.http_session,
            endpoint,
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

    @commands.group(aliases=("ins", "i"), invoke_without_command=True)
    async def inspect(self, ctx):
        """Group of the inspect commands."""
        pass

    @inspect.command()
    async def user(self, ctx: Context, name: str):
        """Shows someone's statistics"""

        try:
            id_, type_ = id_from_mention(name)
        except ValueError:
            raise MiltonInputError("Not a valid mention or ID")

        member: User = self.bot.get_user(id_)
        if not member:
            raise MiltonInputError("Cannot Find User")

        out = Paginator(force_embed=True, title=f"Data for user {member.name}")
        async with MiltonUser(id_) as user:
            formatted = pprint.pformat(user.data, indent=4)
        formatted = formatted.split("\n")
        for line in formatted:
            out.add_line(line)
        await out.paginate(ctx)


def setup(bot: Milton):
    bot.add_cog(DebugCog(bot))

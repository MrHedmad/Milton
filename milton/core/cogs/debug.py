import pprint

from discord.ext import commands
import discord
from discord import app_commands
from discord import Interaction
from discord.ext.commands.context import Context

from milton.core.bot import Milton
from milton.core.database import MiltonUser
from milton.core.errors import MiltonInputError
from milton.utils.paginator import Paginator
from milton.utils.tools import fetch


class DebugCog(commands.GroupCog, name="debug"):
    """"""

    def __init__(self, bot) -> None:
        self.bot: Milton = bot

    def cog_check(self, ctx: Context):
        # Assure that these commands may only be executed from the owner of the
        # bot.
        return self.bot.is_owner(ctx.author)

    @app_commands.command()
    async def test(self, interaction: Interaction):
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

        await out.paginate(interaction)

    @app_commands.command()
    async def inspect(self, interaction: Interaction, member: discord.Member):
        """Shows the data related to someone"""

        if not member:
            raise MiltonInputError("Cannot Find User")

        out = Paginator(force_embed=True, title=f"Data for user {member.name}")
        async with MiltonUser(member.id) as user:
            formatted = pprint.pformat(user.data, indent=4)
        formatted = formatted.split("\n")
        for line in formatted:
            out.add_line(line)
        await out.paginate(interaction)


async def setup(bot: Milton):
    await bot.add_cog(DebugCog(bot))

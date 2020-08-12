import datetime
import platform
import sys
import time
from importlib.metadata import version

from discord.ext import commands

import milton
from milton.bot import Milton
from milton.utils.paginator import Paginator


class TestingCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def test(self, ctx):
        """Sends a test message"""

        out = Paginator()

        for _ in range(20):
            out.add_line(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Cras maximus tristique quam non euismod. In ut nisi semper, ullamcorper dui consequat, scelerisque dui. Nullam eu quam vel tortor tincidunt tempor. Aliquam malesuada eros elit, ac faucibus nisl faucibus ac. Cras dictum dolor maximus augue suscipit auctor. Nunc elementum lacus ullamcorper nisi fermentum iaculis eu eget nisl. Proin mattis, orci sed sollicitudin faucibus, ipsum purus ultrices ligula, nec fermentum justo augue eu mi. Donec at urna vel ex convallis hendrerit. Pellentesque porttitor neque lacus, id tincidunt nisl convallis quis. Sed consequat neque ac gravida euismod. Praesent in enim et justo efficitur lacinia id ac urna."
            )

        for _ in range(5):
            out.add_line(
                "Etiam ut tristique nisl. Donec bibendum justo et ipsum vulputate maximus. In vitae dui tristique, dignissim mi et, porta magna. Nunc vitae augue lobortis, dapibus lacus eleifend, tincidunt mauris. Vivamus a nibh metus. Nunc et ultricies elit, ac vulputate metus. Nunc dui purus, sollicitudin a convallis ac, euismod sed elit. Morbi ultrices mauris id egestas porttitor. Nunc ipsum tortor, mattis sed enim quis, vehicula euismod ante. Nullam vestibulum porta congue. Nullam in elit ut nulla luctus feugiat ut sed nunc. Vestibulum a felis vel sem consectetur dignissim. Fusce at mi libero. Proin ut purus placerat, imperdiet elit sed, dapibus ex. Phasellus nisl ipsum, ultricies et malesuada a, ornare vel turpis. Duis sodales felis at enim dictum lobortis. "
            )

        await out.paginate(ctx)

    @commands.command()
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def status(self, ctx):
        """Returns the status of the bot"""
        out = Paginator()

        # Versions
        me = milton.__version__
        dpy = version("discord.py")
        python = sys.version.replace("\n", "")
        os = f"{platform.system()} {platform.release()}"

        # Statistics
        tot_users = len(self.bot.users)
        tot_guilds = len(self.bot.guilds)

        # Time
        since = datetime.timedelta(seconds=time.time() - self.bot.started_on)

        out.add_line(
            (
                "**Status**\n"
                f"Milton Library Assistant version `{me}` - Python `{python}` - Dpy `{dpy}`\n"
                f"Running on `{os}`.\n"
                f"I am in {tot_guilds} guilds, and I can see {tot_users} users.\n"
                f"I was online for {since}."
            )
        )
        await out.paginate(ctx)

    @commands.command()
    @commands.is_owner()
    async def trigger_error(self, ctx):
        raise ValueError("This was triggered by a command.")


def setup(bot: Milton):
    bot.add_cog(TestingCog(bot))

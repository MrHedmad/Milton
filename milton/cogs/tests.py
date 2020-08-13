import datetime
import platform
import sys
import time
from importlib.metadata import version

import discord
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
        """Sends a test message in order to try pagination."""

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
        embed = discord.Embed()

        # Versions
        me = milton.__version__
        dpy = version("discord.py")
        python = sys.version.replace("\n", "").split()[0]
        os = f"{platform.system()} {platform.release()}"

        # Statistics
        tot_users = len(self.bot.users)
        tot_guilds = len(self.bot.guilds)

        # Time
        since = datetime.timedelta(seconds=time.time() - self.bot.started_on)
        form_since = f"{since.days} days and {since.seconds // 60}:{since.seconds % 60}"

        embed.title = "**Milton Library Assistant - Status**"
        embed.add_field(name="Version", value=f"{me}")
        embed.add_field(name="Python Version", value=python, inline=True)
        embed.add_field(name="OS Information", value=f"{os}")
        embed.add_field(name="Discord.py", value=dpy)
        embed.add_field(name="Online since", value=form_since)
        embed.add_field(
            name="Watching",
            value=f"{tot_guilds} guilds - {tot_users} users",
            inline=True,
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def trigger_error(self, ctx):
        """Manually trigger a ValueError inside the bot. To test error handling"""
        raise ValueError("This was triggered by a command.")

    @commands.command()
    async def source(self, ctx):
        """Returns the link to the bot's source code."""
        embed = discord.Embed()
        embed.set_thumbnail(url=str(self.bot.user.avatar_url))
        embed.set_author(name="Milton Library Assistant")
        embed.title = "Find me on GitHub!"
        embed.url = r"https://github.com/MrHedmad/Milton"
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Pong!"""
        embed = discord.Embed()
        embed.title = "**Pong!**"
        embed.add_field(name="Discord Websocket Latency", value=str(self.bot.latency))

        await ctx.send(embed=embed)


def setup(bot: Milton):
    bot.add_cog(TestingCog(bot))

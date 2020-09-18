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


class MetaCog(commands.Cog, name="Meta"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def status(self, ctx):
        """Returns the status of the bot.

        Information like uptime, python version and linux version.
        """
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

        embed.title = "**Milton Library Assistant - Status**"
        embed.add_field(name="Version", value=f"{me}")
        embed.add_field(name="Python Version", value=python, inline=True)
        embed.add_field(name="OS Information", value=f"{os}")
        embed.add_field(name="Discord.py", value=dpy)
        embed.add_field(name="Online since", value=str(since).split(".")[0])
        embed.add_field(
            name="Watching",
            value=f"{tot_guilds} guilds - {tot_users} users",
            inline=True,
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx):
        """Returns the link to the bot's source code.

        Proudly hosted by GitHub.
        """
        embed = discord.Embed()
        embed.set_thumbnail(url=str(self.bot.user.avatar_url))
        embed.set_author(name="Milton Library Assistant")
        embed.title = "Find me on GitHub!"
        embed.url = r"https://github.com/MrHedmad/Milton"
        await ctx.send(embed=embed)

    @commands.command()
    async def ping(self, ctx):
        """Pong!

        Returns the discord websocket latency, kinda like the ping of the bot.
        """
        embed = discord.Embed()
        embed.title = "**Pong!**"
        embed.add_field(name="Discord Websocket Latency", value=str(self.bot.latency))

        await ctx.send(embed=embed)


def setup(bot: Milton):
    bot.add_cog(MetaCog(bot))

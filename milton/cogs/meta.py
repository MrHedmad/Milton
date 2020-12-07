import datetime
import platform
import sys
import time
from importlib.metadata import version

import discord
from discord.errors import Forbidden
from discord.ext import commands
from discord.ext.commands.context import Context

from milton.core.bot import Milton
from milton.core.errors import MiltonInputError
from milton.utils.tools import get_random_line


class MetaCog(commands.Cog, name="Meta"):
    """Cog hosting commands related to the bot itself."""

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command()
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def status(self, ctx: Context):
        """Returns the status of the bot.

        Information like uptime, python version and linux version.
        """
        embed = discord.Embed()

        # Versions
        me = self.bot.version
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
        embed.add_field(name="Python Version", value=python)
        embed.add_field(name="OS Information", value=f"{os}")
        embed.add_field(name="Discord.py", value=dpy)
        embed.add_field(name="Online since", value=str(since).split(".")[0])
        embed.add_field(
            name="Watching", value=f"{tot_guilds} guilds - {tot_users} users"
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx: Context):
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
    async def ping(self, ctx: Context):
        """Pong!

        Returns the discord websocket latency, kinda like the ping of the bot.
        The real latency of the bot depends on the time it takes to process the
        command.
        """
        embed = discord.Embed()
        embed.title = "**Pong!**"
        embed.add_field(name="Discord Websocket Latency", value=str(self.bot.latency))
        await ctx.send(embed=embed)

    @commands.group(
        name="changes",
        aliases=("changelog", "log", "notes"),
        invoke_without_command=True,
    )
    async def changes_group(self, ctx):
        """Display the full changelog for the bot"""
        out = self.bot.changelog.to_paginator()
        await out.paginate(ctx)

    @changes_group.command()
    async def link(self, ctx: Context):
        """Returns the link to the bot's full changelog.

        For those who prefer a less interactive changelog.
        Proudly hosted by GitHub.
        """
        embed = discord.Embed()
        embed.set_thumbnail(url=str(self.bot.user.avatar_url))
        embed.set_author(name="Milton Library Assistant")
        embed.title = "Read my full changelog on GitHub!"
        embed.url = r"https://github.com/MrHedmad/Milton/blob/master/CHANGELOG.md"
        await ctx.send(embed=embed)

    @commands.command(name="inside", invoke_without_command=True)
    @commands.guild_only()
    async def subscribe(self, ctx: Context):
        """Subscribe to announcements and other things."""
        if (role := ctx.guild.get_role(777612764222717992)) :
            if role not in ctx.author.roles:
                try:
                    await ctx.author.add_roles(role)
                except Forbidden:
                    raise MiltonInputError("I do not have powers here... :(")
                embed = discord.Embed(title="You are now inside!")
                embed.set_image(url=get_random_line("./milton/resources/insiders.txt"))
                await ctx.send(embed=embed)
            else:
                try:
                    await ctx.author.remove_roles(role)
                except Forbidden:
                    raise MiltonInputError("I do not have powers here... :(")
                embed = discord.Embed(title="You are no longer inside.")
                embed.set_image(
                    url=get_random_line("./milton/resources/noinsiders.txt")
                )
                await ctx.send(embed=embed)


def setup(bot: Milton):
    bot.add_cog(MetaCog(bot))

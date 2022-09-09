import datetime
import platform
import sys
import time
from importlib.metadata import version
import importlib.resources as pkg_resources

import discord
from discord.errors import Forbidden
from discord import app_commands
from discord import Interaction
from discord.ext import commands
from discord.ext.commands.context import Context

from milton.core.bot import Milton
from milton.core.errors import MiltonInputError
from milton.utils.checks import in_home_guild
from milton.utils.tools import get_random_line


class MetaCog(commands.Cog, name="Meta"):
    """Cog hosting commands related to the bot itself."""

    def __init__(self, bot) -> None:
        self.bot = bot

    @app_commands.command()
    @app_commands.checks.cooldown(1, 10)
    async def status(self, interaction: Interaction):
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

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command()
    async def source(self, interaction: Interaction):
        """Returns the link to the bot's source code.

        Proudly hosted by GitHub.
        """
        embed = discord.Embed()
        embed.set_thumbnail(url=str(self.bot.user.display_avatar.url))
        embed.set_author(name="Milton Library Assistant")
        embed.title = "Find me on GitHub!"
        embed.url = r"https://github.com/MrHedmad/Milton"
        await interaction.response.send(embed=embed)

    @app_commands.command()
    async def ping(self, interaction: Interaction):
        """Pong!

        Returns the discord websocket latency, kinda like the ping of the bot.
        The real latency of the bot depends on the time it takes to process the
        command.
        """
        embed = discord.Embed()
        embed.title = "**Pong!**"
        embed.add_field(name="Discord Websocket Latency", value=str(self.bot.latency))
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(
        name="changes",
        aliases=("changelog", "log", "notes"),
        invoke_without_command=True,
    )
    async def changes(self, interaction: Interaction):
        """Display the full changelog for the bot"""
        out = self.bot.changelog.to_paginator()
        out.url = r"https://github.com/MrHedmad/Milton/blob/master/CHANGELOG.md"
        out.title = "Milton Library Assistant Changelog"
        await out.paginate(interaction)

    @commands.command(name="inside", invoke_without_command=True)
    @commands.guild_only()
    @in_home_guild()
    async def subscribe(self, ctx: Context):
        """Subscribe to announcements and other things."""
        if (role := ctx.guild.get_role(777612764222717992)) :
            if role not in ctx.author.roles:
                try:
                    await ctx.author.add_roles(role)
                except Forbidden:
                    raise MiltonInputError("I do not have powers here... :(")
                embed = discord.Embed(title="You are now inside!")
                with pkg_resources.path("milton.resources", "insiders.txt") as path:
                    embed.set_image(url=get_random_line(path))
                await ctx.send(embed=embed)
            else:
                try:
                    await ctx.author.remove_roles(role)
                except Forbidden:
                    raise MiltonInputError("I do not have powers here... :(")
                embed = discord.Embed(title="You are no longer inside.")
                with pkg_resources.path("milton.resources", "noinsiders.txt") as path:
                    embed.set_image(url=get_random_line(path))
                await ctx.send(embed=embed)


async def setup(bot: Milton):
    await bot.add_cog(MetaCog(bot))

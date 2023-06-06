import datetime
import importlib.resources as pkg_resources
import platform
import sys
import time
from importlib.metadata import version

import discord
from discord import Interaction, app_commands
from discord.errors import Forbidden
from discord.ext import commands

from milton.core.bot import Milton
from milton.core.errors import MiltonInputError
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

        embed.title = "**Milton Lab Assistant - Status**"
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
        embed.set_author(name="Milton Lab Assistant")
        embed.title = "Find me on GitHub!"
        embed.url = r"https://github.com/MrHedmad/Milton"
        await interaction.response.send_message(embed=embed)

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

    @app_commands.command(name="inside")
    @app_commands.guilds(discord.Object(id=311200788858798080))
    async def subscribe(self, interaction: Interaction):
        """Subscribe to announcements and other things."""
        if role := interaction.guild.get_role(777612764222717992):
            if role not in interaction.message.author.roles:
                try:
                    await interaction.message.author.add_roles(role)
                except Forbidden:
                    raise MiltonInputError("I do not have powers here... :(")
                embed = discord.Embed(title="You are now inside!")
                with pkg_resources.path("milton.resources", "insiders.txt") as path:
                    embed.set_image(url=get_random_line(path))
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                try:
                    await interaction.message.author.remove_roles(role)
                except Forbidden:
                    raise MiltonInputError("I do not have powers here... :(")
                embed = discord.Embed(title="You are no longer inside.")
                with pkg_resources.path("milton.resources", "noinsiders.txt") as path:
                    embed.set_image(url=get_random_line(path))
                await interaction.response.send_message(embed=embed)


async def setup(bot: Milton):
    await bot.add_cog(MetaCog(bot))

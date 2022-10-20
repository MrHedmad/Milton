"""RSS feeds parser"""
import html
import logging
import re

import discord
import feedparser
from discord.ext import commands
from discord import app_commands
from discord import Interaction

from milton.core.bot import Milton
from milton.utils import tasks

log = logging.getLogger(__name__)


async def get_last_xkcd(session):
    """Get the last comic from xkcd and make an embed."""
    url = "https://xkcd.com/rss.xml"
    async with session.get(url) as response:
        content = await response.text()
        parsed = feedparser.parse(content)

    title = re.search('title="(.*?)"', parsed.entries[0].description)
    img_url = re.search('src="(.*?)"', parsed.entries[0].description)

    embed = discord.Embed()

    embed.title = parsed.entries[0].title
    embed.description = html.unescape(title.group(1))
    embed.set_image(url=img_url.group(1).strip())
    embed.set_footer(text=parsed.entries[0].link)

    return embed


class RSSCog(commands.GroupCog, name = "xkcd"):
    def __init__(self, bot) -> None:
        self.bot: Milton = bot

        self.check_xkcd_task.start()

    @app_commands.command()
    async def latest(self, interaction: Interaction):
        """Send the latest XKCD issue."""
        embed = await get_last_xkcd(self.bot.http_session)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def here(self, interaction: Interaction):
        """Send updates when new XKCD issues come out in this channel."""
        guild_id = interaction.guild_id
        channel_id = interaction.channel_id

        log.info(f"Updating xkcd shout channel for guild {guild_id} to {channel_id}")
        await self.bot.db.execute((
            "INSERT INTO xkcd (guild_id, shout_channel) VALUES (:guild_id, :channel_id) "
            "ON CONFLICT (guild_id) DO UPDATE SET shout_channel = :channel_id "
            "WHERE guild_id = :guild_id"
        ), (guild_id, channel_id))
        await self.bot.db.commit()

        await interaction.response.send_message("I will send the xkcd issues here from now on!")

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def silence(self, interaction: Interaction):
        """Stop sending XKCD updates in this guild."""
        guild_id = interaction.guild_id

        log.info(f"Removing xkcd shout channel for guild {guild_id}")
        await self.bot.db.execute((
            "DELETE FROM xkcd WHERE guild_id = :guild_id"
        ), (guild_id,))
        await self.bot.db.commit()

        await interaction.response.send_message("I won't send the xkcd issues anymore.")

    @tasks.loop(hours=8)
    async def check_xkcd_task(self):
        """Task that checks for new comics"""
        log.info("Checking for new xkcd issues...")
        embed = await get_last_xkcd(self.bot.http_session)

        async with self.bot.db.execute("SELECT last_sent_xkcd, shout_channel FROM xkcd") as cursor:
            async for row in cursor:
                last_title, shout_channel = row

                if embed.title == last_title:
                    log.info("No need to send an update")
                    return

                channel = self.bot.get_channel(shout_channel)

                if not channel:
                    log.warning(f"Couldn't find the channel to send the xkcd message to ({shout_channel}).")
                    return

                await channel.send(embed=embed)

        last_title = embed.title
        # Update all rows with the new xkcd.
        # I mean, it might not have been sent, but who cares...
        await self.bot.db.execute("UPDATE xkcd SET last_sent_xkcd = :last_title", (last_title,))
        await self.bot.db.commit()

    @check_xkcd_task.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: Milton):
    await bot.add_cog(RSSCog(bot))

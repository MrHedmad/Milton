"""RSS feeds parser"""
import html
import logging
import re

import discord
import feedparser
from discord.ext import commands
from discord.ext.commands.context import Context

from milton.core.bot import Milton
from milton.core.database import MiltonGeneric
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


class RSSCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: Milton = bot

        self.check_xkcd_task.start()

    @commands.command()
    async def xkcd(self, ctx: Context):
        embed = await get_last_xkcd(self.bot.http_session)
        await ctx.send(embed=embed)

    @tasks.loop(hours=8)
    async def check_xkcd_task(self):
        """Task that checks for new comics"""
        log.info("Checking for new xkcd issues...")
        embed = await get_last_xkcd(self.bot.http_session)

        async with MiltonGeneric as doc:
            last_title = doc["last_xkcd_title"]

        if embed.title == last_title:
            log.info("No need to send an update")
            return

        channel = self.bot.get_channel(861597995879628850)

        if not channel:
            log.warning("Couldnt find a channel to send the xkcd message to")
            return

        await channel.send(embed=embed)

        async with MiltonGeneric as doc:
            doc["last_xkcd_title"] = embed.title

    @check_xkcd_task.before_loop
    async def before_task(self):
        await self.bot.wait_until_ready()


def setup(bot: Milton):
    bot.add_cog(RSSCog(bot))

"""RSS feeds parser"""
import html
import re

import discord
import feedparser
from discord.ext import commands
from discord.ext.commands.context import Context

from milton.core.bot import Milton


class RSSCog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot: Milton = bot

    @commands.command()
    async def xkcd(self, ctx: Context):
        url = "https://xkcd.com/rss.xml"
        async with self.bot.http_session.get(url) as response:
            content = await response.text()
            parsed = feedparser.parse(content)

        title = re.search('title="(.*?)"', parsed.entries[0].description)
        img_url = re.search('src="(.*?)"', parsed.entries[0].description)

        embed = discord.Embed()

        embed.title = parsed.entries[0].title
        embed.description = html.unescape(title.group(1))
        embed.set_image(url=img_url.group(1).strip())
        embed.set_footer(text=parsed.entries[0].link)

        await ctx.send(embed=embed)


def setup(bot: Milton):
    bot.add_cog(RSSCog(bot))

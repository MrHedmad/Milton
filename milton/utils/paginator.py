import asyncio
import logging
from contextlib import suppress
from typing import Optional

import discord
from discord import Message
from discord.abc import Messageable
from discord.embeds import EmptyEmbed
from discord.ext import commands

from milton.core.config import CONFIG

log = logging.getLogger(__name__)

DELETE_EMOJI = CONFIG.emojis.trash
NEXT_EMOJI = CONFIG.emojis.next
BACK_EMOJI = CONFIG.emojis.back
LAST_EMOJI = CONFIG.emojis.last
FIRST_EMOJI = CONFIG.emojis.first
STOP_EMOJI = CONFIG.emojis.stop

DEFAULT_EMOJIS = (
    DELETE_EMOJI,
    FIRST_EMOJI,
    BACK_EMOJI,
    NEXT_EMOJI,
    LAST_EMOJI,
    STOP_EMOJI,
)


class Paginator(commands.Paginator):
    """Helper that builds and sends messages to channels.

    Allows interactive pagination with emojis. This class is heavily copied
    from the Python Discord bot.

    Args:
        prefix: A prefix to give to each page of the resulting embed.
        suffix: A suffix to give to each page of the resulting embed.
        max_size: The maximum size of a page. Defaults to discord's maximum
            message size, 2000 characters.
        force_embed: By default, one-page embeds are sent as a normal message.
            Should it be sent as an embed instead?
        title: An optional title for the embed.
    """

    def __init__(
        self,
        prefix: str = "",
        suffix: str = "",
        max_size: int = 2000,
        force_embed: bool = False,
        title: Optional[str] = None,
    ) -> None:
        # As this is used a lot, I expose the parent class arguments explicitly
        super().__init__(prefix, suffix, max_size)
        self.force_embed = force_embed
        self.title = title

    async def paginate(self, ctx: Messageable):
        """Send and start to paginate this message

        If message is just one page, does not provide interactive pagination,
        as it's useless.

        Args:
            ctx: The messageable channel to send the message to.
        """
        # Yanked and modified from the python discord bot paginator
        def event_check(reaction_: discord.Reaction, user_: discord.Member) -> bool:
            """Make sure that this reaction is what we want to operate on."""

            return (
                # Conditions for a successful pagination:
                all(
                    (
                        # Reaction is on this message
                        reaction_.message.id == message.id,
                        # Reaction is one of the pagination emotes
                        str(reaction_.emoji) in DEFAULT_EMOJIS,
                        # Reaction was not made by the Bot
                        user_.id != ctx.bot.user.id,
                    )
                )
            )

        pages = self.pages
        max_pages = len(pages)

        embed = discord.Embed(description=pages[0], title=self.title or EmptyEmbed)
        current_page = 0

        if max_pages <= 1 and self.force_embed is False:
            # Only a single page to send. Just send it and stop
            return await ctx.send(embed.description)
        elif self.force_embed:
            # Forced to send an embed anyway.
            return await ctx.send(embed=embed)

        # Add a handy descriptive footer
        embed.set_footer(text=f"Page {current_page + 1} / {max_pages}")

        message: Message = await ctx.send(embed=embed)

        for emoji in DEFAULT_EMOJIS:
            await message.add_reaction(emoji=emoji)

        while True:
            try:
                reaction, user = await ctx.bot.wait_for(
                    "reaction_add",
                    timeout=ctx.bot.config.bot.pagination_timeout,
                    check=event_check,
                )
            except asyncio.TimeoutError:
                log.debug("Timed out waiting for a reaction")
                break

            if str(reaction.emoji) == DELETE_EMOJI:
                log.debug("Got delete reaction")
                return await message.delete()

            if reaction.emoji == FIRST_EMOJI:
                await message.remove_reaction(reaction.emoji, user)
                current_page = 0

                log.debug(f"Got first page reaction - changing to page 1/{max_pages}")

                embed.description = pages[current_page]
                embed.set_footer(text=f"Page {current_page + 1}/{max_pages}")
                await message.edit(embed=embed)

            if reaction.emoji == LAST_EMOJI:
                await message.remove_reaction(reaction.emoji, user)
                current_page = max_pages - 1

                log.debug(
                    f"Got last page reaction - changing to page {current_page + 1}/{max_pages}"
                )

                embed.description = pages[current_page]
                embed.set_footer(text=f"Page {current_page + 1}/{max_pages}")
                await message.edit(embed=embed)

            if reaction.emoji == BACK_EMOJI:
                await message.remove_reaction(reaction.emoji, user)

                if current_page <= 0:
                    log.debug(
                        "Got previous page reaction, but we're on the first page - ignoring"
                    )
                    continue

                current_page -= 1
                log.debug(
                    f"Got previous page reaction - changing to page {current_page + 1}/{max_pages}"
                )

                embed.description = pages[current_page]
                embed.set_footer(text=f"Page {current_page + 1}/{max_pages}")
                await message.edit(embed=embed)

            if reaction.emoji == NEXT_EMOJI:
                await message.remove_reaction(reaction.emoji, user)

                if current_page >= max_pages - 1:
                    log.debug(
                        "Got next page reaction, but we're on the last page - ignoring"
                    )
                    continue

                current_page += 1
                log.debug(
                    f"Got next page reaction - changing to page {current_page + 1}/{max_pages}"
                )

                embed.description = pages[current_page]
                embed.set_footer(text=f"Page {current_page + 1}/{max_pages}")

                await message.edit(embed=embed)

            if reaction.emoji == STOP_EMOJI:
                break

        log.debug("Ending pagination and clearing reactions.")
        with suppress(discord.NotFound):
            await message.clear_reactions()

import asyncio
import io
import logging
import re

import discord
from discord import Message
from discord.ext import commands
from matplotlib.mathtext import math_to_image

from milton.core.bot import Milton

log = logging.getLogger(__name__)

FIND_MATH_REGEX = re.compile(r"(\$.+?\$)")
MATH_RENDER_EMOJI = "👁️"


class MathRenderCog(commands.Cog, name="Math renderer"):
    def __init__(self, bot: Milton) -> None:
        self.bot = bot

    @commands.Cog.listener(name="on_message")
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        match = FIND_MATH_REGEX.search(message.content)
        if not match:
            return

        log.debug(f"Got a formula match for message {message.content}")

        formulae = match.groups()
        # Check if at least one formula is valid
        # Very long formulae are probably invalid.
        formulae = [x for x in formulae if len(x) < 400]
        if not formulae:
            return

        log.debug(f"Found {len(formulae)} formulae to render.")
        # If we get here, the message probably has a valid formula.
        # Make an image out of it.
        renders = []
        for formula in formulae:
            try:
                buffer = io.BytesIO()
                buffer.name = "render.png"
                math_to_image(formula, buffer, dpi=250, format="png")
                buffer.seek(0)
                renders.append(buffer)
            except Exception as e:
                log.exception("Got an error while rendering:", e)
                continue

        # If we failed to render anything, stop here
        if not renders:
            log.error("Couldn't render any math.")
            return

        # Add a listener to wait for the reaction
        def event_check(reaction_: discord.Reaction, user_: discord.Member) -> bool:
            """Make sure that this reaction is what we want to operate on."""

            return (
                # Conditions for a successful pagination:
                all(
                    (
                        # Reaction is on this message
                        reaction_.message.id == message.id,
                        # Reaction is one of the pagination emotes
                        str(reaction_.emoji) == MATH_RENDER_EMOJI,
                        # Reaction was not made by the Bot
                        user_.id != message.author.bot,
                    )
                )
            )

        await message.add_reaction(MATH_RENDER_EMOJI)
        log.debug(f"Starting to listen for math reaction for message {message.id}")

        try:
            await self.bot.wait_for("reaction_add", timeout=300, check=event_check)
        except asyncio.TimeoutError:
            log.debug(f"Timed out waiting for reaction on message {message.id}")
            return

        for render in renders:
            await message.reply(file=discord.File(render))


async def setup(bot: Milton):
    cog = MathRenderCog(bot)

    await bot.add_cog(cog)

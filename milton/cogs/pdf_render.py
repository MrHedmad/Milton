import logging
from asyncio import get_running_loop
from functools import partial
from io import BytesIO

import discord
from discord.ext import commands
from discord.ext.commands import Cog
from pdf2image import convert_from_bytes
from PyPDF2 import PdfReader

from milton.core.bot import Milton

log = logging.getLogger(__name__)


class PDFRenderCog(commands.Cog, name="PDF renderer"):
    def __init__(self, bot: Milton) -> None:
        self.bot: Milton = bot

    @Cog.listener(name="on_message")
    async def on_message(self, message: discord.Message):
        loop = get_running_loop()

        if message.attachments is None:
            return

        ref = message.to_reference()

        for attachment in message.attachments:
            if not attachment.filename.lower().endswith(".pdf"):
                continue

            # Someone sent a pdf. Render and send a preview of it
            try:

                async with self.bot.http_session.request(
                    "GET", attachment.url
                ) as stream:
                    bytes = await stream.read()
                    file_metadata = PdfReader(BytesIO(bytes))

                convert_ptl = partial(
                    convert_from_bytes, pdf_file=bytes, single_file=True, fmt="png"
                )
                render = await loop.run_in_executor(None, func=convert_ptl)

            except Exception as e:
                log.exception(e)
                continue

            render = render[0]  # We get a list of 1 item here

            width, height = render.size
            render = render.crop(box=(0, 0, width, height / 2))

            with BytesIO() as byte_container:
                render.save(byte_container, "PNG")
                byte_container.seek(0)
                file = discord.File(fp=byte_container, filename="image.png")
            embed = discord.Embed()
            embed.set_image(url="attachment://image.png").set_footer(
                text="Automatic PDF preview rendering"
            )

            info = file_metadata.getDocumentInfo()
            file_len = file_metadata.getNumPages()

            if info.title:
                embed.add_field(
                    name="Title", value=info.title.encode("ascii").decode("UTF-8")
                )

            if info.author:
                embed.add_field(name="Author(s)", value=info.author)

            embed.add_field(name="Pages", value=file_len)

            await message.channel.send(file=file, embed=embed, reference=ref)


async def setup(bot):
    await bot.add_cog(PDFRenderCog(bot))

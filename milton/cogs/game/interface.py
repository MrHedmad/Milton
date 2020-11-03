from discord.ext import commands

from milton.bot import Milton


class GameCog(commands.Cog):
    """Cog hosting the game interface"""

    def __init__(self, bot: Milton) -> None:
        self.bot: Milton = bot

from milton import bot
from milton.cogs.game.interface import GameCog


def setup(bot: bot.Milton):
    cog = GameCog(bot)

    bot.add_cog(cog)

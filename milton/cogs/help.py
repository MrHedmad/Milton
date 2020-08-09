"""Implements the help command"""
from discord.ext import commands


class MiltonHelp(commands.MinimalHelpCommand):
    def get_command_signature(self, command):
        return "{0.clean_prefix}{1.qualified_name} {1.signature}".format(self, command)


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self._original_help_command = bot.help_command
        bot.help_command = MiltonHelp()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot: commands.Bot):
    bot.add_cog(HelpCog())

import logging
import random

from discord.ext import commands

from milton.bot import Milton
from milton.utils.paginator import Paginator


log = logging.getLogger(__name__)


class Toys(commands.Cog):
    """Cog for implementing toy functions"""

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command()
    async def roll(self, ctx, dice):
        log.debug("roll was triggered")

        out = Paginator()

        try:
            number, sides = [abs(int(x)) for x in dice.split("d")]
        except (IndexError, ValueError):
            out.add_line("Cannot parse message. Please restate. Try: $roll 1d20")
            return await out.paginate(ctx)

        if number > 100:
            out.add_line("I'm sorry, I cannot roll that many dice.")
            return await out.paginate(ctx)

        if sides > 50000:
            out.add_line("I'm sorry, I cannot roll dice that big.")
            return await out.paginate(ctx)

        message = "Rolling {}: ".format((str(number) + "d" + str(sides)))

        results = []
        sign = ""
        for _ in range(0, number):
            result = random.randint(1, sides)
            results.append(result)
            if result == sides:
                result = "**" + str(result) + "**"
            else:
                result = str(result)
            message += sign + result
            sign = " + "

        summation = sum(results)
        message += f" = **{summation}**"
        out.add_line(message)
        return await out.paginate(ctx)


def setup(bot):
    bot.add_cog(Toys(bot))

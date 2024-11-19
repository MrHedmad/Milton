# Contributing to Milton

You can contribute to the bot by adding an extension that does something cool.
Extensions should be put in the `cogs` folder and loaded in the `bot.py` script.
More information on how to correctly write extensions can be found in the [`discord.py` documentation](https://discordpy.readthedocs.io/en/latest/).

I welcome and will review all pull requests. 

## Setting up for development
To setup for developing Milton, you will need `python 3.11` installed. [Follow the standard GitHub contributing workflow](https://docs.github.com/en/get-started/quickstart/contributing-to-projects).

Remember to install pre-commit (I suggest installing it to the system-wide installation) with `pip install pre-commit` and setting it up with `pre-commit install` before committing. Pre-commit will handle setting code style and whatnot.

# Creating a new cog
When creating a new cog, it's useful to read the [cogs](https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html#ext-commands-cogs) documentation.
A cog is an encapsulated logic module that has full access to all the bot's capabilities.

The simplest Milton cog which you can take as example is the [toys cog](https://github.com/MrHedmad/Milton/blob/main/milton/cogs/toys.py).

## Using the database
Remember that you can access Milton's database with the connections in the `Milton` class (see [here](https://github.com/MrHedmad/Milton/blob/068a0d04db23efdee0a35418231f72be7587a9c2/milton/core/bot.py#L37), for example).

An example database call:
```python
# Reading data from a table
# The SQL call needs to be protected from SQL injection, this is why the 
# `execute` call takes care of string substitutions, and you should NEVER use
# f-strings when interacting with the DB.
async with self.bot.db.execute(
    f"SELECT column FROM table WHERE column = :id",
    (id,),
) as cursor:
    async for row in cursor:
        # You get a list with the columns in order
        print(f"The value of 'column' is {row[0]}")

# Insert data in a table
await self.bot.db.execute(
    "INSERT INTO table (col1, col2) VALUES (:one, :two) ",
    (one, two),
)
await self.bot.db.commit() # commit the scheduled transaction to the DB

# Same for deleting data to the table, use `execute` followed by `commit`
```

See the docs for `aiosqlite` here: https://aiosqlite.omnilib.dev/en/stable/index.html

## Getting data from the internet
You can fetch data (with `GET` requests) using the pool of connections in the
bot's instance by doing something like this:
```python
async with session.get(url) as response:
    content = await response.text()
    # The content is the raw HTML.
```
See the documentation for `aiohttp` here: https://docs.aiohttp.org/en/stable/


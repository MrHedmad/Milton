# The Milton Lab Assistant
[![License](https://img.shields.io/github/license/MrHedmad/Milton?style=flat-square)](https://choosealicense.com/licenses/mit/)
[![Required Python Version](https://img.shields.io/badge/Python-3.10-blue?style=flat-square)](https://python.org)
[![Code Style](https://img.shields.io/badge/style-Black-black?style=flat-square)](https://github.com/psf/black)
[![Issues](https://img.shields.io/github/issues/mrhedmad/milton?style=flat-square)](https://github.com/MrHedmad/Milton/issues)

Home of Milton Lab Assistant - the Discord Bot.
> There is only me, and you, and an eternity of doubt.
>
> — <cite>Milton</cite>

## About
This is a Discord bot mainly aimed at managing a research laboratory Discord Server.
It has specific features designed with research and a laboratory in mind.

The bot uses a local [SQLite](https://https://www.sqlite.org/index.html/) database to store its data.

## Deploy your own instance
To install and run milton, follow these instructions:
1. Install `python 3.10` or later and `git`.
   I assume that `python` points to the Python 3.11 interpreter;
2. Optionally, but highly advised, make a virtual environment and enter it with
   `python -m venv env` followed by `source env/bin/activate`.
3. Install the bot with `pip install git+https://github.com/MrHedmad/Milton.git@release`.
   - Optionally, you can remove the `@release` to install the latest dev branch.
4. Configure the bot, such as adding your bot token (see below).
5. Run the bot by executing `milton` (while in the `env`, if you made one).

To re-run the bot after you install it, run `milton` again while in the virtual environment.

### Configuration
Milton looks in `$HOME/.config/milton/milton.toml` to find its configuration.
The configuration is a [`TOML`](https://toml.io/en/) file with this possible
fields:
```toml
[bot]
token = # The bot's token
pagination_timeout = 300 # Time it takes to time out pagination, in seconds
test_server_id = 12345678900000 # The ID of the test server, if any.
# A list of the names of the extensions to load at startup.
startup_extensions = [
    "meta", "toys", "birthday", "math_render", "rss", "pdf_render"
]

[database]
path = "~/.milton/database.sqlite" # Where to store and look for the database file

[logs]
path = "~/.milton/logs/mla.log" # Where to store and look for the logs
# Logging levels (0: all, 10: DEBUG, 20: INFO, 30: WARNING, 40: ERROR, 50: CRITICAL)
file_level = 10 # logging level of messages saved to file.
stdout_level = 30 # logging level of messages sent to stdout.

[prefixes]
guild = "!!" # Prefix to use when invoking the bot in a guild (server).

[emojis]
# You usually do not change these. They are the emojis used when paginating.
trash = "\u274c"
next = "\u25b6"
back = "\u25c0"
last = "\u23e9"
first = "\u23ea"
stop = "\u23f9"

[birthday] # Config of the birthday cog
when = 10 # Time (in hours) to announce new birthdays. Uses local timezone.
```

Following the TOML convention, just remove a field if you'd like to use its
default value.

One config you **must** override is the `bot > token` field,
providing your own [discord bot token](https://discord.com/developers/applications).
Milton will not start without a token.

### Invite your bot
In the Discord Developers panel you can get a link

### Interactive use
When you launch milton, a CLI will appear.
Here, you may launch admin commands to manage your milton instance.
You can get a list of all commands using `help`.

Note: Misspelled commands are (lightly) grobbed to what Milton thinks you want.
This was mainly implemented since I constanly misspell `shutdown`.

# Contributing to Milton

You can contribute to the bot by adding an extension that does something cool.
Extensions should be put in the `cogs` folder and loaded in the `bot.py` script.
More information on how to correctly write extensions can be found in the
[`discord.py` documentation](https://discordpy.readthedocs.io/en/latest/).

I welcome and will review all pull requests. 

## Setting up for development
To setup for developing Milton, you will need `python 3.11` installed.
[Follow the standard GitHub contributing workflow](https://docs.github.com/en/get-started/quickstart/contributing-to-projects).

I strongly suggest working in a virtual environment.
Install the dev dependencies with `pip install -r requirements-dev.txt`,
then setup `pre-commit` with `pre-commit install`.

We follow the [`black`](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html) code style
and the [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)
commit message style.
The conventional commits standard that I follow is [here](https://github.com/MrHedmad/MrHedmad/blob/1bd723e6a4b59689aba8e19136178428ce7932ca/defaults/.gitlint).


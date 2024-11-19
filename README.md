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
You first need to install Milton. You can do it either with Docker or locally.

### With Docker
If you have Docker, you can either run `./run_docker` to have docker fetch the latest remote image for you,
or you could manually rebuild the docker container by cloning the repo and executing:
```bash
cd Milton
docker build -t mrhedmad/milton:latest .
./run_docker
```
The `run_docker` script as of today only support default paths for the database and the config file for milton,
mounting these defaults inside the container.
If you changed them, look into the `run_docker` script and edit the `run` command accordingly.

### Locally
To install and run milton locally, follow these instructions:
1. Install `python 3.13` or later and `git`.
   I assume that `python` points to the Python 3.13 interpreter;
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
In the Discord Developers panel you can get a link to invite your bot to your guild.
You can generate a link in the `Installation` tab.
Once you do, simply use it and invite the bot.

You will need to assign permissions to Milton before you invite it.
I usually give it most permissions.

Note that some commands require the priviledged intent "Message Content", which
you have to enable in the "Bot" tab of the Discord Developer Portal.

### Interactive use
When you launch milton, a CLI will appear.
Here, you may launch admin commands to manage your milton instance.
You can get a list of all commands using `help`.

Note: Misspelled commands are (lightly) globbed to what Milton thinks you want.
This was mainly implemented since I constanly misspell `shutdown`.

# Contributing to Milton

Please take a look at the [CONTRIBUTING.md](CONTRIBUTING.md) file for more information.

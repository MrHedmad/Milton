# The Milton Lab Assistant
[![License](https://img.shields.io/github/license/MrHedmad/Milton-Library-Assistant?style=flat-square)](https://choosealicense.com/licenses/mit/)
[![Required Python Version](https://img.shields.io/badge/Python-3.10-blue?style=flat-square)](https://python.org)
[![Code Style](https://img.shields.io/badge/style-Black-black?style=flat-square)](https://github.com/psf/black)
[![Issues](https://img.shields.io/github/issues/mrhedmad/milton?style=flat-square)](https://github.com/MrHedmad/Milton/issues)

Home of Milton Lab Assistant - the Discord Bot.
> There is only me, and you, and an eternity of doubt.
> 
> — <cite>Milton</cite> 

## About

This is a Discord bot mainly aimed at managing a research laboratory Discord Server. It has specific features designed with research and a laboratory in mind.

The bot uses a local [SQLite](https://https://www.sqlite.org/index.html/) database to store its data.

## Deploy your own instance

There are two ways to run your own instance of Milton:
1. Install `python 3.10` or later and `git`. I assume that `python` points to the Python 3.11 interpreter;
2. Optionally, but highly advised, make a virtual environment and enter it `python -m venv env`, then activate it `source env/bin/activate`.
3. Install the bot with `pip install git+https://github.com/MrHedmad/Milton.git@release`.
4. Configure the bot, such as adding your bot token (see below).
5. Run the bot by executing `milton` (while in the `env`).

To re-run the bot after you install it, run `milton` again while in the virtual environment. 

### Configuration

Create a `config.yml` (and not `.yaml`!) in `~/.milton/` and add your specific configuration for the bot, overriding any configs in the `default-config.yml` file. Note that the structure of the file must be identical to the first (I suggest copy-pasting it and changing what you need/like: from the Milton folder, `mkdir ~/.milton/ && cp ./milton/default-config.yml ~/.milton/config.yml`).

One config you must override is the `bot > token` field, providing your own [discord bot token](https://discord.com/developers/applications).

## Contribute with an extension

To contribute, please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) guide.
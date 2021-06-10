# The Milton Library Assistant
[![License](https://img.shields.io/github/license/MrHedmad/Milton-Library-Assistant?style=flat-square)](https://choosealicense.com/licenses/mit/)
[![Required Python Version](https://img.shields.io/github/pipenv/locked/python-version/MrHedmad/Milton-Library-Assistant?style=flat-square)](https://python.org)
[![Code Style](https://img.shields.io/badge/style-Black-black?style=flat-square)](https://github.com/psf/black)
[![Issues](https://img.shields.io/github/issues/mrhedmad/milton?style=flat-square)](https://github.com/MrHedmad/Milton/issues)

**THIS REPO IS NOW ARCHIVED AND READ-ONLY** - There are some security vulnerabilities with packages used by this repo at the time of archiving. Be sure to update them. This will be probabily remade (and renamed) once `discord.py` version 2 comes out. 

Home of Milton Library Assistant - the Discord Bot.

This is the (hopefully) final iteration of the discord bot for my personal guild. If you find it useful in any way, feel free to run new instances of it. Please also take a look at the source code and suggest fixes for it, as I am not a professional programmer.

The bot uses [MongoDB](https://www.mongodb.com/) to store data.

This bot is only tested on my machine, which runs Linux. Hence, I am not sure of its behaviour on Windows.

## Installation

1. Install `python` (3.8+), `git`, `mongoDB` and `pipenv` (this is os-specific, so google how-to).
2. Clone the repo to your local machine: `git clone https://github.com/MrHedmad/Milton.git`
3. Enter the folder where you cloned this into: `cd Milton`
4. Install the python dependencies: `pipenv install`
5. Configure the bot, such as adding your bot token (see below).
6. Run the bot by entering a virtual environment (`pipenv shell`) and running `python -m milton` **OR** by running `pipenv run python -m milton`.

If you're contributing, also setup `pre-commit` to automatically run `black` and other checks for you when you commit using `pre-commit install`.

### Configuration

Create a `config.yml` (and not `.yaml`!) at the same level of the `milton` folder and add your specific configuration for the bot, overriding any configs in the `default-config.yml` file. Note that the structure of the file must be identical to the first (I suggest copy-pasting it and changing what you need/like).

One config you must override is the `bot > token` field, providing your own [discord bot token](https://discord.com/developers/applications).

## Contribute with an extension

You can contribute to the bot by adding an extension that does something cool. Look into the examples folder for an example which can be copy-pasted. Extensions should be put in the `cogs` folder and loaded in the `bot.py` script. More information on how to correctly write extensions can be found in the [`discord.py` documentation](https://discordpy.readthedocs.io/en/latest/).

Code style is enforced by [`black`](https://github.com/psf/black).

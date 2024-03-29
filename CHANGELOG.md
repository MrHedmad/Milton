# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to (a thing similar to) [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The Major version is increased when large code changes are made, such as changes in the storage facility.
The Minor version is increased when commands are added or removed.
The Patch version is increased for any other change.

The `beta` tag is added when the bot has not been in production for long. Can be removed without increasing any patch number.


## [1.1.0-beta] - 2023-01-21
### Added
- Added a `--gen_config` command line option when starting the bot to make an empty config file.
- Added the `announcements` cog to handle e-mail announcements. This cog is **not** loaded by default.

### Changed
- Changed default file level logging to DEBUG (was INFO).


## [1.0.1-beta] - 2023-01-18
### Added
- Added a math rendering function. Simply type a math expression between `$$`s, and click on the eye reaction that Milton sends if it detects any math it can render.


## [1.0.1] - 2022-11-07
### Fixed
- Fixed a bug that prevented some PDFs from rendering properly.


## [1.0.0-beta] - 2022-10-20
### Changed
- Moved from MongoDB to SQLite. It should be faster, safer, and easier to set up.
- The xkcd cog can now handle sending the issue to multiple servers.
### Added
- Database schema migrations should be applied magically when the bot updates.


## [0.6.2] - 2022-10-14
### Fixed
- Some commands in the birthday cog were not migrated correctly. This should be fixed now.


## [0.6.1] - 2022-09-05
### Changed
- Added the `pdf_render` cog to automatically render PDF files that users upload in channels. The operation occurs completely in-memory. I'm not 100% sure that the bot will not crash if you upload a 10Gb PDF file, but discord's file size limitations should prevent any abuse.
- The above cog **is not** loaded by default.


## [0.6.0] - 2022-09-05
### Changed
- Updated the `discord.py` backend to version 2. Migrated the necessary commands.


## [0.5.0] - 2021-07-05
### Added
- Added the `xkcd` command.
- Added a periodic check for new issues of the above comic.


## [0.4.1] - 2021-07-02
### Changed
- !! Upgraded from Python 3.8 to Python 3.9 (again)
### Fixed
- Fixed a crash when using unknown commands in the CLI.
- Fixed errors showing up when closing the bot loop through the CLI.


## [0.4.0] - 2020-11-17
### Added
- Added some examples.
- Added a whole lot of documentation strings.

### Changed
- Changed a whole lot of configuration strings.
- Moved the description for the changelog (former changelog_typing.md) to the changelog_parser.py file.
- The Toys cog now uses the UserInputError exception correctly.

### Fixed
- Fixed a LOT of unused imports. *So many unused imports*.
- Fixed some type hits. Who knew what `Optional` meant?


## [0.3.0] - 2020-11-07
### Removed
- Bazza was (un)successfully banned. Removed the `bzban` command.


## [0.2.3] - 2020-11-07
### Changed
- More precise countdown for `bzban` as we are nearing *the time*.


## [0.2.2] - 2020-11-04
### Added
- Added a CLI command to list guilds that Milton can see.
- Added a CLI command to leave a guild Milton is in based on its ID.


## [0.2.1] - 2020-11-03
### Removed
- Removed the Arctic Cog.

### Fixed
- Some small backend fixes.


## [0.2.0] - 2020-11-03
### Added
- Support for the #Kick Bazza on the 8th of November movement.
- Added the Arctic Cog for Arctic-specific commands.
- Added a utility that searches for a Hide and Seek locations. Powered by Augurian.
- Added some backend checks.

### Changed
- !! Rolled back Python3.9 support. The ecosystem is too unprepared for now, and many packages do not have wheels already released.
- Small changes here and there.

## [0.1.1] - 2020-10-07
### Changed
- !! Upgraded from python 3.8 to python 3.9

### Removed
- Some stray files have been removed.

### Fixed
- Fixed some typos in the changelog.
- Fixed the birthday cog ignoring the `config.yml` file.


## [0.1.0-beta] - 2020-10-06
### Added
- !! Added the changelog and the `changelog` command.
- Added the `changelog link` command to provide a link to this same changelog on GitHub.
- We are now following a sort of Sematic Versioning. See the changelog directly on GitHub for more information.
- !! As the changelog has to be parsed, the semantics of it have to be preserved. Details in the `changelog_typing.md` file.

### Changed
- The bot version is no longer in the `VERSION` file but in the bot class itself.
- Now the bot's version is aligned to the changelog's latest version.

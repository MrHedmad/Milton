# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to (a thing similar to) [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The Major version is increased when large code changes are made, such as changes in the storage facility.
The Minor version is increased when commands are added or removed.
The Patch version is increased for any other change.

The `beta` tag is added when the bot has not been in production for long. Can be removed without increasing any patch number.

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

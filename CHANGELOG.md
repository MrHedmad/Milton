# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to (a thing similar to) [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The Major version is increased when large code changes are made, such as changes in the storage facility.
The Minor version is increased when commands are added or removed.
The Patch version is increased for any other change.

The `beta` tag is added when the bot has not been in production for long. Can be removed without increasing any patch number.

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

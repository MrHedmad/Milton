# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to (a thing similar to) [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The Major version is increased when large code changes are made, such as changes in the storage facility.
The Minor version is increased when commands are added or removed.
The Patch version is increased for any other version.

The `beta` tag is added when the bot has not been in production for long. Can be removed without increasing any patch number.

## [0.1.0-beta] - 2020-10-06
### Added
- !! Added the changelog and the `changelog` command.
- Added the `changelog list` command to provide a link to this same changelog on GitHub.
- We are now following a sort of Sematic Versioning. See the changelog directly on GitHub for more information.
- !! As the changelog has to be parsed, the semantics of it have to be preserved. Details in the `changelog_typing.md` file.

### Changed
- The bot version is no longer in the `VERSION` file but in the bot class itself.
- Now the bot's version is aligned to the changelog's latest version.
-

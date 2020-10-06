This file describes what is allowed in the changelog. The allowed line types are these:

# Header
Metaline

## Page Header
- Chunkless line
- !! Important chunkless line
### Chunk Header
- Chunk line
- !! Important chunk line


They are treated as follows:
> Header
Completely Ignored

> Metaline
Ignored

> Page Header
Must be of the following type:
    \[MAJOR.MINOR.PATCH-[[, -TAG], -HASH]\] - \(YEAR-MONTH-DAY\)
    OR
    \[Unreleased\]
It is parsed to the changelog. The first non-unreleased header version is the version of the bot.

> Chunkless line and Important chunkless line
Completely Ignored

> Chunk Header
Must be a word in this list (case insensitive):
    (ADDED, CHANGED, REMOVED, DEPRECATED, FIXED, SECURITY, BALANCE)
It is parsed in the changelog.

> Chunk line and Important Chunk line
Parsed to the changelog.

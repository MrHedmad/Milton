# The migration files

Every file in this dir and listed in the `migrations.txt` will be applied to 
the database. The first one is considered the "empty" schema. The others are considered as transactions from the previous to the new schemas.

For example, if the `migrations.txt` file contains:
```
initial.sql
second.sql
other.sql
```
Then `initial.sql` is the "new database" schema. The latest version of the db
is stored in `other.sql`. On startup, if the database is at a version other than
`other.sql`, then the other migrations will be applied, in order, to get to the
latest versions. In this case, if the db is on version `initial`, Milton will
apply `second.sql` then `other.sql`, setting the final version to `other`.

Changing this file must be done with care, as it could break old milton instances.

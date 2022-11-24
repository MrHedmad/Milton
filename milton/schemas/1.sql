CREATE TABLE announcement_user_data (
    user_id PRIMARY KEY,
    guild_id NOT NULL,
    user_email NOT NULL
);

CREATE TABLE announcement_guild_config (
    guild_id PRIMARY KEY,
    announcement_channel INT NOT NULL
);

CREATE TABLE announcement_roles (
    guild_id PRIMARY KEY,
    role INT NOT NULL
);

UPDATE version SET version = 1 WHERE Id = 0;

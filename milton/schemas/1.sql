CREATE TABLE announcement_user_data (
    user_id NOT NULL UNIQUE,
    guild_id NOT NULL,
    user_email NOT NULL
);

CREATE TABLE announcement_guild_config (
    guild_id PRIMARY KEY,
    announcement_channel INT UNIQUE NOT NULL
);

CREATE TABLE announcement_roles (
    guild_id INT NOT NULL,
    role INT NOT NULL UNIQUE
);

UPDATE version SET version = 1;

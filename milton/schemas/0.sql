CREATE TABLE version (
    version INT
);

INSERT INTO version (version) VALUES (0);

CREATE TABLE birthdays (
    guild_id INT,
    user_id INT,
    year INT,
    day INT NOT NULL,
    month INT NOT NULL
);

CREATE TABLE guild_config (
    guild_id INT PRIMARY KEY,
    bday_shout_channel INT,
    xcd_shout_channel INT
);

CREATE TABLE meta (
    last_sent_xkcd TEXT
);

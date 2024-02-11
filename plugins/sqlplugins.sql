-- This is a toy database definition that provides a working environment
-- for testing tattler plugins.
--
-- See https://docs.tattler.dev/quickstart.html
BEGIN;

CREATE TABLE IF NOT EXISTS "auth_user" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "email" varchar(254) NOT NULL,
    "password" varchar(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS "userprofile" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "first_name" varchar(256) NULL,
    "last_name" varchar(256) NULL,
    "language" varchar(5) NULL,
    "mobile_number" varchar(20) NULL,
    "telegram_id" varchar(20) NULL,
    "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);

INSERT INTO auth_user VALUES(1,'your@email.net','pbkdf2_sha256$720000$lP7x1sV5nU469b80EaWI93$r4oR5LcymNIS5/VkfAisQ9KGhPVnx9TwYhVn+jtOmww=');
INSERT INTO userprofile VALUES(1,'Michelle','Obama','EN','+1789456321','5689234578',1);

INSERT INTO auth_user VALUES(2,'another@organization.com','pbkdf2_sha256$720000$lP7x1sV5nU469b80EaWI93$r4oR5LcymNIS5/VkfAisQ9KGhPVnx9TwYhVn+jtOmww=');
INSERT INTO userprofile VALUES(2,'Angela','Merkel','DE','+49859456321','4689132165',2);

CREATE TABLE IF NOT EXISTS "resource" (
    "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "traffic" UNSIGNED BIG INT NULL
);

INSERT INTO resource VALUES(1,965373706);
INSERT INTO resource VALUES(2,1224994602);

CREATE TABLE IF NOT EXISTS "billing" (
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "number" varchar(20) NOT NULL,
    "paid" integer NOT NULL DEFAULT 0
);

INSERT INTO billing VALUES(1, "2024010001", 0);
INSERT INTO billing VALUES(1, "2024021001", 1);
INSERT INTO billing VALUES(2, "2023123001", 1);

COMMIT;

create TABLE log (
    id bigint(20) not null,
    msg varchar(8000),
    url varchar(1024),
    method varchar(100),
    status_ varchar(1024),
    ip varchar(20),
    "time" timestamp not null default 'CURRENT_TIMESTAMP',
    PRIMARY KEY (id)
);
create TABLE sessions (
    id varchar(300) not null,
    user_id bigint(20) not null,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);
CREATE UNIQUE INDEX unique_user_id ON sessions (user_id);
create TABLE users (
    id bigint(20) not null,
    name varchar(64) not null,
    pass_sha256 varchar(300) not null,
    is_admin tinyint(1) default '0',
    is_activated tinyint(1) default '0',
    has_avatar tinyint(1) not null default '0',
    email varchar(1024),
    activation_code varchar(300),
    file_extension varchar(10),
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX unique_activation_code ON users (activation_code);
CREATE UNIQUE INDEX unique_email ON users (email);
CREATE UNIQUE INDEX unique_name ON users (name);
create TABLE friends (
    "user" bigint(20),
    friend bigint(20),
    id bigint(20) not null,
    PRIMARY KEY (id),
    FOREIGN KEY ("user") REFERENCES users (id),
    FOREIGN KEY (friend) REFERENCES users (id)
);
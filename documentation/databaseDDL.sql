CREATE TABLE sessions
(
    id VARCHAR(300) PRIMARY KEY NOT NULL,
    user_id BIGINT NOT NULL
);
CREATE TABLE users
(
    id BIGINT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    name VARCHAR(64) NOT NULL,
    pass_sha256 VARCHAR(300) NOT NULL
);
ALTER TABLE sessions ADD FOREIGN KEY (user_id) REFERENCES users (id);
CREATE UNIQUE INDEX unique_user_id ON sessions (user_id);
CREATE UNIQUE INDEX unique_name ON users (name);

-- Exported definition from 2007-12-04T17:57:39
-- Class jcl.model.account.User
-- Database: sqlite
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    jid TEXT,
    has_received_motd TINYINT,
    child_name VARCHAR(255)
)

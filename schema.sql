PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS app_metadata (
 key TEXT PRIMARY KEY, value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ranks (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, title TEXT NOT NULL,
 min_exp INTEGER NOT NULL CHECK(min_exp >= 0), category TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT NOT NULL COLLATE NOCASE UNIQUE,
 email TEXT NOT NULL COLLATE NOCASE UNIQUE,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL DEFAULT 'member' CHECK(role IN ('member','admin')),
 exp INTEGER NOT NULL DEFAULT 0 CHECK(exp >= 0),
 avatar TEXT NOT NULL DEFAULT 'tippy',
 verified INTEGER NOT NULL DEFAULT 0,
 banned INTEGER NOT NULL DEFAULT 0,
 rank_override INTEGER REFERENCES ranks(id),
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL, description TEXT NOT NULL, event_type TEXT NOT NULL,
 start_time TEXT NOT NULL, end_time TEXT NOT NULL,
 reward_exp INTEGER NOT NULL CHECK(reward_exp >= 0),
 min_exp INTEGER NOT NULL DEFAULT 0 CHECK(min_exp >= 0),
 location TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','closed')),
 capacity INTEGER NOT NULL DEFAULT 100 CHECK(capacity > 0),
 art TEXT NOT NULL DEFAULT 'birthday',
 created_by INTEGER REFERENCES users(id), created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS event_registrations (
 id INTEGER PRIMARY KEY AUTOINCREMENT, event_id INTEGER NOT NULL REFERENCES events(id),
 user_id INTEGER NOT NULL REFERENCES users(id),
 status TEXT NOT NULL DEFAULT 'registered' CHECK(status IN ('registered','attended')),
 registered_at TEXT NOT NULL, awarded_at TEXT,
 UNIQUE(event_id,user_id)
);
CREATE TABLE IF NOT EXISTS posts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id),
 author_name TEXT, title TEXT NOT NULL, content TEXT NOT NULL, category TEXT NOT NULL,
 is_announcement INTEGER NOT NULL DEFAULT 0, is_pinned INTEGER NOT NULL DEFAULT 0,
 locked INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS comments (
 id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
 user_id INTEGER NOT NULL REFERENCES users(id), content TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS post_likes (
 post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
 user_id INTEGER NOT NULL REFERENCES users(id), created_at TEXT NOT NULL,
 PRIMARY KEY(post_id,user_id)
);
CREATE TABLE IF NOT EXISTS exp_transactions (
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id),
 amount INTEGER NOT NULL, reason TEXT NOT NULL, reference TEXT NOT NULL UNIQUE,
 created_at TEXT NOT NULL, local_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS checkins (
 user_id INTEGER NOT NULL REFERENCES users(id), local_date TEXT NOT NULL,
 created_at TEXT NOT NULL, PRIMARY KEY(user_id,local_date)
);
CREATE TABLE IF NOT EXISTS audit_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER REFERENCES users(id),
 action TEXT NOT NULL, details TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_attempts (
 fingerprint TEXT PRIMARY KEY, count INTEGER NOT NULL, first_at REAL NOT NULL
);

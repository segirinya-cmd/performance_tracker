-- schema.sql
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS performance_metrics;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin', 'trainer', 'scout')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    primary_position TEXT NOT NULL,
    preferred_foot TEXT CHECK(preferred_foot IN ('Left', 'Right', 'Both')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    recorded_by INTEGER NOT NULL,
    session_date DATE NOT NULL,
    sprint_30m_sec REAL NOT NULL,        -- Lower is better
    agility_test_sec REAL NOT NULL,     -- Lower is better
    passing_accuracy_pct REAL NOT NULL, -- 0 to 100
    stamina_score REAL NOT NULL,        -- 0 to 100
    coach_rating REAL NOT NULL,         -- 1.0 to 10.0
    video_url TEXT,                     -- External video link as per proposal scope
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (recorded_by) REFERENCES users(id)
);

CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
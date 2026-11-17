CREATE TABLE IF NOT EXISTS scenarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  params_json TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scenario_id INTEGER REFERENCES scenarios(id) ON DELETE CASCADE,
  strategy TEXT NOT NULL,
  avg_wait REAL, p90_wait REAL, max_wait REAL,
  avg_queue REAL, peak_queue INTEGER,
  utilisation REAL, staff_minutes REAL, est_error REAL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS run_series (
  run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
  t REAL, queue_length INTEGER
);
CREATE TABLE IF NOT EXISTS counter_stats (
  run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
  counter_no INTEGER, utilisation REAL, busy_minutes REAL
);
CREATE TABLE IF NOT EXISTS validations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scenario_id INTEGER REFERENCES scenarios(id) ON DELETE CASCADE,
  strategy TEXT, mean_wait REAL, ci95 REAL, win_rate REAL, runs INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

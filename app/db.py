import sqlite3
from flask import current_app, g

SCHEMA = '''
CREATE TABLE IF NOT EXISTS patients (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, is_simulated INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS observations (id INTEGER PRIMARY KEY, event_id TEXT NOT NULL UNIQUE, patient_id TEXT NOT NULL REFERENCES patients(id), observed_at TEXT NOT NULL, heart_rate REAL, respiratory_rate REAL, oxygen_saturation REAL, systolic_bp REAL, temperature REAL, is_simulated INTEGER NOT NULL DEFAULT 1, quality TEXT NOT NULL DEFAULT 'valid');
CREATE INDEX IF NOT EXISTS obs_patient_time ON observations(patient_id, observed_at DESC);
CREATE TABLE IF NOT EXISTS assessments (id INTEGER PRIMARY KEY, observation_id INTEGER NOT NULL UNIQUE REFERENCES observations(id), category TEXT NOT NULL, explanation TEXT NOT NULL, triggered_rules TEXT NOT NULL, model_score REAL, model_version TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY, assessment_id INTEGER NOT NULL UNIQUE REFERENCES assessments(id), patient_id TEXT NOT NULL REFERENCES patients(id), category TEXT NOT NULL, explanation TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL, acknowledged_at TEXT, acknowledged_by TEXT);
CREATE TABLE IF NOT EXISTS audit_events (id INTEGER PRIMARY KEY, alert_id INTEGER REFERENCES alerts(id), event_type TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
'''
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db
def init_db(app):
    with app.app_context(): get_db().executescript(SCHEMA); get_db().commit()
    @app.teardown_appcontext
    def close_db(_=None):
        db = g.pop('db', None)
        if db is not None: db.close()

# TriagePulse AI

Educational emergency-care decision-support prototype for the IBM Z Datathon 2026. **Not a medical device, not clinically validated, and not for real patient care.** It does not diagnose or prescribe. All generated data is fictional; rule categories are software-defined review signals, not approved triage categories.

## Local setup (Windows PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python run.py
```

Open `http://127.0.0.1:8000`. The app creates `instance/triagepulse.sqlite3`. Set `TRIAGEPULSE_DB` to move it to a persistent writable path. Keep `.env`, databases, model artifacts, and keys out of source control.

## Demo and development

Use the dashboard simulator's Normal, Concerning, or Invalid scenario. The scenario controls are session-local and browser-side, with at most one timer per page. Generate initial records with `python scripts/generate_demo_data.py`. Run checks with `python -m pytest`. Evaluate model availability with `python scripts/evaluate_model.py`; no model is shipped because no authorized, outcome-labelled data is configured. Optional serial load measurement: `python scripts/load_test.py --events 100`.

## API

`GET /health`, `GET /api/v1/metrics`, dashboard summary/activity, patient list/detail/timeline, observation POST/list, alert list/detail/acknowledge, and simulator status/start/pause/resume/reset are under `/api/v1`. Observation input takes `event_id` (optional, generated if absent), `patient_id`, optional ISO `observed_at`, any subset of `heart_rate`, `respiratory_rate`, `oxygen_saturation`, `systolic_bp`, `temperature`, and `is_simulated`. At least one measurement is required. See `docs/architecture.md`.

## Status and limitations

The app uses Flask and Python's SQLite interface with transactional persistence. Assessment uses transparent, versioned demonstration rules. No clinical dataset or model is included. API timing percentiles are measured from a bounded in-memory sample and reset on restart. The prototype has been deployed to the LinuxONE RHEL 9.8 / s390x VM at `148.100.99.197`, runs as `linux1` under systemd, and binds only to loopback port 8000. Access it from Windows through the SSH tunnel in `deployment/linuxone-rhel.md`. The deployment smoke test and persistence check are recorded there. This remains an educational prototype, not a clinical or production medical system.

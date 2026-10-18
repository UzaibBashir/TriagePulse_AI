# Three-minute demonstration

- 0:00–0:30: Describe the challenge of keeping up with changing observations; explain that all records here are fictional.
- 0:30–1:10: Start Scenario A and show the patient list and live event count.
- 1:10–2:00: Reset and start Scenario B. Open a patient timeline, inspect the rule explanation, and acknowledge its alert.
- 2:00–2:30: Show `/health`, `/api/v1/metrics`, and the SQLite persistence location. Use the load script for measured local request timings; label the actual machine and run size.
- 2:30–3:00: Explain human review, educational scope, lack of clinical validation, and the need for authorized outcome-labelled data before evaluating a predictive model.

Offline fallback: run `python scripts/generate_demo_data.py` before presenting. Never present synthetic metrics as deployment or clinical results.

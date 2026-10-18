# IBM LinuxONE deployment (RHEL / s390x)

## Verified deployment

The prototype is deployed to `linux1@148.100.99.197`.

- VM: RHEL 9.8, IBM Z `s390x`, Python 3.9.25, 7.3 GiB RAM, 50 GiB root filesystem.
- Service: `triagepulse.service`, enabled at boot, running as unprivileged user `linux1` with Gunicorn 23.0.0 (one worker, to keep simulator state consistent).
- Application: `/home/linux1/triagepulse-ai`; isolated Python environment at `.venv`.
- Persistent SQLite data: `/home/linux1/triagepulse-data/triagepulse.sqlite3`.
- Protected environment file: `/etc/triagepulse.env` (root-owned, mode 600).
- Listen address: `127.0.0.1:8000`. No public application port or firewall rule was added. The existing firewall allowed SSH and rejected other new inbound connections.
- A systemd execution restriction prevented launching Python through its symlink inside the home directory. The unit invokes `/usr/bin/python3` and loads Flask/Gunicorn from the isolated environment using `PYTHONPATH`; SELinux remains enforcing.
- The local private key was used without disclosing its contents and its Windows ACL was restricted for OpenSSH. The archive sent to the VM excluded key files.

Verified on 2026-10-18: `/health` responded; the dashboard HTML loaded; a synthetic observation was accepted, assessed as `Critical rule triggered`, and persisted with an alert; a repeated event ID was rejected as a duplicate; acknowledgement persisted; the service restarted successfully and retained the observation and acknowledgement. Access through a temporary SSH tunnel on local port 18080 returned the same persisted event. Four LinuxONE API tests passed (`4 passed`).

Performance sample on the LinuxONE VM: 100 sequential synthetic POST requests, one client, no concurrency, same-host loopback to Gunicorn and SQLite. Measured request latency: p50 2.48 ms, p95 3.13 ms, p99 5.20 ms; summed request duration 0.26 seconds. This is a small prototype smoke-load sample, not a capacity benchmark or guarantee. The database currently contains 101 synthetic observations across 11 synthetic patients (100 load-test records plus one alert/acknowledgement verification record). No clinical model or dataset was deployed.

## Access through the SSH tunnel

Use a separate Windows PowerShell window. Substitute the local path to the SSH key; do not copy key material into the repository or send its contents to anyone.

```powershell
ssh -i "C:\path\to\key.pem" -N -L 8000:127.0.0.1:8000 linux1@148.100.99.197
```

Open `http://127.0.0.1:8000`. If local port 8000 is already occupied, choose another local port, such as `18080`, and change only the first port in `-L 18080:127.0.0.1:8000`; open `http://127.0.0.1:18080`.

## Service operations

```powershell
ssh -i "C:\path\to\key.pem" linux1@148.100.99.197 "sudo systemctl status triagepulse.service --no-pager"
ssh -i "C:\path\to\key.pem" linux1@148.100.99.197 "sudo systemctl restart triagepulse.service"
ssh -i "C:\path\to\key.pem" linux1@148.100.99.197 "sudo journalctl -u triagepulse.service -n 50 --no-pager"
```

The existing service unit is in `deployment/systemd/triagepulse.service`. Service logs go to the system journal. The SQLite directory is separate from source and restricted to `linux1`. Gunicorn is bound to loopback; access from a workstation requires the SSH tunnel above.

## Rollback and backup

Before an application upgrade, stop and preserve the existing source, service unit, environment file, and SQLite database. Use SQLite's backup API or `sqlite3 .backup` for a consistent database copy; retain the previous application release until the new service passes health, ingestion, alert, and persistence checks. The VM does not provide a verified independent backup. Keep a separate copy of the database and release outside the VM before relying on this deployment.

## Fresh-host inspection and deployment notes

For another VM, first inspect `whoami`, OS version, `uname -m`, Python, memory, disk, listening ports, running services, firewall rules, writable paths, and systemd. Do not assume the target has the same policy as this VM. Here, RHEL's `python3-pip` package was absent, so it was installed using `sudo dnf install -y python3-pip`; Flask and Gunicorn were installed only in the application's virtual environment. No SSH settings, firewall rules, or system Python installation were changed. Keep Flask debug mode off and do not bind to `0.0.0.0` for the initial deployment.

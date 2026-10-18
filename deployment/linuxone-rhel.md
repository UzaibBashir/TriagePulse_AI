# IBM LinuxONE deployment (RHEL / s390x)

Deployment has not been run: no SSH host or key is available in the environment. Inspect the supplied VM first. Use only account `linux1`; do not enable password or root SSH, change firewall rules, or expose port 8000 publicly. Place the release in a user-owned directory and SQLite in a separate persistent writable directory. Confirm OS, `uname -m`, Python, memory, disk, ports, services, firewall, directory permissions, and systemd before making changes.

From Windows PowerShell, substitute the actual host and key path (never put the key in the repository):

```powershell
ssh -i "C:\path\to\key.pem" linux1@YOUR_SERVER_IP
scp -i "C:\path\to\key.pem" -r .\* linux1@YOUR_SERVER_IP:~/triagepulse-ai/
```

On the VM, check Python and architecture compatibility before installing:

```bash
whoami; uname -m; cat /etc/os-release; python3 --version; free -h; df -h; ss -lnt
mkdir -p ~/triagepulse-ai ~/triagepulse-data
cd ~/triagepulse-ai
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
TRIAGEPULSE_DB=$HOME/triagepulse-data/triagepulse.sqlite3 python run.py
```

The app binds to `127.0.0.1:8000`. On Windows, establish the SSH tunnel in another PowerShell window:

```powershell
ssh -i "C:\path\to\key.pem" -N -L 8000:127.0.0.1:8000 linux1@YOUR_SERVER_IP
```

Open `http://127.0.0.1:8000`. Verify `/health`, submit a synthetic observation, inspect its alert and verify persistence across a controlled restart. A systemd unit should be created only after the VM's actual policy and systemd availability are confirmed. Back up database and release before replacing them; no server access, deployment, or backup has been verified for this repository.

# HOW TO RUN

**This file is outdated. See the root [README.md](../README.md) for the one-command workflow.**

---

## TL;DR

From anywhere in WSL:

```bash
cd /mnt/d/Coding-projects/outbound-caller-python-main
./call.sh 9415180701 Chris
```

That one command starts the agent, starts the dashboard, and dispatches a call.

Watch live:

- **Browser:** <http://localhost:8080>
- **Terminal:** `tail -f /tmp/emma-agent.log`

Stop everything:

```bash
pkill -f "python3 agent.py"
pkill -f "uvicorn dashboard"
```

For voice changes, prompt edits, and troubleshooting, see [../README.md](../README.md).

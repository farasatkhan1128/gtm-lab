# Self-Hosted AI GTM Lab — Notes

## Day 2 — Docker Concepts, Hands-On (7 Jul 2026)

### Core idea of the day
**Container = disposable compute. Volume = persistent data.**
The container is throwaway — it can be stopped, removed and rebuilt.
My work does NOT live in the container. It lives in the volume.

### Why my Lead Intake workflow survived overnight
I closed everything and rebooted, so yesterday's container was stopped.
A fresh container started this morning, yet my workflow was still there.
It survived because it lives in the **n8n_data volume**, not in the container.
The volume is persistent storage that Docker manages on my machine,
independent of any container. Container died, volume kept my work, new
container picked it back up.

### The Docker client vs engine split
- **Docker Desktop (the app with the whale)** = the ENGINE. It does the real
  work of running containers.
- **The `docker` command in PowerShell** = a REMOTE CONTROL that sends
  instructions to the engine.
- If the engine is off, `docker` commands fail with
  "cannot find the file specified" — nothing is broken, the engine is just off.
  Fix: open Docker Desktop, wait for "Engine running", try again.

### Docker Desktop auto-restarts containers
When I reopened Docker Desktop, the engine came back on and automatically
resumed my n8n container from yesterday. That's why n8n was already running
without me relaunching it.

### The container lifecycle
created -> running -> stopped -> removed
- Stop n8n  -> browser at localhost:5678 fails to load (nothing behind the door)
- Start n8n -> refresh browser, workflow is back
- The data never moved. Only the compute stopped and started.

### Commands cheat-sheet
```
docker ps               list running containers
docker ps -a            list all containers (incl stopped)
docker volume ls        list volumes  (I can see n8n_data here)
docker stop <name>      stop a running container
docker start <name>     start a stopped container
docker restart <name>   restart it
docker logs <name>      view its output/logs
docker inspect <name>   full config (find the "Mounts" section = where data lives)
docker run -d ...       run detached (background, gives terminal back)
```

### About the run flags
- `-d`   detached / background (terminal stays free, n8n keeps running)
- `--rm` auto-deletes the CONTAINER when it stops (safe: data is in the volume)
- `--name n8n` names the container
- `-p 5678:5678` port mapping (my machine's 5678 -> container's 5678)
- `-v n8n_data:/home/node/.n8n` attaches the volume to where n8n stores data

### Interview explanation (say out loud)
"I run n8n as a Docker container with a named volume. The container itself is
disposable — I can stop, remove and rebuild it — but all my workflows and
credentials persist in the volume, so nothing is lost on restart. That
separation of ephemeral compute from persistent state is how I keep the
self-hosted setup reliable."

### Why this matters for GTM Engineering
Every GTM system runs somewhere. Knowing the container lifecycle and where
data actually lives is what separates a GTM Engineer who runs infrastructure
from someone who just clicks buttons in a no-code tool. "I self-host n8n and
my workflows persist in a named volume across restarts" is the language of
someone who owns their stack.

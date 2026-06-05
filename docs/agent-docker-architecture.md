# Agent Docker Container: Architecture, Persistence, and Recovery

**Agents:** Hermes · OpenClaw · Pi  
**LLM Backend:** External API (URL-injected at runtime)  
**Document Purpose:** Full system design, agent awareness requirements, and operator recovery runbook

---

## Table of Contents

1. [The Problems](#1-the-problems)
2. [Solution Architecture](#2-solution-architecture)
3. [Filesystem Map: What Persists and What Doesn't](#3-filesystem-map)
4. [Agent Awareness Design](#4-agent-awareness-design)
5. [When Things Go Wrong: Recovery Runbook](#5-recovery-runbook)
6. [Backup and Snapshot Strategy](#6-backup-and-snapshot-strategy)
7. [Implementation Files](#7-implementation-files)
8. [Conclusions](#8-conclusions)

---

## 1. The Problems

### 1.1 Docker's Ephemeral Filesystem

Docker images are built from stacked, read-only layers. When a container starts, Docker creates a thin **writable overlay layer** on top. Every file the container creates or modifies lives in this overlay. When the container **stops and restarts** — whether due to a reboot, a `docker compose restart`, or a crash — that overlay is discarded, and the filesystem resets to the image state.

For an ordinary stateless web service, this is correct behavior. For a container where Hermes, OpenClaw, and Pi are actively managing the system — creating files, installing tools, and writing configuration — this means everything they do is silently erased on restart unless we explicitly opt specific paths out of ephemeral behavior using **Docker named volumes**.

The risk is not just inconvenience. An agent that doesn't know which parts of its filesystem are ephemeral will install software to the wrong paths, write state to locations that vanish, and behave inconsistently across restarts in ways that are difficult to diagnose.

### 1.2 LLM API URL Injection

All three agents share a single external LLM API endpoint. This URL (and its credentials) must be:

- **Not baked into the image** — secrets in images are a security liability, and rebuilding the image to change an endpoint is unnecessary friction
- **Available at startup to all agents** — without each needing its own configuration file
- **Easy to rotate** — changing providers, pointing to a local inference server, or swapping models should require only an environment variable change and a restart

### 1.3 Agent Corruption is Inevitable

Agents with full system access will eventually write to the wrong paths. This is not a failure of instruction design — it is a property of sufficiently capable agents operating in a rich, ambiguous environment. Causes include:

- Following tutorials or documentation that assume a traditional Linux install
- Post-install scripts that write to system paths as a side effect
- Resolving a problem in the most direct way rather than the architecturally correct way
- Logical mistakes under novel conditions

The system must be designed so that when this happens, the path from detection to recovery is short, clear, and executable by an operator who is not a Docker expert.

---

## 2. Solution Architecture

### 2.1 LLM API via Environment Variables

The API endpoint, key, and default model are passed as environment variables at container startup. They are never written into the image or into any configuration file that travels with it.

**`.env` file (host machine, excluded from version control):**
```env
LLM_API_URL=https://your-llm-endpoint/v1
LLM_API_KEY=sk-your-key-here
LLM_API_MODEL=your-default-model
```

Agents read these at startup:
```python
import os
api_url   = os.environ["LLM_API_URL"]
api_key   = os.environ.get("LLM_API_KEY", "")
api_model = os.environ.get("LLM_API_MODEL", "default")
```

Swapping the backend — changing providers, pointing to a local llama.cpp server, changing models — requires editing `.env` and running `docker compose restart`. No rebuild required.

### 2.2 Volume Strategy

Named Docker volumes are mounted over every path the agents are expected to modify. Docker creates and manages these volumes on the host; they persist until explicitly deleted.

| Volume Name        | Mount Path       | What It Preserves                                          |
|--------------------|------------------|------------------------------------------------------------|
| `agent_home`       | `/home/`         | Agent workspaces, user configs, `.local`, `.config`, files |
| `agent_local`      | `/usr/local/`    | pip/pipx installs, compiled tools, local binaries          |
| `agent_opt`        | `/opt/`          | conda, nix, micromamba, self-contained app installs        |
| `agent_varlib`     | `/var/lib/`      | apt package database, application state, database files    |
| `agent_varcache`   | `/var/cache/`    | apt package cache, downloaded archives                     |
| `agent_etc`        | `/etc/`          | System-wide configuration changes *(see warning)*          |
| `agent_logs`       | `/var/log/`      | Persistent logs, change records, corruption reports        |

> ⚠️ **`/etc` Warning:** This is the highest-risk volume. A single corrupted file — `/etc/sudoers`, `/etc/passwd`, `/etc/resolv.conf` — can make the container unbootable or leave agents unable to escalate privileges. It must be volume-mounted to preserve intentional configuration, but it must also be the first volume backed up and the one treated with the most caution. See Section 5.2 for recovery.

### 2.3 What Remains Ephemeral

The following paths are **not** volume-mounted. They are part of the image layer and **reset automatically on every restart**:

```
/bin        /sbin        /usr/bin      /usr/sbin
/usr/lib    /lib         /lib64        /tmp          /run
```

This is intentional. If an agent installs a binary to `/usr/bin` or modifies a system library in `/usr/lib`, the next restart cleans it up automatically. Ephemeral-path corruption is **self-healing**. This is a feature — lean into it. The Docker image should contain everything the agents reliably need at startup; treat agent-driven writes as temporary unless they go to a volume path.

---

## 3. Filesystem Map

This map is the single most important piece of information all three agents must internalize.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DOCKER IMAGE LAYER                           │
│                 (read-only baked in — RESETS ON RESTART)            │
│                                                                     │
│   /bin   /sbin   /usr/bin   /usr/sbin   /usr/lib   /lib   /tmp      │
│                                                                     │
│   ✗ Do NOT install software here expecting it to persist            │
│   ✓ Changes here are automatically cleaned up on restart            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         DOCKER VOLUMES                              │
│              (read-write — PERSIST ACROSS RESTARTS)                 │
│                                                                     │
│   /home/          ← PRIMARY workspace for all agents                │
│   /usr/local/     ← pip, pipx, compiled installs                    │
│   /opt/           ← conda, nix, self-contained runtimes             │
│   /var/lib/       ← apt state, database files, app state            │
│   /var/cache/     ← apt/package caches                              │
│   /etc/           ← system config (⚠ handle with caution)           │
│   /var/log/       ← logs, agent change records                      │
│                                                                     │
│   ✓ Work, installs, and configs written here survive restart        │
│   ⚠ Corruption here requires manual recovery                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     HOST READ-ONLY MOUNT                            │
│                  (injected by operator, agents cannot modify)       │
│                                                                     │
│   /recovery/      ← backup scripts, recovery tools, this manifest   │
└─────────────────────────────────────────────────────────────────────┘
```

**Software install decision tree for agents:**

```
Need to install a tool?
│
├─ Python package?
│   └─ Use: pipx install <tool>  OR  pip install --user <pkg>
│       Writes to: /usr/local/bin or /home/agent/.local  ✓ PERSISTED
│
├─ Needs conda/scientific stack?
│   └─ Use: micromamba install -p /opt/conda
│       Writes to: /opt/conda  ✓ PERSISTED
│
├─ System package (apt)?
│   └─ Use: sudo apt install <pkg>   (acceptable but non-ideal)
│       Binaries go to: /usr/bin     ✗ EPHEMERAL (lost on restart)
│       apt state goes to: /var/lib  ✓ PERSISTED
│       → Prefer pipx/conda alternatives when available
│
├─ Compiled from source?
│   └─ Install to: /usr/local/  (./configure --prefix=/usr/local)
│       ✓ PERSISTED
│
└─ NEVER: install directly to /usr/bin, /usr/lib, /bin, /lib
    These are EPHEMERAL and will be erased on restart
```

---

## 4. Agent Awareness Design

### 4.1 The Container Manifest

A file `/container-manifest.md` is baked into the Docker image as a **read-only, world-readable document**. It is the canonical reference for what the container is, how it's structured, and what agents must and must not do. It is loaded into each agent's context at startup — either injected into the system prompt or made the first document in the context window.

This is not optional documentation. It is infrastructure.

**Key contents of `/container-manifest.md`:**

```markdown
# Container Manifest — Required Reading Before Taking Any Action

You are operating inside a managed Docker container. Three agents share
this environment: Hermes, OpenClaw, and Pi. All three access an external
LLM API via the LLM_API_URL environment variable.

## Filesystem: What Persists and What Does Not

PERSISTED (survives restart — safe to write work here):
  /home/          your primary workspace
  /usr/local/     local software installs
  /opt/           conda, nix, self-contained runtimes
  /var/lib/       system app state
  /var/log/       logs

EPHEMERAL (resets on restart — anything written here is temporary):
  /bin  /usr/bin  /usr/sbin  /usr/lib  /lib  /tmp

## Rules You Must Follow

1. All work files belong in /home/agent or /home/agent/workspace
2. Install Python packages with pipx or pip --user, not pip (system)
3. Install compiled tools to /usr/local, not /usr/bin
4. For scientific packages, use micromamba to /opt/conda
5. Before any change to /etc, back up the affected file:
   cp /etc/<file> /home/agent/.backups/etc/<file>.$(date +%s)
6. Log every significant system change:
   echo "$(date -u) | ACTION: <what you did>" >> /var/log/agent-changes.log
7. If you believe you have corrupted a system file, stop further system
   changes immediately and write a report to /var/log/corruption-report.txt

## Recovery

If you have damaged the environment, the operator will use the procedures
in /recovery/. Do not attempt to repair critical system files unless you
have confirmed via /var/log/agent-changes.log exactly what changed.
```

### 4.2 System Prompt Injection

Each agent must receive the manifest at startup. The entrypoint script reads it and exports it into the environment:

**`entrypoint.sh`:**
```bash
#!/bin/bash
export CONTAINER_MANIFEST=$(cat /container-manifest.md)
echo "$(date -u) | Container started" >> /var/log/agent-startup.log
exec "$@"
```

Each agent's initialization code prepends it to the system prompt:

```python
import os

manifest = os.environ.get("CONTAINER_MANIFEST", open("/container-manifest.md").read())

SYSTEM_PROMPT = f"""
{manifest}

---

{AGENT_SPECIFIC_INSTRUCTIONS}
"""
```

### 4.3 Per-Agent Risk Profiles and Guidance

Each agent has a different operational profile and therefore a different risk surface:

**Hermes** (coordination, messaging, task routing)  
- Risk level: **Low** — primarily reads and writes structured data, manages inter-agent communication  
- Key guidance: Do not install communication libraries system-wide. Write all message queues, logs, and routing tables to `/home/hermes/`. Do not modify `/etc/hosts` or network configuration without explicit operator instruction.

**OpenClaw** (system operations, tool execution, environment management)  
- Risk level: **High** — the most likely agent to install packages, modify configuration, and interact with the OS directly  
- Key guidance: Treat every system-level action as potentially irreversible. Log before executing, not after. For any change to `/etc`, always create a timestamped backup in `/home/agent/.backups/etc/` first. When in doubt between a system-level and user-space solution, always choose user-space.

**Pi** (analysis, computation, data processing)  
- Risk level: **Medium** — frequently installs data science packages; heavy `/tmp` usage  
- Key guidance: All package installation via micromamba to `/opt/conda`. Do not use system pip. Write all intermediate computation outputs to `/home/pi/scratch/` rather than `/tmp` (which is ephemeral). Large datasets should go to `/home/pi/data/` to persist across sessions.

---

## 5. Recovery Runbook

Recovery scenarios are ordered from least to most severe. Identify your scenario, then follow the steps exactly.

---

### 5.1 Scenario A: Ephemeral Path Corruption

**Symptoms:** An agent installed a binary to `/usr/bin` or modified a library in `/usr/lib`. The tool works now but will be gone after restart. Or: the container is currently misbehaving due to a bad system binary.

**Self-healing:** Yes. These paths are image-layer. A restart resets them.

**Recovery:**
```bash
docker compose restart
```

That's it. The image layer overwrites all ephemeral paths. Check `/var/log/agent-changes.log` afterward to understand what changed and update the agent's guidance if it made the same mistake twice.

---

### 5.2 Scenario B: Broken `/etc` — Container Starts but Agents Can't Function

**Symptoms:** Container starts, but sudo fails, DNS doesn't resolve, SSH daemon misbehaves, or some other system behavior is broken.

**Recovery — read the change log first:**
```bash
docker compose exec agent cat /var/log/agent-changes.log | tail -50
```

**Recovery — override entrypoint and fix manually:**
```bash
docker compose run --entrypoint /bin/bash agent
# You're now in a root-accessible shell
# Fix the broken file:
nano /etc/sudoers         # or whatever was corrupted
# Verify the fix, then exit
exit
docker compose up -d
```

**Recovery — restore /etc from backup:**
```bash
docker compose down
docker run --rm \
  -v agent_container_agent_etc:/mnt/etc \
  -v /backups/agent-volumes/YYYY-MM-DD-HH-MM:/backup:ro \
  ubuntu:24.04 \
  tar xzf /backup/agent_etc.tar.gz -C /mnt/etc
docker compose up -d
```

**Nuclear option — wipe /etc volume entirely:**
```bash
docker compose down
docker volume rm agent_container_agent_etc
docker compose up -d
# /etc will be re-initialized from the clean image layer on first start
# All intentional /etc customizations are lost; must be re-applied
```

---

### 5.3 Scenario C: Container Will Not Start

**Symptoms:** `docker compose up` exits immediately. `docker compose ps` shows the container in a restart loop. The entrypoint itself may be broken, or a critical `/etc` file (like `/etc/passwd`) is malformed.

**Recovery — bypass the entrypoint entirely:**
```bash
docker compose run --entrypoint /bin/bash agent
# If this also fails, the image itself may be broken
# Move to the next step
```

**Recovery — use a rescue image with volumes attached:**
```bash
# Attach the broken volumes to a fresh, unrelated image for inspection
docker run -it --rm \
  -v agent_container_agent_etc:/mnt/etc \
  -v agent_container_agent_home:/mnt/home \
  -v agent_container_agent_local:/mnt/local \
  ubuntu:24.04 bash

# Inside the rescue shell:
cat /mnt/etc/passwd          # inspect for corruption
cat /mnt/home/agent/.backups/etc/passwd.* | tail -1   # check backup
# Repair or restore the file, then exit
exit

docker compose up -d
```

---

### 5.4 Scenario D: Cascading Volume Corruption

**Symptoms:** Multiple volumes are in an inconsistent state — e.g., a Python version conflict corrupted both `/usr/local/` and `/home/agent/.local/`, or a botched conda install broke `/opt/` in a way that prevents the agent runtime from loading.

**Recovery — identify scope from change log:**
```bash
# Start the rescue container (see 5.3)
cat /mnt/logs/agent-changes.log | grep -A2 -B2 "$(date +%Y-%m-%d)"
# Identify which volumes were touched and in what order
```

**Recovery — selective volume restore:**
```bash
docker compose down

# Restore only the affected volumes, leave others intact
for VOLUME in agent_local agent_opt; do
  docker run --rm \
    -v "agent_container_${VOLUME}:/target" \
    -v "/backups/agent-volumes/YYYY-MM-DD:/backup:ro" \
    ubuntu:24.04 \
    bash -c "cd /target && tar xzf /backup/${VOLUME}.tar.gz"
done

docker compose up -d
```

**Recovery — full restore from snapshot (last resort):**
```bash
docker compose down
/opt/agent/recovery/restore-all-volumes.sh YYYY-MM-DD-HH-MM
docker compose up -d
```

---

### 5.5 Scenario E: Agent Deleted Its Own Work

**Symptoms:** An agent deleted files from `/home/` that represent hours of work — scripts, data, configurations the agent had built up.

**Recovery from nightly backup:**
```bash
docker run --rm \
  -v agent_container_agent_home:/mnt/home \
  -v /backups/agent-volumes/YYYY-MM-DD:/backup:ro \
  ubuntu:24.04 \
  bash -c "cd /mnt/home && tar xzf /backup/agent_home.tar.gz ./agent/path/to/deleted/files"
```

**Note:** If the work was created after the last nightly backup and there is no pre-change snapshot, the work may be unrecoverable. This is the strongest argument for the agents themselves triggering snapshots before destructive operations (see Section 6.2).

---

## 6. Backup and Snapshot Strategy

### 6.1 Nightly Automated Backup (Host Cron)

Run on the **host machine**, not inside the container:

**`/opt/agent/backup-volumes.sh`:**
```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups/agent-volumes"
DATE=$(date +%Y-%m-%d-%H-%M)
VOLUMES="agent_home agent_local agent_opt agent_varlib agent_varcache agent_etc agent_logs"
PROJECT="agent_container"   # matches docker compose project name

mkdir -p "$BACKUP_DIR/$DATE"

for VOLUME in $VOLUMES; do
  echo "Backing up ${PROJECT}_${VOLUME}..."
  docker run --rm \
    -v "${PROJECT}_${VOLUME}:/source:ro" \
    -v "$BACKUP_DIR/$DATE:/backup" \
    ubuntu:24.04 \
    tar czf "/backup/${VOLUME}.tar.gz" -C /source .
  echo "  → Done: $(du -sh $BACKUP_DIR/$DATE/${VOLUME}.tar.gz | cut -f1)"
done

echo "Backup complete: $BACKUP_DIR/$DATE"
echo "$(date -u) | Nightly backup complete: $DATE" >> /var/log/agent-backup.log

# Retain 7 days of backups
find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;
```

**Host crontab:**
```cron
0 3 * * * /opt/agent/backup-volumes.sh >> /var/log/agent-backup.log 2>&1
```

### 6.2 Agent-Triggered Pre-Change Snapshots

The `/recovery/` directory is mounted read-only into the container (`./recovery:/recovery:ro`). Agents can invoke — but not modify — the snapshot script by calling a small shim:

**`/recovery/request-snapshot.sh` (host-side, invoked via docker exec):**
```bash
#!/bin/bash
LABEL=${1:-"agent-requested"}
/opt/agent/backup-volumes.sh
echo "$(date -u) | Pre-change snapshot: $LABEL" >> /var/log/agent-changes.log
```

Agents should be instructed to request a snapshot before:
- Any bulk deletion operation
- Any change to `/etc/`
- Installing or removing a runtime (Python, Node, conda)
- Any operation described as "clean up" or "reset"

The instruction in the system prompt:
```
Before any destructive or hard-to-reverse operation, write:
  echo "SNAPSHOT_REQUEST: <reason>" >> /var/log/agent-changes.log
The operator monitors this log and will trigger a snapshot.
```

(Fully automated agent-triggered snapshots require a host-side daemon watching that log, which can be added as an enhancement.)

### 6.3 Restore Script

**`/opt/agent/recovery/restore-volume.sh`:**
```bash
#!/bin/bash
VOLUME=$1
DATE=$2
PROJECT="agent_container"
BACKUP="/backups/agent-volumes/$DATE/${VOLUME}.tar.gz"

if [ ! -f "$BACKUP" ]; then
  echo "Error: backup not found at $BACKUP"; exit 1
fi

echo "Restoring ${PROJECT}_${VOLUME} from $DATE..."
docker compose down
docker run --rm \
  -v "${PROJECT}_${VOLUME}:/target" \
  -v "$(dirname $BACKUP):/backup:ro" \
  ubuntu:24.04 \
  bash -c "cd /target && tar xzf /backup/$(basename $BACKUP)"
docker compose up -d
echo "Done."
```

---

## 7. Implementation Files

### 7.1 Dockerfile

```dockerfile
FROM ubuntu:24.04

# Baked-in baseline — always available, always clean on restart
RUN apt-get update && apt-get install -y \
    curl wget git sudo python3 python3-pip pipx \
    vim nano htop jq ca-certificates gnupg && \
    rm -rf /var/lib/apt/lists/*

# Install micromamba for conda-compatible package management to /opt
RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
    | tar -xvj -C /usr/local bin/micromamba

# Create agent user with sudo access
RUN useradd -m -s /bin/bash agent && \
    echo "agent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir -p /home/agent/.backups/etc

# Bake in the manifest — read-only, world-readable
COPY container-manifest.md /container-manifest.md
RUN chmod 444 /container-manifest.md

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER agent
WORKDIR /home/agent
ENTRYPOINT ["/entrypoint.sh"]
```

### 7.2 docker-compose.yml

```yaml
services:
  agent:
    build: .
    container_name: agent_container
    env_file: .env
    volumes:
      - agent_home:/home/
      - agent_local:/usr/local/
      - agent_opt:/opt/
      - agent_varlib:/var/lib/
      - agent_varcache:/var/cache/
      - agent_etc:/etc/
      - agent_logs:/var/log/
      # Recovery tools: host-side scripts, read-only inside container
      - ./recovery:/recovery:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "test", "-f", "/var/log/agent-startup.log"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 30s

volumes:
  agent_home:
  agent_local:
  agent_opt:
  agent_varlib:
  agent_varcache:
  agent_etc:
  agent_logs:
```

### 7.3 entrypoint.sh

```bash
#!/bin/bash
set -e

echo "=== Agent Container Starting ==="
echo "  LLM_API_URL : ${LLM_API_URL}"
echo "  Timestamp   : $(date -u)"

# Make the manifest available in the environment for agents to inject
export CONTAINER_MANIFEST=$(cat /container-manifest.md)

# Ensure backup directory exists in persisted home
mkdir -p /home/agent/.backups/etc

# Persistent startup log
echo "$(date -u) | Container started | LLM_API_URL=${LLM_API_URL}" \
  >> /var/log/agent-startup.log

exec "$@"
```

---

## 8. Conclusions

### 8.1 The Volume Strategy is the Foundation

Every other component — agent awareness, recovery procedures, snapshots — depends on getting the volume strategy right. If a path the agents write to is not volume-mounted, no amount of agent instruction will prevent that work from being lost on restart. Validate the volume map before deploying agents, not after.

### 8.2 Ephemeral Corruption Is Self-Healing — Use This

When OpenClaw installs a tool to `/usr/bin`, when Pi's conda bootstrap writes to `/usr/lib`, when Hermes accidentally edits a system binary — a restart fixes it. This is the Docker image layer doing its job. Design the base image to contain everything the agents reliably need at startup, and treat agent-driven changes to ephemeral paths as inherently temporary. This reframe eliminates an entire class of "corruption" events that are in fact harmless.

### 8.3 `/etc` is the Real Danger Zone

All other corrupted paths either self-heal (ephemeral) or contain recoverable agent work (volumes). A corrupted `/etc` file is the one scenario that can make the container unbootable and requires operator intervention with Docker internals. OpenClaw, as the agent most likely to interact with system configuration, must treat every `/etc` modification as a high-risk operation with a mandatory pre-change backup. This should be baked into its system prompt as an absolute rule, not a guideline.

### 8.4 Agent Awareness Is Infrastructure, Not Documentation

The container manifest is not a README for humans. It is a structured context injection that every agent reads before taking its first action. It must be maintained with the same discipline as a configuration file: when the volume layout changes, the manifest changes. When a new agent is added, it inherits the manifest. If the manifest is out of date, the agents are operating on incorrect information, and corruption becomes more likely.

### 8.5 The Change Log is the Recovery Lifeline

In every scenario in Section 5, the first step after establishing shell access is reading `/var/log/agent-changes.log`. This log is only useful if agents write to it. It must be a standing behavioral requirement in all three agents' system prompts — not a suggestion. The log is the difference between a 10-minute recovery and a 2-hour investigation.

### 8.6 Snapshots Must Precede Major Operations

Nightly backups protect against ordinary data loss. They do not protect against an agent that destroys work between backups. Pre-change snapshots — triggered by the agents themselves before bulk deletions, runtime installs, or `/etc` modifications — are the gap-filler. The agent-triggered snapshot mechanism in Section 6.2 should be treated as mandatory, not optional.

### 8.7 Recovery Must Be Practiced Before It Is Needed

The five recovery scenarios in Section 5 require the operator to have a working mental model of Docker volumes, container override commands, and the project's naming conventions. This is not knowledge that comes naturally under pressure at 2 AM. Schedule a recovery drill on a copy of the container. Run Scenario C (unbootable container) in a test environment. Verify the restore script actually works. The runbook is only reliable if it has been tested.

### 8.8 Accept the Inevitable and Design for Speed of Recovery

No instruction set will make Hermes, OpenClaw, or Pi perfectly safe. They are capable agents with full system access, operating under novel conditions, solving problems the designers did not anticipate. Corruption will occur. The correct response is not to over-restrict the agents — restricted agents are less useful — but to minimize recovery time. With good volumes, a tested runbook, nightly backups, and a change log, most corruption events should be resolvable in under 15 minutes without data loss.

---

## 9. Implementation Notes & Deviations

During the actual implementation on the `010-agent-docker-setup` branch, the following deviations and design decisions were made to ensure a production-ready, clash-free, and robust deployment:

### 9.1 Multi-Stage Production Build
The production `Dockerfile` was upgraded to a multi-stage build:
1. **Stage 1 (web-builder)**: Uses `node:22-slim` to build the Vite frontend monorepo app (`apps/web`). This avoids polluting the final runtime image with web build-time tools.
2. **Stage 2 (Runtime)**: Sets up the lean `ubuntu:24.04` base, installs Python 3.13 via the deadsnakes PPA, Node.js 22, astral `uv`, and micromamba. The built static files from Stage 1 are copied into `/workspace/apps/web/dist` where the FastAPI backend serves them.

### 9.2 Resolving Ubuntu UID 1000 Clash
The official `ubuntu:24.04` Docker base image has a pre-created user named `ubuntu` with UID 1000. In order to create our `agent` user with UID 1000 (which is required to match the typical host user's UID and prevent SQLite/file write permission errors on bind-mounted/named volumes), the Dockerfile explicitly deletes the default user first:
```dockerfile
RUN userdel -r ubuntu && \
    useradd -m -u 1000 -s /bin/bash agent && \
    echo "agent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
```

### 9.3 Development Port & Host Isolation
To allow testing and debugging the Docker stack without stopping the active host development servers (running on ports `8000` and `5173`), the test container stack (`docker-compose.test.yml`) remaps host ports as follows:
- **API Server / Static Web**: Mapped to host port `8080` (container port `8000`)
- **Vite Dev Server (if run)**: Mapped to host port `5174` (container port `5173`)
This fully isolates development and test environments.

### 9.4 Named Volume Globals
All 7 named volumes are explicitly named globally to prevent Docker Compose from prefixing them with the folder/project name, ensuring clean host backup and restore scripting:
`wright_home`, `wright_local`, `wright_opt`, `wright_varlib`, `wright_varcache`, `wright_etc`, and `wright_logs`.

### 9.5 Scripts Directory Mounting
The recovery scripts directory on the host is named `scripts/` (not `recovery/`). Thus, in `docker-compose.test.yml`, the scripts are mounted to `/recovery` read-only via:
`- ./scripts:/recovery:ro`

---

*End of Document*

# Docker Deployment & Filesystem Map

Wright utilizes containerized execution environments to ensure consistent behavior, ease of installation, and secure isolation. To eliminate local dependency drift, the platform employs a **Thick Base / Thin Code** Docker architecture.

---

## The Ephemeral Filesystem

Docker images are built from stacked, read-only layers. When a container starts, Docker creates a thin **writable overlay layer** on top. Every file the container creates or modifies lives in this overlay. When the container stops and restarts (due to reboots, compose restarts, or crashes), that overlay is discarded, and the filesystem resets to the image state.

To prevent agent files and configurations from being erased, Wright mounts **named Docker volumes** over paths intended for persistence.

## Filesystem Map

All agents operating in the container adhere to this filesystem structure:

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
│   /recovery/      ← backup scripts, recovery tools                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Software Installation Guide for Agents

When installing new tools inside the agent container, follow this decision tree to ensure persistence:

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

## Named Volume Mapping

The Docker Compose setup maps seven named volumes:
*   `wright_home` -> `/home/`
*   `wright_local` -> `/usr/local/`
*   `wright_opt` -> `/opt/`
*   `wright_varlib` -> `/var/lib/`
*   `wright_varcache` -> `/var/cache/`
*   `wright_etc` -> `/etc/`
*   `wright_logs` -> `/var/log/`

## Container Manifest

A file `/container-manifest.md` is baked into the Docker image as a read-only, world-readable document. It provides the context configuration loaded by agents at startup to ensure they maintain awareness of the directory mapping rules.

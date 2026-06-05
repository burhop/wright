# Maintenance, Backups & Snapshots

To prevent data loss from accidental or agent-driven file deletions, Wright utilizes an automated backup and manual snapshot scheduling system.

---

## 1. Nightly Automated Backups (Host Cron)

Backups are executed on the **host machine** (not inside the container) using a scheduled cron job.

### Backup Script (`/opt/agent/backup-volumes.sh`)

```bash
#!/bin/bash
set -e

BACKUP_DIR="/backups/agent-volumes"
DATE=$(date +%Y-%m-%d-%H-%M)
VOLUMES="agent_home agent_local agent_opt agent_varlib agent_varcache agent_etc agent_logs"
PROJECT="wright"   # matches docker compose project/volume prefix

mkdir -p "$BACKUP_DIR/$DATE"

for VOLUME in $VOLUMES; do
  echo "Backing up ${PROJECT}_${VOLUME}..."
  docker run --rm \
    -v "${PROJECT}_${VOLUME}:/source:ro" \
    -v "$BACKUP_DIR/$DATE:/backup" \
    ubuntu:24.04 \
    tar czf "/backup/${VOLUME}.tar.gz" -C /source .
done

echo "Backup complete: $BACKUP_DIR/$DATE"
find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;
```

### Crontab Setup

To run backups nightly at 3:00 AM, add this entry to the host root crontab:
```cron
0 3 * * * /opt/agent/backup-volumes.sh >> /var/log/agent-backup.log 2>&1
```

---

## 2. Agent-Triggered Pre-Change Snapshots

The host scripts directory is mounted read-only to `/recovery/` inside the container. Agents can invoke a snapshot command before performing potentially dangerous operations.

### Requesting Snapshots

Agents are instructed to request a snapshot before:
*   Any bulk deletion or workspace reset
*   Modifying configuration files in `/etc/`
*   Installing or removing runtime dependencies (Python, Node, Conda)

Within their chat loop, agents write a log to `/var/log/agent-changes.log`:
```text
SNAPSHOT_REQUEST: Installing new CadQuery package
```

The operator or host-side monitoring daemon triggers the snapshot utility:
```bash
# /recovery/request-snapshot.sh <label>
/opt/agent/backup-volumes.sh
```

---

## 3. Restore Script (`/opt/agent/recovery/restore-volume.sh`)

To restore a specific named volume from a snapshot:

```bash
#!/bin/bash
VOLUME=$1
DATE=$2
PROJECT="wright"
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

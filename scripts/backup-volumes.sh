#!/bin/bash
set -e

# Define target backup directory
BACKUP_ROOT="/backups/wright-volumes"

# Check if /backups is writable, otherwise fallback to project root's backups directory
if [ ! -w "/backups" ] && [ ! -d "/backups" ]; then
  # Find repo root
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_ROOT="$(dirname "$SCRIPT_DIR")"
  BACKUP_ROOT="$REPO_ROOT/backups/wright-volumes"
  echo "Warning: /backups is not writable. Falling back to project root: $BACKUP_ROOT"
fi

DATE=$(date +%Y-%m-%d-%H-%M)
BACKUP_DIR="$BACKUP_ROOT/$DATE"

VOLUMES="wright_home wright_local wright_opt wright_varlib wright_varcache wright_etc wright_logs"

echo "=== Starting Wright Docker Volume Backup ==="
echo "Backup Destination: $BACKUP_DIR"
echo "Timestamp: $(date -u)"

mkdir -p "$BACKUP_DIR"

for VOLUME in $VOLUMES; do
  echo "Backing up volume: $VOLUME..."
  
  # Run a temporary container to archive the volume
  if docker run --rm \
    -v "$VOLUME:/source:ro" \
    -v "$BACKUP_DIR:/backup" \
    ubuntu:24.04 \
    tar czf "/backup/${VOLUME}.tar.gz" -C /source . ; then
    
    FILE_SIZE=$(du -sh "$BACKUP_DIR/${VOLUME}.tar.gz" | cut -f1)
    echo "  → Successfully backed up $VOLUME ($FILE_SIZE)"
  else
    echo "Error: Failed to back up volume $VOLUME" >&2
    exit 1
  fi
done

echo "Backup completed successfully."

# Retain 7 days of backups
echo "Pruning backups older than 7 days from $BACKUP_ROOT..."
if [ -d "$BACKUP_ROOT" ]; then
  find "$BACKUP_ROOT" -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;
fi
echo "Pruning complete."

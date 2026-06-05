#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ "$#" -ne 2 ]; then
  echo -e "${RED}Usage: $0 <volume_name> <backup_timestamp_or_date>${NC}"
  echo -e "${YELLOW}Example: $0 wright_home 2026-06-04-12-00${NC}"
  exit 1
fi

VOLUME="$1"
DATE="$2"

# Define backup root path
BACKUP_ROOT="/backups/wright-volumes"

# Fallback check
if [ ! -d "$BACKUP_ROOT" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  REPO_ROOT="$(dirname "$SCRIPT_DIR")"
  BACKUP_ROOT="$REPO_ROOT/backups/wright-volumes"
fi

BACKUP_FILE="$BACKUP_ROOT/$DATE/${VOLUME}.tar.gz"

if [ ! -f "$BACKUP_FILE" ]; then
  echo -e "${RED}Error: Backup file not found at $BACKUP_FILE${NC}"
  exit 1
fi

echo -e "${YELLOW}=== Starting Wright Volume Restore ===${NC}"
echo -e "Volume: $VOLUME"
echo -e "Backup Source: $BACKUP_FILE"

# Determine which compose file is in use or check if containers are running
COMPOSE_FILE="docker-compose.yml"
if docker compose -f docker-compose.test.yml ps | grep -q "wright_agent_test"; then
  COMPOSE_FILE="docker-compose.test.yml"
fi

echo -e "Stopping container stack ($COMPOSE_FILE) to prevent write conflicts..."
docker compose -f "$COMPOSE_FILE" down

echo -e "Restoring backup archive into volume $VOLUME..."
if docker run --rm \
  -v "$VOLUME:/target" \
  -v "$(dirname "$BACKUP_FILE"):/backup:ro" \
  ubuntu:24.04 \
  bash -c "cd /target && rm -rf ./* && tar xzf /backup/$(basename "$BACKUP_FILE")" ; then
  
  echo -e "${GREEN}✓ Successfully restored $VOLUME from $DATE backup.${NC}"
else
  echo -e "${RED}✗ Error: Failed to restore volume $VOLUME${NC}" >&2
  exit 1
fi

echo -e "Restarting container stack ($COMPOSE_FILE)..."
docker compose -f "$COMPOSE_FILE" up -d

echo -e "${GREEN}=== RESTORE COMPLETED ===${NC}"

#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.hackathon.yml}"
RESTART_TARGET="${RESTART_TARGET:-wright-api hermes-gateway}"
LOG_FILE="${LOG_FILE:-tmp/nous-hackathon-update.log}"

mkdir -p "$(dirname "$LOG_FILE")"
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) hackathon update start args=$* ===" | tee -a "$LOG_FILE"

if [[ "${1:-}" == "--rebuild" ]]; then
  docker compose -f "$COMPOSE_FILE" up -d --build 2>&1 | tee -a "$LOG_FILE"
  exit "${PIPESTATUS[0]}"
fi

if [[ "${1:-}" == "--restart-all" ]]; then
  RESTART_TARGET="all"
fi

docker compose -f "$COMPOSE_FILE" exec -T agent bash -lc "
set -e
cd /workspace
uv sync --python 3.13 --all-packages --all-groups
HERMES_PYTHON=\"\"
for candidate in /usr/local/lib/hermes-agent/venv/bin/python /usr/local/lib/hermes-agent/.venv/bin/python; do
  if [ -x \"\$candidate\" ]; then
    HERMES_PYTHON=\"\$candidate\"
    break
  fi
done
if [ -n \"\$HERMES_PYTHON\" ]; then
  uv pip install --python \"\$HERMES_PYTHON\" -e /workspace/hermes-plugin-wright
fi
supervisorctl -c /etc/supervisor/conf.d/wright-hackathon.conf restart ${RESTART_TARGET}
" 2>&1 | tee -a "$LOG_FILE"
exit "${PIPESTATUS[0]}"

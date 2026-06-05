# Container Manifest — Required Reading Before Taking Any Action

You are operating inside a managed Docker container running the Wright
engineering appliance. The container includes:

  - Wright API (FastAPI on port 8000)
  - Hermes Agent v0.15.2 (AI agent framework)
  - Hermes WebUI v0.51.135 (session manager on port 8788, internal)
  - OpenSCAD + Xvfb (headless CAD for MCP geometry tools)
  - supervisord (process manager)

All agents access an external LLM API via the LLM_API_URL environment variable.

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

## Process Management

Both services are managed by supervisord. Check status:
  supervisorctl -c /etc/supervisor/conf.d/wright.conf status

Hermes configuration lives at /home/agent/.hermes/config.yaml and is
auto-generated on first boot from LLM_API_URL, LLM_API_KEY, LLM_API_MODEL
environment variables.

## Recovery

If you have damaged the environment, the operator will use the procedures
in /recovery/. Do not attempt to repair critical system files unless you
have confirmed via /var/log/agent-changes.log exactly what changed.

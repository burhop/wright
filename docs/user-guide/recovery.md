# Recovery Runbook

When agents or operators corrupt files in the system, recovery scenarios can be initiated depending on which directory was affected. 

---

## Scenario A: Ephemeral Path Corruption

*   **Symptoms**: An agent installed a binary to `/usr/bin` or modified a library in `/usr/lib`. The tool works now but will be gone after a container restart, or the container is currently misbehaving due to system binary corruption.
*   **Self-healing**: Yes. These paths are in the image layer. A restart resets them.
*   **Recovery Action**:
    ```bash
    docker compose restart
    ```
    This resets all ephemeral paths. Check `/var/log/agent-changes.log` afterward.

---

## Scenario B: Broken `/etc` (Container Starts, Agents Fail)

*   **Symptoms**: Container starts, but `sudo` fails, DNS does not resolve, or other system utilities are broken due to corrupted configurations in `/etc/`.
*   **Recovery Action 1 (Inspect log first)**:
    ```bash
    docker compose exec agent cat /var/log/agent-changes.log | tail -50
    ```
*   **Recovery Action 2 (Override Entrypoint and Fix)**:
    ```bash
    docker compose run --entrypoint /bin/bash agent
    # Edit the broken file (e.g., nano /etc/sudoers)
    exit
    docker compose up -d
    ```
*   **Recovery Action 3 (Restore from Backup)**:
    ```bash
    docker compose down
    docker run --rm \
      -v wright_etc:/mnt/etc \
      -v /backups/agent-volumes/YYYY-MM-DD-HH-MM:/backup:ro \
      ubuntu:24.04 \
      tar xzf /backup/agent_etc.tar.gz -C /mnt/etc
    docker compose up -d
    ```
*   **Recovery Action 4 (Wipe `/etc` entirely — last resort)**:
    ```bash
    docker compose down
    docker volume rm wright_etc
    docker compose up -d
    ```
    The volume is re-initialized from the clean image layer on startup.

---

## Scenario C: Container Will Not Start

*   **Symptoms**: `docker compose up` exits immediately or loops in restart.
*   **Recovery Action 1 (Bypass Entrypoint)**:
    ```bash
    docker compose run --entrypoint /bin/bash agent
    ```
*   **Recovery Action 2 (Use Rescue Image with Volumes)**:
    ```bash
    docker run -it --rm \
      -v wright_etc:/mnt/etc \
      -v wright_home:/mnt/home \
      -v wright_local:/mnt/local \
      ubuntu:24.04 bash
    
    # Inside the rescue shell:
    cat /mnt/etc/passwd          # inspect for corruption
    exit
    docker compose up -d
    ```

---

## Scenario D: Cascading Volume Corruption

*   **Symptoms**: Multiple volumes are in an inconsistent state (e.g., Python packages conflicts in `/usr/local/` and `/home/agent/.local/`).
*   **Recovery Action**:
    ```bash
    docker compose down
    
    # Restore only the affected volumes
    for VOLUME in agent_local agent_opt; do
      docker run --rm \
        -v "wright_${VOLUME}:/target" \
        -v "/backups/agent-volumes/YYYY-MM-DD:/backup:ro" \
        ubuntu:24.04 \
        bash -c "cd /target && tar xzf /backup/${VOLUME}.tar.gz"
    done
    
    docker compose up -d
    ```

---

## Scenario E: Agent Deleted Its Own Work

*   **Symptoms**: An agent deleted files from `/home/` that represent active workspace progress.
*   **Recovery Action**:
    ```bash
    docker run --rm \
      -v wright_home:/mnt/home \
      -v /backups/agent-volumes/YYYY-MM-DD:/backup:ro \
      ubuntu:24.04 \
      bash -c "cd /mnt/home && tar xzf /backup/agent_home.tar.gz ./agent/path/to/deleted/files"
    ```

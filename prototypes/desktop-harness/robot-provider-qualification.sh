#!/usr/bin/env bash
# GB10 ARM64 qualification only; no installed-provider or desktop-workflow claim.
set -euo pipefail
state=${1:?Supply a new absolute /tmp evidence directory}
case "$state" in /tmp/wright-desktop-robot-provider-*) ;; *) exit 2 ;; esac
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
mkdir -m 700 "$state"
container=$(basename "$state")
image=sha256:6c5ebe4d1812e9bc4f6fc7d857a21ee2ad6488f63c0128dabc12fc9535d9b99f
# This is the already-built, qualified baseline image, not the installed command.
# Provider dependencies are added only to this container's private temporary area.
docker run --name "$container" --user "$(id -u):$(id -g)" \
  --read-only --cap-drop ALL --security-opt no-new-privileges \
  --memory 4g --cpus 2 --pids-limit 256 --tmpfs /tmp:rw,exec,nosuid,size=2g \
  --env UV_CACHE_DIR=/tmp/uv-cache --env UV_PYTHON_INSTALL_DIR=/tmp/uv-python \
  --env MPLCONFIGDIR=/tmp/matplotlib \
  --mount "type=bind,source=$repo,target=/repo,readonly" \
  --mount "type=bind,source=$state,target=/evidence" \
  --entrypoint /bin/sh "$image" -c '
    set -e
    uv venv --python 3.12 /tmp/robot-env
    uv pip install --python /tmp/robot-env/bin/python \
      rosbag-mcp==0.2.0 mcp==1.28.1 rosbags==0.11.5 \
      numpy==2.5.3 matplotlib==3.11.1 pillow==12.3.0
    uv pip freeze --python /tmp/robot-env/bin/python > /evidence/versions.txt
    /tmp/robot-env/bin/python /repo/scripts/qualify-robot-campaign.py \
      --execute --root /repo --output /evidence/provider-proof
  ' > "$state/container.log" 2>&1
# Keep the stopped container and evidence; never prune other sessions' state.

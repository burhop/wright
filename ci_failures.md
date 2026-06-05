# CI Failure Report
Generated automatically for local triage and AI code patching.

---

## 1. Docker Build CI (Run #27026177877)
- **Branch**: `dev`
- **Commit SHA**: `f61e79281e8cf68518308534a19e274d2e5fecb4`
- **Time**: 2026-06-05T16:12:16Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27026177877)

### Failed Log Output
```text
build-and-push	Run Smoke Test	﻿2026-06-05T16:14:35.0752095Z ##[group]Run set -euo pipefail
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0752454Z [36;1mset -euo pipefail[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0752696Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0753013Z [36;1mIMAGE="wright-agent:6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0753418Z [36;1mCONTAINER="wright-ci-smoke"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0753681Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0754169Z [36;1m# Start the container with a dummy LLM URL (no real LLM needed for smoke)[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0754615Z [36;1mdocker run --rm -d --name "$CONTAINER" \[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0754947Z [36;1m  -p 127.0.0.1:8090:8000 \[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0755376Z [36;1m  -e LLM_API_URL="https://ci-placeholder.example.com/v1" \[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0755753Z [36;1m  -e LLM_API_KEY="ci-test" \[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0756035Z [36;1m  -e LLM_API_MODEL="ci-model" \[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0756308Z [36;1m  "$IMAGE"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0756901Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0757183Z [36;1mcleanup() { docker rm -f "$CONTAINER" 2>/dev/null || true; }[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0757575Z [36;1mtrap cleanup EXIT[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0757812Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0758053Z [36;1m# Wait for Wright API health endpoint (up to 60s)[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0758410Z [36;1mecho "⏳ Waiting for Wright API..."[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0758713Z [36;1mfor i in $(seq 1 30); do[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0759110Z [36;1m  if curl -sf http://127.0.0.1:8090/api/health > /dev/null 2>&1; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0759508Z [36;1m    echo "✅ Wright API healthy"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0759776Z [36;1m    break[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0759991Z [36;1m  fi[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0760206Z [36;1m  if [ "$i" -eq 30 ]; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0760524Z [36;1m    echo "❌ Wright API did not become healthy in 60s"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0760917Z [36;1m    docker logs "$CONTAINER" 2>&1 | tail -50[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0761221Z [36;1m    exit 1[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0761431Z [36;1m  fi[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0761631Z [36;1m  sleep 2[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0761724Z [36;1mdone[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0761804Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0762024Z [36;1m# Verify Hermes WebUI is reachable via the agent health proxy (up to 30s)[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0762150Z [36;1mecho "⏳ Checking Hermes Agent proxy..."[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0762248Z [36;1mfor i in $(seq 1 15); do[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0762548Z [36;1m  AGENT_HEALTH=$(curl -sf http://127.0.0.1:8090/api/agent/health || echo '{"state":"disconnected"}')[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0762742Z [36;1m  AGENT_STATE=$(echo "$AGENT_HEALTH" | jq -r '.state // "unknown"')[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0762881Z [36;1m  echo "   Agent state attempt $i: $AGENT_STATE"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0763006Z [36;1m  if [ "$AGENT_STATE" = "connected" ]; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0763116Z [36;1m    echo "✅ Hermes Agent connected"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0763206Z [36;1m    break[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0763288Z [36;1m  fi[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0763380Z [36;1m  if [ "$i" -eq 15 ]; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0763548Z [36;1m    echo "❌ Hermes Agent not connected (state=$AGENT_STATE)"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0763675Z [36;1m    docker logs "$CONTAINER" 2>&1 | tail -50[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0763763Z [36;1m    exit 1[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0763847Z [36;1m  fi[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0763928Z [36;1m  sleep 2[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0764015Z [36;1mdone[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0764104Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0764183Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0764298Z [36;1m# Verify workspace creation works[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0764419Z [36;1mecho "⏳ Testing workspace creation..."[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0764638Z [36;1mWS_RESPONSE=$(curl -sf -X POST http://127.0.0.1:8090/api/workspace/create \[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0764765Z [36;1m  -H "Content-Type: application/json" \[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0764946Z [36;1m  -d '{"name":"CI Smoke Test","local_path":"/home/agent/workspace"}')[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0765118Z [36;1mWS_ID=$(echo "$WS_RESPONSE" | jq -r '.workspace_id // empty')[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0765216Z [36;1mif [ -z "$WS_ID" ]; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0765564Z [36;1m  echo "❌ Workspace creation failed: $WS_RESPONSE"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0765654Z [36;1m  exit 1[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0765740Z [36;1mfi[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0765854Z [36;1mecho "✅ Workspace created: $WS_ID"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0765938Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0766075Z [36;1m# Verify supervisord has both processes running[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0766326Z [36;1mecho "⏳ Checking supervisord processes..."[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0766908Z [36;1mPROCS=$(docker exec "$CONTAINER" supervisorctl -c /etc/supervisor/conf.d/wright.conf status 2>&1)[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0767006Z [36;1mecho "$PROCS"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0767169Z [36;1mif ! echo "$PROCS" | grep -q "wright-api.*RUNNING"; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0767283Z [36;1m  echo "❌ wright-api not RUNNING"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0767365Z [36;1m  exit 1[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0767448Z [36;1mfi[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0767604Z [36;1mif ! echo "$PROCS" | grep -q "hermes-webui.*RUNNING"; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0767730Z [36;1m  echo "❌ hermes-webui not RUNNING"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0767817Z [36;1m  exit 1[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0767894Z [36;1mfi[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0768004Z [36;1mecho "✅ All processes running"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0768088Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0768174Z [36;1mecho ""[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0768287Z [36;1mecho "🎉 Smoke test passed!"[0m
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0792681Z shell: /usr/bin/bash -e {0}
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0792766Z env:
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0793011Z   DOCKER_METADATA_OUTPUT_VERSION: sha-6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0793277Z   DOCKER_METADATA_OUTPUT_TAGS: /wright-agent:sha-6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0793491Z   DOCKER_METADATA_OUTPUT_TAG_NAMES: sha-6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0795285Z   DOCKER_METADATA_OUTPUT_LABELS: org.opencontainers.image.created=2026-06-05T16:12:32.749Z
build-and-push	Run Smoke Test	org.opencontainers.image.description=A digital engineer, designer, and mechanical analyst
build-and-push	Run Smoke Test	org.opencontainers.image.licenses=MIT
build-and-push	Run Smoke Test	org.opencontainers.image.revision=6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482
build-and-push	Run Smoke Test	org.opencontainers.image.source=https://github.com/burhop/wright
build-and-push	Run Smoke Test	org.opencontainers.image.title=wright
build-and-push	Run Smoke Test	org.opencontainers.image.url=https://github.com/burhop/wright
build-and-push	Run Smoke Test	org.opencontainers.image.version=sha-6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0797606Z   DOCKER_METADATA_OUTPUT_ANNOTATIONS: manifest:org.opencontainers.image.created=2026-06-05T16:12:32.749Z
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.description=A digital engineer, designer, and mechanical analyst
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.licenses=MIT
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.revision=6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.source=https://github.com/burhop/wright
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.title=wright
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.url=https://github.com/burhop/wright
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.version=sha-6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0802010Z   DOCKER_METADATA_OUTPUT_JSON: {"tags":["/wright-agent:sha-6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482"],"tag-names":["sha-6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482"],"labels":{"org.opencontainers.image.created":"2026-06-05T16:12:32.749Z","org.opencontainers.image.description":"A digital engineer, designer, and mechanical analyst","org.opencontainers.image.licenses":"MIT","org.opencontainers.image.revision":"6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482","org.opencontainers.image.source":"https://github.com/burhop/wright","org.opencontainers.image.title":"wright","org.opencontainers.image.url":"https://github.com/burhop/wright","org.opencontainers.image.version":"sha-6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482"},"annotations":["manifest:org.opencontainers.image.created=2026-06-05T16:12:32.749Z","manifest:org.opencontainers.image.description=A digital engineer, designer, and mechanical analyst","manifest:org.opencontainers.image.licenses=MIT","manifest:org.opencontainers.image.revision=6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482","manifest:org.opencontainers.image.source=https://github.com/burhop/wright","manifest:org.opencontainers.image.title=wright","manifest:org.opencontainers.image.url=https://github.com/burhop/wright","manifest:org.opencontainers.image.version=sha-6ba785a0f52f9046bca5ac7ad4d6e2c3f6962482"]}
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0802611Z   DOCKER_METADATA_OUTPUT_BAKE_FILE_TAGS: /home/runner/work/_temp/docker-actions-toolkit-uCsdXu/docker-metadata-action-bake-tags.json
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0803138Z   DOCKER_METADATA_OUTPUT_BAKE_FILE_LABELS: /home/runner/work/_temp/docker-actions-toolkit-uCsdXu/docker-metadata-action-bake-labels.json
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0803596Z   DOCKER_METADATA_OUTPUT_BAKE_FILE_ANNOTATIONS: /home/runner/work/_temp/docker-actions-toolkit-uCsdXu/docker-metadata-action-bake-annotations.json
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0803958Z   DOCKER_METADATA_OUTPUT_BAKE_FILE: /home/runner/work/_temp/docker-actions-toolkit-uCsdXu/docker-metadata-action-bake.json
build-and-push	Run Smoke Test	2026-06-05T16:14:35.0804044Z ##[endgroup]
build-and-push	Run Smoke Test	2026-06-05T16:14:35.1212013Z 19b428d79503e4e14c065fef6c19362a788c86195f7118cbf05f4f61dae991f1
build-and-push	Run Smoke Test	2026-06-05T16:14:35.2992368Z ⏳ Waiting for Wright API...
build-and-push	Run Smoke Test	2026-06-05T16:14:39.3691733Z ✅ Wright API healthy
build-and-push	Run Smoke Test	2026-06-05T16:14:39.3692884Z ⏳ Checking Hermes Agent proxy...
build-and-push	Run Smoke Test	2026-06-05T16:14:39.4767746Z    Agent state attempt 1: connected
build-and-push	Run Smoke Test	2026-06-05T16:14:39.4769043Z ✅ Hermes Agent connected
build-and-push	Run Smoke Test	2026-06-05T16:14:39.4769776Z ⏳ Testing workspace creation...
build-and-push	Run Smoke Test	2026-06-05T16:14:39.7941753Z wright-ci-smoke
build-and-push	Run Smoke Test	2026-06-05T16:14:39.7975597Z ##[error]Process completed with exit code 22.
```

---

## 2. Docker Build CI (Run #27025715246)
- **Branch**: `dev`
- **Commit SHA**: `94c524c9c5e20eb699c4ba883394bb02ceeee50e`
- **Time**: 2026-06-05T16:03:09Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27025715246)

### Failed Log Output
```text
build-and-push	Run Smoke Test	﻿2026-06-05T16:09:53.6136157Z ##[group]Run set -euo pipefail
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6136507Z [36;1mset -euo pipefail[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6136741Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6137048Z [36;1mIMAGE="wright-agent:2653d6f38aedd398ba129b2c5266519913828e18"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6137438Z [36;1mCONTAINER="wright-ci-smoke"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6137693Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6138348Z [36;1m# Start the container with a dummy LLM URL (no real LLM needed for smoke)[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6138809Z [36;1mdocker run --rm -d --name "$CONTAINER" \[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6139122Z [36;1m  -p 127.0.0.1:8090:8000 \[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6139474Z [36;1m  -e LLM_API_URL="https://ci-placeholder.example.com/v1" \[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6139863Z [36;1m  -e LLM_API_KEY="ci-test" \[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6140150Z [36;1m  -e LLM_API_MODEL="ci-model" \[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6140423Z [36;1m  "$IMAGE"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6140627Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6140899Z [36;1mcleanup() { docker rm -f "$CONTAINER" 2>/dev/null || true; }[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6141299Z [36;1mtrap cleanup EXIT[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6141536Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6141937Z [36;1m# Wait for Wright API health endpoint (up to 60s)[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6142292Z [36;1mecho "⏳ Waiting for Wright API..."[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6142583Z [36;1mfor i in $(seq 1 30); do[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6142946Z [36;1m  if curl -sf http://127.0.0.1:8090/api/health > /dev/null 2>&1; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6143333Z [36;1m    echo "✅ Wright API healthy"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6143599Z [36;1m    break[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6143803Z [36;1m  fi[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6144001Z [36;1m  if [ "$i" -eq 30 ]; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6144321Z [36;1m    echo "❌ Wright API did not become healthy in 60s"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6144703Z [36;1m    docker logs "$CONTAINER" 2>&1 | tail -50[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6145008Z [36;1m    exit 1[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6145207Z [36;1m  fi[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6145400Z [36;1m  sleep 2[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6145613Z [36;1mdone[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6145691Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6145865Z [36;1m# Verify Hermes WebUI is reachable via the agent health proxy[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6145997Z [36;1mecho "⏳ Checking Hermes Agent proxy..."[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6146225Z [36;1mAGENT_HEALTH=$(curl -sf http://127.0.0.1:8090/api/agent/health || echo '{}')[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6146409Z [36;1mAGENT_STATE=$(echo "$AGENT_HEALTH" | jq -r '.state // "unknown"')[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6146517Z [36;1mecho "   Agent state: $AGENT_STATE"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6146637Z [36;1mif [ "$AGENT_STATE" != "connected" ]; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6146796Z [36;1m  echo "❌ Hermes Agent not connected (state=$AGENT_STATE)"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6146918Z [36;1m  docker logs "$CONTAINER" 2>&1 | tail -50[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6146999Z [36;1m  exit 1[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6147071Z [36;1mfi[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6147173Z [36;1mecho "✅ Hermes Agent connected"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6147246Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6147360Z [36;1m# Verify workspace creation works[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6147480Z [36;1mecho "⏳ Testing workspace creation..."[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6147703Z [36;1mWS_RESPONSE=$(curl -sf -X POST http://127.0.0.1:8090/api/workspace/create \[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6147827Z [36;1m  -H "Content-Type: application/json" \[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6148346Z [36;1m  -d '{"name":"CI Smoke Test","local_path":"/home/agent/workspace"}')[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6148530Z [36;1mWS_ID=$(echo "$WS_RESPONSE" | jq -r '.workspace_id // empty')[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6148623Z [36;1mif [ -z "$WS_ID" ]; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6148775Z [36;1m  echo "❌ Workspace creation failed: $WS_RESPONSE"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6148854Z [36;1m  exit 1[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6148931Z [36;1mfi[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6149037Z [36;1mecho "✅ Workspace created: $WS_ID"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6149114Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6149258Z [36;1m# Verify supervisord has both processes running[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6149576Z [36;1mecho "⏳ Checking supervisord processes..."[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6149891Z [36;1mPROCS=$(docker exec "$CONTAINER" supervisorctl -c /etc/supervisor/conf.d/wright.conf status 2>&1)[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6149989Z [36;1mecho "$PROCS"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6150145Z [36;1mif ! echo "$PROCS" | grep -q "wright-api.*RUNNING"; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6150253Z [36;1m  echo "❌ wright-api not RUNNING"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6150328Z [36;1m  exit 1[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6150408Z [36;1mfi[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6150566Z [36;1mif ! echo "$PROCS" | grep -q "hermes-webui.*RUNNING"; then[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6150674Z [36;1m  echo "❌ hermes-webui not RUNNING"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6150753Z [36;1m  exit 1[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6150830Z [36;1mfi[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6150928Z [36;1mecho "✅ All processes running"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6151006Z [36;1m[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6151082Z [36;1mecho ""[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6151181Z [36;1mecho "🎉 Smoke test passed!"[0m
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6174235Z shell: /usr/bin/bash -e {0}
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6174314Z env:
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6174548Z   DOCKER_METADATA_OUTPUT_VERSION: sha-2653d6f38aedd398ba129b2c5266519913828e18
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6174941Z   DOCKER_METADATA_OUTPUT_TAGS: /wright-agent:sha-2653d6f38aedd398ba129b2c5266519913828e18
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6175152Z   DOCKER_METADATA_OUTPUT_TAG_NAMES: sha-2653d6f38aedd398ba129b2c5266519913828e18
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6177029Z   DOCKER_METADATA_OUTPUT_LABELS: org.opencontainers.image.created=2026-06-05T16:03:28.349Z
build-and-push	Run Smoke Test	org.opencontainers.image.description=A digital engineer, designer, and mechanical analyst
build-and-push	Run Smoke Test	org.opencontainers.image.licenses=MIT
build-and-push	Run Smoke Test	org.opencontainers.image.revision=2653d6f38aedd398ba129b2c5266519913828e18
build-and-push	Run Smoke Test	org.opencontainers.image.source=https://github.com/burhop/wright
build-and-push	Run Smoke Test	org.opencontainers.image.title=wright
build-and-push	Run Smoke Test	org.opencontainers.image.url=https://github.com/burhop/wright
build-and-push	Run Smoke Test	org.opencontainers.image.version=sha-2653d6f38aedd398ba129b2c5266519913828e18
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6179454Z   DOCKER_METADATA_OUTPUT_ANNOTATIONS: manifest:org.opencontainers.image.created=2026-06-05T16:03:28.349Z
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.description=A digital engineer, designer, and mechanical analyst
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.licenses=MIT
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.revision=2653d6f38aedd398ba129b2c5266519913828e18
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.source=https://github.com/burhop/wright
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.title=wright
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.url=https://github.com/burhop/wright
build-and-push	Run Smoke Test	manifest:org.opencontainers.image.version=sha-2653d6f38aedd398ba129b2c5266519913828e18
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6184045Z   DOCKER_METADATA_OUTPUT_JSON: {"tags":["/wright-agent:sha-2653d6f38aedd398ba129b2c5266519913828e18"],"tag-names":["sha-2653d6f38aedd398ba129b2c5266519913828e18"],"labels":{"org.opencontainers.image.created":"2026-06-05T16:03:28.349Z","org.opencontainers.image.description":"A digital engineer, designer, and mechanical analyst","org.opencontainers.image.licenses":"MIT","org.opencontainers.image.revision":"2653d6f38aedd398ba129b2c5266519913828e18","org.opencontainers.image.source":"https://github.com/burhop/wright","org.opencontainers.image.title":"wright","org.opencontainers.image.url":"https://github.com/burhop/wright","org.opencontainers.image.version":"sha-2653d6f38aedd398ba129b2c5266519913828e18"},"annotations":["manifest:org.opencontainers.image.created=2026-06-05T16:03:28.349Z","manifest:org.opencontainers.image.description=A digital engineer, designer, and mechanical analyst","manifest:org.opencontainers.image.licenses=MIT","manifest:org.opencontainers.image.revision=2653d6f38aedd398ba129b2c5266519913828e18","manifest:org.opencontainers.image.source=https://github.com/burhop/wright","manifest:org.opencontainers.image.title=wright","manifest:org.opencontainers.image.url=https://github.com/burhop/wright","manifest:org.opencontainers.image.version=sha-2653d6f38aedd398ba129b2c5266519913828e18"]}
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6184490Z   DOCKER_METADATA_OUTPUT_BAKE_FILE_TAGS: /home/runner/work/_temp/docker-actions-toolkit-d3qNX3/docker-metadata-action-bake-tags.json
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6185064Z   DOCKER_METADATA_OUTPUT_BAKE_FILE_LABELS: /home/runner/work/_temp/docker-actions-toolkit-d3qNX3/docker-metadata-action-bake-labels.json
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6185543Z   DOCKER_METADATA_OUTPUT_BAKE_FILE_ANNOTATIONS: /home/runner/work/_temp/docker-actions-toolkit-d3qNX3/docker-metadata-action-bake-annotations.json
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6185918Z   DOCKER_METADATA_OUTPUT_BAKE_FILE: /home/runner/work/_temp/docker-actions-toolkit-d3qNX3/docker-metadata-action-bake.json
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6185996Z ##[endgroup]
build-and-push	Run Smoke Test	2026-06-05T16:09:53.6665976Z 71e0a9b46da025000d6f9d7f23144d53e5290a978c02a25ddd47c41e6cc8f294
build-and-push	Run Smoke Test	2026-06-05T16:09:53.8571865Z ⏳ Waiting for Wright API...
build-and-push	Run Smoke Test	2026-06-05T16:09:57.9310146Z ✅ Wright API healthy
build-and-push	Run Smoke Test	2026-06-05T16:09:57.9329198Z ⏳ Checking Hermes Agent proxy...
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0488469Z    Agent state: disconnected
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0498623Z ❌ Hermes Agent not connected (state=disconnected)
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0632916Z === Agent Container Starting ===
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0637694Z   LLM_API_URL : https://ci-placeholder.example.com/v1
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0639265Z   Timestamp   : Fri Jun  5 16:09:53 UTC 2026
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0640068Z First boot: initializing Hermes Agent...
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0640996Z Hermes bootstrapped with LLM endpoint: https://ci-placeholder.example.com/v1
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0641963Z === Starting services ===
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0642801Z 2026-06-05 16:09:54,089 INFO RPC interface 'supervisor' initialized
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0643967Z 2026-06-05 16:09:54,089 CRIT Server 'unix_http_server' running without any HTTP authentication checking
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0645139Z 2026-06-05 16:09:54,089 INFO supervisord started with pid 1
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0646162Z 2026-06-05 16:09:55,092 INFO spawned: 'hermes-webui' with pid 18
build-and-push	Run Smoke Test	2026-06-05T16:09:58.0647179Z 2026-06-05 16:09:55,096 INFO spawned: 'wright-api' with pid 19
build-and-push	Run Smoke Test	2026-06-05T16:09:58.3140250Z wright-ci-smoke
build-and-push	Run Smoke Test	2026-06-05T16:09:58.3185810Z ##[error]Process completed with exit code 1.
```

---

## 3. python-quality (Run #27025470042)
- **Branch**: `dev`
- **Commit SHA**: `2ceded12d1146c23d62b4b8c7c6aeb3d831bb82f`
- **Time**: 2026-06-05T15:58:30Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27025470042)

### Failed Log Output
```text
python-quality	Run Tests with pytest	﻿2026-06-05T15:58:53.4659353Z ##[group]Run uv run pytest
python-quality	Run Tests with pytest	2026-06-05T15:58:53.4659667Z [36;1muv run pytest[0m
python-quality	Run Tests with pytest	2026-06-05T15:58:53.4686021Z shell: /usr/bin/bash -e {0}
python-quality	Run Tests with pytest	2026-06-05T15:58:53.4686289Z env:
python-quality	Run Tests with pytest	2026-06-05T15:58:53.4686552Z   UV_CACHE_DIR: /home/runner/work/_temp/setup-uv-cache
python-quality	Run Tests with pytest	2026-06-05T15:58:53.4687147Z   pythonLocation: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:58:53.4687612Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib/pkgconfig
python-quality	Run Tests with pytest	2026-06-05T15:58:53.4688058Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:58:53.4688468Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:58:53.4688876Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:58:53.4689291Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib
python-quality	Run Tests with pytest	2026-06-05T15:58:53.4689635Z ##[endgroup]
python-quality	Run Tests with pytest	2026-06-05T15:58:55.9396359Z ============================= test session starts ==============================
python-quality	Run Tests with pytest	2026-06-05T15:58:55.9397585Z platform linux -- Python 3.13.13, pytest-9.0.3, pluggy-1.6.0
python-quality	Run Tests with pytest	2026-06-05T15:58:55.9398928Z rootdir: /home/runner/work/wright/wright
python-quality	Run Tests with pytest	2026-06-05T15:58:55.9404556Z configfile: pyproject.toml
python-quality	Run Tests with pytest	2026-06-05T15:58:55.9405312Z plugins: asyncio-1.4.0, anyio-4.13.0
python-quality	Run Tests with pytest	2026-06-05T15:58:55.9406505Z asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
python-quality	Run Tests with pytest	2026-06-05T15:58:55.9407719Z collected 45 items
python-quality	Run Tests with pytest	2026-06-05T15:58:55.9408146Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:56.2150778Z apps/api/tests/test_hermes_adapter.py ........                           [ 17%]
python-quality	Run Tests with pytest	2026-06-05T15:58:56.4496633Z apps/api/tests/test_mcp_api.py .............                             [ 46%]
python-quality	Run Tests with pytest	2026-06-05T15:58:56.5291918Z apps/api/tests/test_webmcp.py ..                                         [ 51%]
python-quality	Run Tests with pytest	2026-06-05T15:58:57.3419381Z apps/api/tests/test_workspace_api.py .......FFF........                  [ 91%]
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4478582Z packages/tool_registry/tests/test_registry.py ....                       [100%]
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4479612Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4480651Z =================================== FAILURES ===================================
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4481799Z __________________________ test_git_status_and_commit __________________________
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4482561Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4483162Z client = <starlette.testclient.TestClient object at 0x7fd359d039b0>
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4483909Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4484314Z     def test_git_status_and_commit(client):
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4485114Z         # Add a file first (will be untracked 'U')
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4485888Z         client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4486526Z             "/api/workspace/files",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4487432Z             json={"session_id": "test-session", "path": "/untracked.txt", "type": "file"},
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4488402Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4488940Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4489478Z         # Check Git Status
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4490110Z         response = client.get(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4491300Z             "/api/workspace/git/status", params={"session_id": "test-session"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4492222Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4492842Z         assert response.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4493620Z         data = response.json()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4494340Z         assert "branch_name" in data
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4495103Z         assert len(data["changes"]) > 0
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4495803Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4496380Z         # Commit changes
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4497066Z         response_commit = client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4497841Z             "/api/workspace/git/commit",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4498764Z             json={"session_id": "test-session", "message": "feat: test git commit"},
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4499654Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4500194Z >       assert response_commit.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4501191Z E       assert 500 == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4501874Z E        +  where 500 = <Response [500 Internal Server Error]>.status_code
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4502493Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4502935Z apps/api/tests/test_workspace_api.py:272: AssertionError
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4504127Z ----------------------------- Captured stdout call -----------------------------
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4505527Z {"event": "Initialized local Git repository in workspace /tmp/tmp5__y0a73", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:56.681537Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4507506Z {"event": "Created default .gitignore in /tmp/tmp5__y0a73/.gitignore", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:56.681698Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4509515Z {"event": "Failed to commit changes: Command '['git', 'commit', '-m', 'feat: test git commit']' returned non-zero exit status 128.", "level": "error", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:56.700186Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4511551Z ___________________________ test_git_diff_and_revert ___________________________
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4512162Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4512617Z self = <core.workspace.WorkspaceManager object at 0x7fd359df17b0>
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4513366Z rel_path = '/diff_test.txt'
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4513769Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4514108Z     def revert_file(self, rel_path: str) -> None:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4514858Z         """Revert a file back to HEAD state or delete if untracked."""
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4515623Z         abs_path = self.sanitize_path(rel_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4516259Z         is_untracked = False
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4516773Z         try:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4517604Z             res_status = subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4518259Z                 ["git", "status", "--porcelain", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4518890Z                 cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4519442Z                 capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4520012Z                 text=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4520748Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4521281Z             if res_status.stdout.startswith("??"):
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4521919Z                 is_untracked = True
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4522473Z         except Exception:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4522998Z             pass
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4523444Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4523884Z         if is_untracked:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4524416Z             if os.path.isdir(abs_path):
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4524985Z                 import shutil
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4525500Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4525941Z                 shutil.rmtree(abs_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4526530Z             elif os.path.exists(abs_path):
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4527114Z                 os.remove(abs_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4527655Z         else:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4528099Z             try:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4528737Z                 subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4529379Z                     ["git", "reset", "HEAD", "--", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4530008Z                     cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4530785Z                     capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4531333Z                 )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4531815Z >               subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4532411Z                     ["git", "checkout", "HEAD", "--", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4533051Z                     cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4533623Z                     capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4534175Z                     check=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4534676Z                 )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4535006Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4535343Z packages/core/src/core/workspace.py:770: 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4536025Z _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4536572Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4536974Z input = None, capture_output = True, timeout = None, check = True
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4537853Z popenargs = (['git', 'checkout', 'HEAD', '--', '/tmp/tmp21etbo73/diff_test.txt'],)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4538726Z kwargs = {'cwd': '/tmp/tmp21etbo73', 'stderr': -1, 'stdout': -1}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4539621Z process = <Popen: returncode: 128 args: ['git', 'checkout', 'HEAD', '--', '/tmp/tmp21e...>
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4540767Z stdout = b'', stderr = b'fatal: invalid reference: HEAD\n', retcode = 128
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4541657Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4541964Z     def run(*popenargs,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4542663Z             input=None, capture_output=False, timeout=None, check=False, **kwargs):
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4543807Z         """Run command with arguments and return a CompletedProcess instance.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4544547Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4545197Z         The returned instance will have attributes args, returncode, stdout and
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4546212Z         stderr. By default, stdout and stderr are not captured, and those attributes
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4547166Z         will be None. Pass stdout=PIPE and/or stderr=PIPE in order to capture them,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4548000Z         or pass capture_output=True to capture both.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4548604Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4549153Z         If check is True and the exit code was non-zero, it raises a
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4550048Z         CalledProcessError. The CalledProcessError object will have the return code
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4551263Z         in the returncode attribute, and output & stderr attributes if those streams
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4552056Z         were captured.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4552538Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4553113Z         If timeout (seconds) is given and the process takes too long,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4553861Z          a TimeoutExpired exception will be raised.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4554444Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4554961Z         There is an optional argument "input", allowing you to
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4555767Z         pass bytes or a string to the subprocess's stdin.  If you use this argument
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4556673Z         you may not also use the Popen constructor's "stdin" argument, as
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4557418Z         it will be used internally.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4557965Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4558584Z         By default, all communication is in bytes, and therefore any "input" should
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4559483Z         be bytes, and the stdout and stderr will be bytes. If in text mode, any
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4560591Z         "input" should be a string, and stdout and stderr will be strings decoded
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4561510Z         according to locale encoding, or by "encoding" if set. Text mode is
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4562420Z         triggered by setting any of text, encoding, errors or universal_newlines.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4563154Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4563708Z         The other arguments are the same as for the Popen constructor.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4564388Z         """
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4564866Z         if input is not None:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4565445Z             if kwargs.get('stdin') is not None:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4566251Z                 raise ValueError('stdin and input arguments may not both be used.')
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4567039Z             kwargs['stdin'] = PIPE
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4567576Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4568035Z         if capture_output:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4568733Z             if kwargs.get('stdout') is not None or kwargs.get('stderr') is not None:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4569696Z                 raise ValueError('stdout and stderr arguments may not be used '
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4570725Z                                  'with capture_output.')
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4571490Z             kwargs['stdout'] = PIPE
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4572050Z             kwargs['stderr'] = PIPE
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4572554Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4573042Z         with Popen(*popenargs, **kwargs) as process:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4573662Z             try:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4574432Z                 stdout, stderr = process.communicate(input, timeout=timeout)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4575162Z             except TimeoutExpired as exc:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4575720Z                 process.kill()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4576235Z                 if _mswindows:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4576812Z                     # Windows accumulates the output in a single blocking
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4577631Z                     # read() call run on child threads, with the timeout
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4578622Z                     # being done in a join() on those threads.  communicate()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4579406Z                     # _after_ kill() is required to collect that and add it
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4580691Z                     # to the exception.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4581325Z                     exc.stdout, exc.stderr = process.communicate()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4581951Z                 else:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4582506Z                     # POSIX _communicate already populated the output so
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4583206Z                     # far into the TimeoutExpired exception.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4583789Z                     process.wait()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4584284Z                 raise
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4584883Z             except:  # Including KeyboardInterrupt, communicate handled that.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4585580Z                 process.kill()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4586180Z                 # We don't call process.wait() as .__exit__ does that for us.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4586836Z                 raise
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4587292Z             retcode = process.poll()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4587818Z             if check and retcode:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4588397Z >               raise CalledProcessError(retcode, process.args,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4589094Z                                          output=stdout, stderr=stderr)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4590436Z E               subprocess.CalledProcessError: Command '['git', 'checkout', 'HEAD', '--', '/tmp/tmp21etbo73/diff_test.txt']' returned non-zero exit status 128.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4591446Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4591983Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/subprocess.py:577: CalledProcessError
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4592662Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4593064Z The above exception was the direct cause of the following exception:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4593612Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4594011Z client = <starlette.testclient.TestClient object at 0x7fd359d03790>
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4594569Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4594842Z     def test_git_diff_and_revert(client):
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4595401Z         # Setup - Create file and commit it
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4595953Z         client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4596426Z             "/api/workspace/files",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4597143Z             json={"session_id": "test-session", "path": "/diff_test.txt", "type": "file"},
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4597863Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4598277Z         client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4598783Z             "/api/workspace/git/commit",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4599452Z             json={"session_id": "test-session", "message": "initial commit"},
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4600120Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4600710Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4601267Z         # Modify file content manually on disk by resolving its path
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4601994Z         from api.config import DATABASE_PATH
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4602712Z         from core.workspace import get_workspace_by_session
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4603366Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4604035Z         workspace = get_workspace_by_session(DATABASE_PATH, "test-session")
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4604911Z         file_path = os.path.join(workspace["local_path"], "diff_test.txt")
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4605608Z         with open(file_path, "w") as f:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4606183Z             f.write("modified content here")
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4606715Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4607112Z         # Get Diff
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4607569Z         response_diff = client.get(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4608146Z             "/api/workspace/git/diff",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4608807Z             params={"session_id": "test-session", "path": "/diff_test.txt"},
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4609477Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4609926Z         assert response_diff.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4610866Z         assert "diff" in response_diff.json()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4611442Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4611915Z         # Revert
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4612346Z >       response_revert = client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4612881Z             "/api/workspace/git/revert",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4614096Z             json={"session_id": "test-session", "path": "/diff_test.txt"},
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4614739Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4614995Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4615265Z apps/api/tests/test_workspace_api.py:312: 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4616079Z _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4616899Z .venv/lib/python3.13/site-packages/starlette/testclient.py:560: in post
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4617595Z     return super().post(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4618194Z .venv/lib/python3.13/site-packages/httpx/_client.py:1144: in post
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4618860Z     return self.request(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4619491Z .venv/lib/python3.13/site-packages/starlette/testclient.py:459: in request
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4620184Z     return super().request(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4621030Z .venv/lib/python3.13/site-packages/httpx/_client.py:825: in request
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4621859Z     return self.send(request, auth=auth, follow_redirects=follow_redirects)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4622599Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4623288Z .venv/lib/python3.13/site-packages/httpx/_client.py:914: in send
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4623958Z     response = self._send_handling_auth(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4624677Z .venv/lib/python3.13/site-packages/httpx/_client.py:942: in _send_handling_auth
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4625462Z     response = self._send_handling_redirects(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4626233Z .venv/lib/python3.13/site-packages/httpx/_client.py:979: in _send_handling_redirects
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4627047Z     response = self._send_single_request(request)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4627616Z                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4628337Z .venv/lib/python3.13/site-packages/httpx/_client.py:1014: in _send_single_request
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4629135Z     response = transport.handle_request(request)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4629706Z                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4630633Z .venv/lib/python3.13/site-packages/starlette/testclient.py:362: in handle_request
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4631405Z     raise exc
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4632026Z .venv/lib/python3.13/site-packages/starlette/testclient.py:359: in handle_request
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4632840Z     portal.call(self.app, scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4633546Z .venv/lib/python3.13/site-packages/anyio/from_thread.py:334: in call
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4634358Z     return cast(T_Retval, self.start_task_soon(func, *args).result())
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4635038Z                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4635880Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/concurrent/futures/_base.py:456: in result
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4636742Z     return self.__get_result()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4637210Z            ^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4637995Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/concurrent/futures/_base.py:401: in __get_result
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4638867Z     raise self._exception
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4639472Z .venv/lib/python3.13/site-packages/anyio/from_thread.py:259: in _call_func
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4640154Z     retval = await retval_or_awaitable
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4640848Z              ^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4641521Z .venv/lib/python3.13/site-packages/fastapi/applications.py:1159: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4642246Z     await super().__call__(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4642968Z .venv/lib/python3.13/site-packages/starlette/applications.py:90: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4643725Z     await self.middleware_stack(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4644483Z .venv/lib/python3.13/site-packages/starlette/middleware/errors.py:186: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4645197Z     raise exc
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4645789Z .venv/lib/python3.13/site-packages/starlette/middleware/errors.py:164: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4646548Z     await self.app(scope, receive, _send)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4647274Z .venv/lib/python3.13/site-packages/starlette/middleware/base.py:191: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4648330Z     with recv_stream, send_stream, collapse_excgroups():
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4648960Z                                    ^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4649935Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/contextlib.py:162: in __exit__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4650953Z     self.gen.throw(value)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4651639Z .venv/lib/python3.13/site-packages/starlette/_utils.py:87: in collapse_excgroups
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4652369Z     raise exc
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4653007Z .venv/lib/python3.13/site-packages/starlette/middleware/base.py:193: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4653857Z     response = await self.dispatch_func(request, call_next)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4654503Z                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4655137Z apps/api/src/api/middleware/tracing.py:119: in dispatch
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4655747Z     response = await call_next(request)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4656276Z                ^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4657067Z .venv/lib/python3.13/site-packages/starlette/middleware/base.py:168: in call_next
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4657926Z     raise app_exc from app_exc.__cause__ or app_exc.__context__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4658751Z .venv/lib/python3.13/site-packages/starlette/middleware/base.py:144: in coro
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4659598Z     await self.app(scope, receive_or_disconnect, send_no_error)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4660643Z .venv/lib/python3.13/site-packages/starlette/middleware/cors.py:88: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4661463Z     await self.app(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4662269Z .venv/lib/python3.13/site-packages/starlette/middleware/exceptions.py:63: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4663239Z     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4664188Z .venv/lib/python3.13/site-packages/starlette/_exception_handler.py:53: in wrapped_app
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4664951Z     raise exc
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4665599Z .venv/lib/python3.13/site-packages/starlette/_exception_handler.py:42: in wrapped_app
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4666379Z     await app(scope, receive, sender)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4667156Z .venv/lib/python3.13/site-packages/fastapi/middleware/asyncexitstack.py:18: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4667994Z     await self.app(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4668696Z .venv/lib/python3.13/site-packages/starlette/routing.py:660: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4669494Z     await self.middleware_stack(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4670399Z .venv/lib/python3.13/site-packages/starlette/routing.py:680: in app
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4671155Z     await route.handle(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4671894Z .venv/lib/python3.13/site-packages/starlette/routing.py:276: in handle
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4672604Z     await self.app(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4673270Z .venv/lib/python3.13/site-packages/fastapi/routing.py:134: in app
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4674081Z     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4675027Z .venv/lib/python3.13/site-packages/starlette/_exception_handler.py:53: in wrapped_app
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4675796Z     raise exc
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4676436Z .venv/lib/python3.13/site-packages/starlette/_exception_handler.py:42: in wrapped_app
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4677241Z     await app(scope, receive, sender)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4677889Z .venv/lib/python3.13/site-packages/fastapi/routing.py:120: in app
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4678579Z     response = await f(request)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4679055Z                ^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4679628Z .venv/lib/python3.13/site-packages/fastapi/routing.py:674: in app
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4680512Z     raw_response = await run_endpoint_function(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4681331Z .venv/lib/python3.13/site-packages/fastapi/routing.py:328: in run_endpoint_function
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4682121Z     return await dependant.call(**values)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4682639Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4683474Z packages/core/src/core/tracing.py:48: in async_wrapper
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4684088Z     result = await func(*args, **kwargs)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4684585Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4685440Z apps/api/src/api/routers/workspace.py:271: in git_revert_endpoint
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4686129Z     mgr.revert_file(body.path)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4686713Z _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4687187Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4687556Z self = <core.workspace.WorkspaceManager object at 0x7fd359df17b0>
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4688216Z rel_path = '/diff_test.txt'
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4688548Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4688831Z     def revert_file(self, rel_path: str) -> None:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4689544Z         """Revert a file back to HEAD state or delete if untracked."""
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4690426Z         abs_path = self.sanitize_path(rel_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4691008Z         is_untracked = False
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4691502Z         try:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4691914Z             res_status = subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4692485Z                 ["git", "status", "--porcelain", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4693075Z                 cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4693578Z                 capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4694085Z                 text=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4694518Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4694978Z             if res_status.stdout.startswith("??"):
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4695547Z                 is_untracked = True
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4696036Z         except Exception:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4696479Z             pass
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4696881Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4697261Z         if is_untracked:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4697742Z             if os.path.isdir(abs_path):
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4698260Z                 import shutil
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4698713Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4699096Z                 shutil.rmtree(abs_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4699622Z             elif os.path.exists(abs_path):
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4700138Z                 os.remove(abs_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4700829Z         else:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4701241Z             try:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4701656Z                 subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4702181Z                     ["git", "reset", "HEAD", "--", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4702775Z                     cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4703282Z                     capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4703774Z                 )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4704192Z                 subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4704731Z                     ["git", "checkout", "HEAD", "--", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4705339Z                     cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4705857Z                     capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4706362Z                     check=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4706814Z                 )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4707239Z             except Exception as e:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4708316Z                 logger.error("Failed to revert file %s: %s", rel_path, e)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4709285Z >               raise RuntimeError(f"Failed to revert file: {e}")
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4711037Z E               RuntimeError: Failed to revert file: Command '['git', 'checkout', 'HEAD', '--', '/tmp/tmp21etbo73/diff_test.txt']' returned non-zero exit status 128.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4712179Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4712617Z packages/core/src/core/workspace.py:778: RuntimeError
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4713506Z ----------------------------- Captured stdout call -----------------------------
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4715116Z {"event": "Initialized local Git repository in workspace /tmp/tmp21etbo73", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:56.756632Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4716942Z {"event": "Created default .gitignore in /tmp/tmp21etbo73/.gitignore", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:56.756787Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.4719105Z {"event": "Failed to commit changes: Command '['git', 'commit', '-m', 'initial commit']' returned non-zero exit status 128.", "level": "error", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:56.769075Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6056933Z {"event": "Failed to revert file /diff_test.txt: Command '['git', 'checkout', 'HEAD', '--', '/tmp/tmp21etbo73/diff_test.txt']' returned non-zero exit status 128.", "level": "error", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:56.783100Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6060794Z _________________ test_workspace_config_and_remote_operations __________________
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6061723Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6062172Z client = <starlette.testclient.TestClient object at 0x7fd359d03df0>
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6062786Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6063162Z     def test_workspace_config_and_remote_operations(client):
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6063828Z         import subprocess
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6064310Z         import shutil
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6064714Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6065127Z         # 1. GET config initially
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6065625Z         response = client.get(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6066257Z             "/api/workspace/config", params={"session_id": "test-session"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6066898Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6067330Z         assert response.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6067858Z         data = response.json()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6068353Z         assert "workspace_id" in data
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6068887Z         assert data["git_remote_url"] is None
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6069427Z         assert data["git_username"] is None
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6069970Z         assert data["has_token"] is False
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6070728Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6071176Z         # 2. Create a bare remote repository
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6071744Z         remote_dir = tempfile.mkdtemp()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6072282Z         try:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6072850Z             subprocess.run(["git", "init", "--bare"], cwd=remote_dir, check=True)
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6073529Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6073942Z             # Configure remote URL
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6074459Z             response_config = client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6074974Z                 "/api/workspace/config",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6075489Z                 json={
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6075962Z                     "session_id": "test-session",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6076526Z                     "git_remote_url": remote_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6077092Z                     "git_username": "test-user",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6077648Z                     "git_token": "test-token",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6078154Z                 },
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6078544Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6078983Z             assert response_config.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6079612Z             assert response_config.json()["success"] is True
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6080170Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6080953Z             # Verify settings updated in GET
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6081501Z             response = client.get(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6082148Z                 "/api/workspace/config", params={"session_id": "test-session"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6082785Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6083192Z             data = response.json()
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6083718Z             assert data["git_remote_url"] == remote_dir
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6084326Z             assert data["git_username"] == "test-user"
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6084898Z             assert data["has_token"] is True
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6085402Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6085813Z             # 3. Create a local file and commit it
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6086366Z             client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6086827Z                 "/api/workspace/files",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6087333Z                 json={
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6087828Z                     "session_id": "test-session",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6088392Z                     "path": "/push_test.txt",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6088906Z                     "type": "file",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6089370Z                 },
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6089766Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6090747Z             client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6091213Z                 "/api/workspace/git/commit",
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6091910Z                 json={"session_id": "test-session", "message": "feat: test remote push"},
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6092827Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6093198Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6093581Z             # 4. Push to remote
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6094054Z             push_res = client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6094707Z                 "/api/workspace/git/push", json={"session_id": "test-session"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6095375Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6095799Z >           assert push_res.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6096332Z E           assert 500 == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6096925Z E            +  where 500 = <Response [500 Internal Server Error]>.status_code
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6097471Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6097791Z apps/api/tests/test_workspace_api.py:383: AssertionError
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6098572Z ----------------------------- Captured stdout call -----------------------------
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6099360Z Initialized empty Git repository in /tmp/tmpwa_alc2d/
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6100897Z {"event": "Initialized local Git repository in workspace /tmp/tmpvj3h2_br", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:57.157957Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6102679Z {"event": "Created default .gitignore in /tmp/tmpvj3h2_br/.gitignore", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:57.158144Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6104664Z {"event": "Failed to commit changes: Command '['git', 'commit', '-m', 'feat: test remote push']' returned non-zero exit status 128.", "level": "error", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:57.169973Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6107424Z {"event": "Failed to push changes: Command '['git', 'push', '/tmp/tmpwa_alc2d', 'master']' returned non-zero exit status 1.\nStderr: error: src refspec master does not match any\nerror: failed to push some refs to '/tmp/tmpwa_alc2d'\n", "level": "error", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:57.178317Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6109508Z ----------------------------- Captured stderr call -----------------------------
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6110594Z hint: Using 'master' as the name for the initial branch. This default branch name
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6111514Z hint: will change to "main" in Git 3.0. To configure the initial branch name
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6112390Z hint: to use in all of your new repositories, which will suppress this warning,
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6113091Z hint: call:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6113469Z hint:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6113933Z hint: 	git config --global init.defaultBranch <name>
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6114516Z hint:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6115069Z hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6116100Z hint: 'development'. The just-created branch can be renamed via this command:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6116806Z hint:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6117198Z hint: 	git branch -m <name>
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6117681Z hint:
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6118268Z hint: Disable this message with "git config set advice.defaultBranchName false"
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6119085Z =============================== warnings summary ===============================
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6119832Z .venv/lib/python3.13/site-packages/fastapi/testclient.py:1
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6121606Z   /home/runner/work/wright/wright/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6123254Z     from starlette.testclient import TestClient as TestClient  # noqa
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6123841Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6124281Z -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6125069Z =========================== short test summary info ============================
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6126007Z FAILED apps/api/tests/test_workspace_api.py::test_git_status_and_commit - assert 500 == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6127219Z  +  where 500 = <Response [500 Internal Server Error]>.status_code
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6128771Z FAILED apps/api/tests/test_workspace_api.py::test_git_diff_and_revert - RuntimeError: Failed to revert file: Command '['git', 'checkout', 'HEAD', '--', '/tmp/tmp21etbo73/diff_test.txt']' returned non-zero exit status 128.
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6131025Z FAILED apps/api/tests/test_workspace_api.py::test_workspace_config_and_remote_operations - assert 500 == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6132045Z  +  where 500 = <Response [500 Internal Server Error]>.status_code
python-quality	Run Tests with pytest	2026-06-05T15:58:57.6132781Z =================== 3 failed, 42 passed, 1 warning in 2.83s ====================
python-quality	Run Tests with pytest	2026-06-05T15:58:57.7564728Z ##[error]Process completed with exit code 1.
```

---

## 4. Docker Build CI (Run #27025470026)
- **Branch**: `dev`
- **Commit SHA**: `2ceded12d1146c23d62b4b8c7c6aeb3d831bb82f`
- **Time**: 2026-06-05T15:58:30Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27025470026)

### Failed Log Output
```text
build-and-push	Build and Load (Local Test)	﻿2026-06-05T15:58:44.5108665Z ##[group]Run docker/build-push-action@v6
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5108979Z with:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5109183Z   context: .
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5109397Z   file: docker/Dockerfile
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5109635Z   load: true
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5109909Z   tags: wright-agent:9ce19851c326b494870f24e6bc2417f3ea764a13
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5110485Z   build-args: VERSION=3/merge
build-and-push	Build and Load (Local Test)	REVISION=9ce19851c326b494870f24e6bc2417f3ea764a13
build-and-push	Build and Load (Local Test)	CREATED=2026-06-05T15:58:43Z
build-and-push	Build and Load (Local Test)	
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5110990Z   cache-from: type=gha
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5111241Z   cache-to: type=gha,mode=max
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5111499Z   no-cache: false
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5111719Z   pull: false
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5111927Z   push: false
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5114802Z   github-token: ***
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5115156Z env:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5115495Z   DOCKER_METADATA_OUTPUT_VERSION: sha-9ce19851c326b494870f24e6bc2417f3ea764a13
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5116064Z   DOCKER_METADATA_OUTPUT_TAGS: /wright-agent:sha-9ce19851c326b494870f24e6bc2417f3ea764a13
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5116659Z   DOCKER_METADATA_OUTPUT_TAG_NAMES: sha-9ce19851c326b494870f24e6bc2417f3ea764a13
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5118769Z   DOCKER_METADATA_OUTPUT_LABELS: org.opencontainers.image.created=2026-06-05T15:58:44.471Z
build-and-push	Build and Load (Local Test)	org.opencontainers.image.description=A digital engineer, designer, and mechanical analyst
build-and-push	Build and Load (Local Test)	org.opencontainers.image.licenses=MIT
build-and-push	Build and Load (Local Test)	org.opencontainers.image.revision=9ce19851c326b494870f24e6bc2417f3ea764a13
build-and-push	Build and Load (Local Test)	org.opencontainers.image.source=https://github.com/burhop/wright
build-and-push	Build and Load (Local Test)	org.opencontainers.image.title=wright
build-and-push	Build and Load (Local Test)	org.opencontainers.image.url=https://github.com/burhop/wright
build-and-push	Build and Load (Local Test)	org.opencontainers.image.version=sha-9ce19851c326b494870f24e6bc2417f3ea764a13
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5122650Z   DOCKER_METADATA_OUTPUT_ANNOTATIONS: manifest:org.opencontainers.image.created=2026-06-05T15:58:44.471Z
build-and-push	Build and Load (Local Test)	manifest:org.opencontainers.image.description=A digital engineer, designer, and mechanical analyst
build-and-push	Build and Load (Local Test)	manifest:org.opencontainers.image.licenses=MIT
build-and-push	Build and Load (Local Test)	manifest:org.opencontainers.image.revision=9ce19851c326b494870f24e6bc2417f3ea764a13
build-and-push	Build and Load (Local Test)	manifest:org.opencontainers.image.source=https://github.com/burhop/wright
build-and-push	Build and Load (Local Test)	manifest:org.opencontainers.image.title=wright
build-and-push	Build and Load (Local Test)	manifest:org.opencontainers.image.url=https://github.com/burhop/wright
build-and-push	Build and Load (Local Test)	manifest:org.opencontainers.image.version=sha-9ce19851c326b494870f24e6bc2417f3ea764a13
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5129433Z   DOCKER_METADATA_OUTPUT_JSON: {"tags":["/wright-agent:sha-9ce19851c326b494870f24e6bc2417f3ea764a13"],"tag-names":["sha-9ce19851c326b494870f24e6bc2417f3ea764a13"],"labels":{"org.opencontainers.image.created":"2026-06-05T15:58:44.471Z","org.opencontainers.image.description":"A digital engineer, designer, and mechanical analyst","org.opencontainers.image.licenses":"MIT","org.opencontainers.image.revision":"9ce19851c326b494870f24e6bc2417f3ea764a13","org.opencontainers.image.source":"https://github.com/burhop/wright","org.opencontainers.image.title":"wright","org.opencontainers.image.url":"https://github.com/burhop/wright","org.opencontainers.image.version":"sha-9ce19851c326b494870f24e6bc2417f3ea764a13"},"annotations":["manifest:org.opencontainers.image.created=2026-06-05T15:58:44.471Z","manifest:org.opencontainers.image.description=A digital engineer, designer, and mechanical analyst","manifest:org.opencontainers.image.licenses=MIT","manifest:org.opencontainers.image.revision=9ce19851c326b494870f24e6bc2417f3ea764a13","manifest:org.opencontainers.image.source=https://github.com/burhop/wright","manifest:org.opencontainers.image.title=wright","manifest:org.opencontainers.image.url=https://github.com/burhop/wright","manifest:org.opencontainers.image.version=sha-9ce19851c326b494870f24e6bc2417f3ea764a13"]}
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5134529Z   DOCKER_METADATA_OUTPUT_BAKE_FILE_TAGS: /home/runner/work/_temp/docker-actions-toolkit-HTfGjS/docker-metadata-action-bake-tags.json
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5135866Z   DOCKER_METADATA_OUTPUT_BAKE_FILE_LABELS: /home/runner/work/_temp/docker-actions-toolkit-HTfGjS/docker-metadata-action-bake-labels.json
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5136846Z   DOCKER_METADATA_OUTPUT_BAKE_FILE_ANNOTATIONS: /home/runner/work/_temp/docker-actions-toolkit-HTfGjS/docker-metadata-action-bake-annotations.json
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5137976Z   DOCKER_METADATA_OUTPUT_BAKE_FILE: /home/runner/work/_temp/docker-actions-toolkit-HTfGjS/docker-metadata-action-bake.json
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.5138533Z ##[endgroup]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8105917Z ##[group]GitHub Actions runtime token ACs
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8140364Z refs/pull/3/merge: read/write
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8141047Z refs/heads/main: read
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8152496Z ##[endgroup]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8153299Z ##[group]Docker info
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8285911Z [command]/usr/bin/docker version
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8599675Z Client: Docker Engine - Community
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8625709Z  Version:           28.0.4
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8645672Z  API version:       1.48
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8665681Z  Go version:        go1.23.7
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8666414Z  Git commit:        b8034c0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8669642Z  Built:             Tue Mar 25 15:07:16 2025
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8685717Z  OS/Arch:           linux/amd64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8704444Z  Context:           default
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8725404Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8745518Z Server: Docker Engine - Community
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8746195Z  Engine:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8754475Z   Version:          28.0.4
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8775768Z   API version:      1.48 (minimum version 1.24)
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8788337Z   Go version:       go1.23.7
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8795570Z   Git commit:       6430e49
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8816573Z   Built:            Tue Mar 25 15:07:16 2025
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8825586Z   OS/Arch:          linux/amd64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8845730Z   Experimental:     false
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8857250Z  containerd:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8895168Z   Version:          v2.2.4
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8956423Z   GitCommit:        193637f7ee8ae5f5aa5248f49e7baa3e6164966e
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.8975668Z  runc:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9015893Z   Version:          1.3.5
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9035557Z   GitCommit:        v1.3.5-0-g488fc13e
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9075469Z  docker-init:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9094068Z   Version:          0.19.0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9122517Z   GitCommit:        de40ad0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9155531Z [command]/usr/bin/docker info
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9640589Z Client: Docker Engine - Community
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9641491Z  Version:    28.0.4
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9642049Z  Context:    default
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9642550Z  Debug Mode: false
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9643086Z  Plugins:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9643633Z   buildx: Docker Buildx (Docker Inc.)
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9644243Z     Version:  v0.34.1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9644839Z     Path:     /usr/libexec/docker/cli-plugins/docker-buildx
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9645818Z   compose: Docker Compose (Docker Inc.)
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9646414Z     Version:  v2.38.2
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9647006Z     Path:     /usr/libexec/docker/cli-plugins/docker-compose
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9647550Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9647893Z Server:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9648345Z  Containers: 1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9648826Z   Running: 1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9649288Z   Paused: 0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9649768Z   Stopped: 0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9650227Z  Images: 7
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9650700Z  Server Version: 28.0.4
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9651207Z  Storage Driver: overlay2
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9651730Z   Backing Filesystem: extfs
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9652250Z   Supports d_type: true
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9652787Z   Using metacopy: false
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9653307Z   Native Overlay Diff: false
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9653832Z   userxattr: false
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9654320Z  Logging Driver: json-file
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9654835Z  Cgroup Driver: systemd
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9655592Z  Cgroup Version: 2
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9656068Z  Plugins:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9656572Z   Volume: local
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9657146Z   Network: bridge host ipvlan macvlan null overlay
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9658055Z   Log: awslogs fluentd gcplogs gelf journald json-file local splunk syslog
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9658846Z  Swarm: inactive
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9659372Z  Runtimes: io.containerd.runc.v2 runc
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9660349Z  Default Runtime: runc
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9660864Z  Init Binary: docker-init
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9661546Z  containerd version: 193637f7ee8ae5f5aa5248f49e7baa3e6164966e
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9662268Z  runc version: v1.3.5-0-g488fc13e
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9662866Z  init version: de40ad0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9663422Z  Security Options:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9663946Z   apparmor
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9664427Z   seccomp
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9664873Z    Profile: builtin
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9665595Z   cgroupns
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9666113Z  Kernel Version: 6.17.0-1015-azure
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9666713Z  Operating System: Ubuntu 24.04.4 LTS
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9667255Z  OSType: linux
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9667727Z  Architecture: x86_64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9668200Z  CPUs: 2
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9668656Z  Total Memory: 7.752GiB
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9669183Z  Name: runnervm3jyl0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9669753Z  ID: d0edc0b0-60b3-4f7a-aee7-b8b49cb2e501
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9670382Z  Docker Root Dir: /var/lib/docker
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9670960Z  Debug Mode: false
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9671488Z  Username: githubactions
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9672042Z  Experimental: false
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9672591Z  Insecure Registries:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9673165Z   ::1/128
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9673640Z   127.0.0.0/8
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9674162Z  Live Restore Enabled: false
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9674625Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9675626Z ##[endgroup]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9676470Z ##[group]Proxy configuration
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9677065Z No proxy configuration found
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:44.9677837Z ##[endgroup]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.0399682Z ##[group]Buildx version
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.0422754Z [command]/usr/bin/docker buildx version
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.0928687Z github.com/docker/buildx v0.34.1 e0b0e77d18d3379bc1e0d55f3b37de288d36fe47
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.0961172Z ##[endgroup]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.0961949Z ##[group]Builder info
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1946355Z {
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1947024Z   "nodes": [
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1947522Z     {
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1948094Z       "name": "builder-9f02d814-dffe-4818-8820-f78b2bddeb2a0",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1948930Z       "endpoint": "unix:///var/run/docker.sock",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1949501Z       "status": "running",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1950460Z       "buildkitd-flags": "--allow-insecure-entitlement security.insecure --allow-insecure-entitlement network.host",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1951481Z       "buildkit": "v0.30.0",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1952226Z       "platforms": "linux/amd64,linux/amd64/v2,linux/amd64/v3,linux/386",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1952928Z       "features": {
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1953554Z         "Automatically load images to the Docker Engine image store": true,
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1954230Z         "Cache export": true,
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1954760Z         "Direct push": true,
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1955549Z         "Docker exporter": true,
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1956101Z         "Multi-platform build": true,
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1956647Z         "OCI exporter": true
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1957166Z       },
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1957548Z       "labels": {
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1958132Z         "org.mobyproject.buildkit.worker.executor": "oci",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1958920Z         "org.mobyproject.buildkit.worker.hostname": "9cd385a342e0",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1959726Z         "org.mobyproject.buildkit.worker.network": "host",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1960498Z         "org.mobyproject.buildkit.worker.oci.process-mode": "sandbox",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1961470Z         "org.mobyproject.buildkit.worker.selinux.enabled": "false",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1962301Z         "org.mobyproject.buildkit.worker.snapshotter": "overlayfs"
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1963017Z       },
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1963437Z       "gcPolicy": [
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1963894Z         {
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1964283Z           "all": false,
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1964762Z           "filter": [
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1965486Z             "type==source.local",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1966037Z             "type==exec.cachemount",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1966620Z             "type==source.git.checkout"
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1967493Z           ],
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1967947Z           "keepDuration": "48h0m0s",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1968463Z           "maxUsedSpace": "488.3MiB"
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1968994Z         },
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1969394Z         {
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1969818Z           "all": false,
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1970284Z           "keepDuration": "1440h0m0s",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1970845Z           "reservedSpace": "7.451GiB",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1971364Z           "maxUsedSpace": "54.02GiB",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1971942Z           "minFreeSpace": "13.97GiB"
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1972458Z         },
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1972899Z         {
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1973283Z           "all": false,
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1973740Z           "reservedSpace": "7.451GiB",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1974324Z           "maxUsedSpace": "54.02GiB",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1974853Z           "minFreeSpace": "13.97GiB"
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1975734Z         },
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1976129Z         {
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1976567Z           "all": true,
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1977042Z           "reservedSpace": "7.451GiB",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1977612Z           "maxUsedSpace": "54.02GiB",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1978119Z           "minFreeSpace": "13.97GiB"
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1978648Z         }
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1979034Z       ]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1979459Z     }
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1979843Z   ],
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1980373Z   "name": "builder-9f02d814-dffe-4818-8820-f78b2bddeb2a",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1981047Z   "driver": "docker-container",
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1981622Z   "lastActivity": "2026-06-05T15:58:39.000Z"
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1982149Z }
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.1983029Z ##[endgroup]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.3683266Z [command]/usr/bin/docker buildx build --build-arg VERSION=3/merge --build-arg REVISION=9ce19851c326b494870f24e6bc2417f3ea764a13 --build-arg CREATED=2026-06-05T15:58:43Z --cache-from type=gha --cache-to type=gha,mode=max --file docker/Dockerfile --iidfile /home/runner/work/_temp/docker-actions-toolkit-1ra7mI/build-iidfile-bbc345aa80.txt --tag wright-agent:9ce19851c326b494870f24e6bc2417f3ea764a13 --load --metadata-file /home/runner/work/_temp/docker-actions-toolkit-1ra7mI/build-metadata-20348b336a.json .
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6762819Z #0 building with "builder-9f02d814-dffe-4818-8820-f78b2bddeb2a" instance using docker-container driver
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6763459Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6763775Z #1 [internal] load build definition from Dockerfile
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6764183Z #1 transferring dockerfile: 8.01kB done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6764451Z #1 DONE 0.0s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6764565Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6764919Z #2 [auth] library/ubuntu:pull token for registry-1.docker.io
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6765523Z #2 DONE 0.0s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6765730Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6766040Z #3 [auth] library/node:pull token for registry-1.docker.io
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6766431Z #3 DONE 0.0s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6766633Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.6766929Z #4 [internal] load metadata for docker.io/library/ubuntu:24.04
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.7982777Z #4 ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.7983383Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.7983850Z #5 [internal] load metadata for ghcr.io/astral-sh/uv:latest
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.7984512Z #5 DONE 0.3s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9001297Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9003090Z #4 [internal] load metadata for docker.io/library/ubuntu:24.04
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9003996Z #4 DONE 0.4s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9008855Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9009971Z #6 [internal] load metadata for docker.io/library/node:22-slim
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9013241Z #6 DONE 0.4s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9013955Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9017770Z #7 [internal] load .dockerignore
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9019053Z #7 transferring context: 448B done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9025715Z #7 DONE 0.0s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9092878Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:45.9093574Z #8 importing cache manifest from gha:15740652020200256831
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.0237916Z #8 DONE 0.0s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.0238404Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.0244086Z #9 FROM ghcr.io/astral-sh/uv:latest@sha256:b46b03ddfcfbf8f547af7e9eaefdf8a39c8cebcba7c98858d3162bd28cf536f6
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.0246433Z #9 resolve ghcr.io/astral-sh/uv:latest@sha256:b46b03ddfcfbf8f547af7e9eaefdf8a39c8cebcba7c98858d3162bd28cf536f6 done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.0249131Z #9 sha256:d76e59d7d403c708ef46713a94c7a4f36ad1d23caa4bc4fab493a83be451fcc5 98B / 98B 0.0s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.1454051Z #9 ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.1455999Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.1457020Z #10 [internal] load build context
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.1459215Z #10 transferring context: 1.41MB 0.1s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.1460498Z #10 DONE 0.1s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.1461065Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.1462568Z #9 FROM ghcr.io/astral-sh/uv:latest@sha256:b46b03ddfcfbf8f547af7e9eaefdf8a39c8cebcba7c98858d3162bd28cf536f6
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.1464035Z #9 sha256:14fdc1e6fbef8e37deea6aed2bc4e25fad8fa76abd164deb11360c38d1c0c0d3 13.63MB / 25.14MB 0.2s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.2555247Z #9 sha256:14fdc1e6fbef8e37deea6aed2bc4e25fad8fa76abd164deb11360c38d1c0c0d3 25.14MB / 25.14MB 0.2s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.2558393Z #9 extracting sha256:14fdc1e6fbef8e37deea6aed2bc4e25fad8fa76abd164deb11360c38d1c0c0d3
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.9338323Z #9 extracting sha256:14fdc1e6fbef8e37deea6aed2bc4e25fad8fa76abd164deb11360c38d1c0c0d3 0.7s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:46.9340967Z #9 extracting sha256:d76e59d7d403c708ef46713a94c7a4f36ad1d23caa4bc4fab493a83be451fcc5
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.0936946Z #9 extracting sha256:d76e59d7d403c708ef46713a94c7a4f36ad1d23caa4bc4fab493a83be451fcc5 0.0s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.0938358Z #9 DONE 1.0s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.0938677Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.0939685Z #11 [web-builder 1/7] FROM docker.io/library/node:22-slim@sha256:7af03b14a13c8cdd38e45058fd957bf00a72bbe17feac43b1c15a689c029c732
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.0941285Z #11 resolve docker.io/library/node:22-slim@sha256:7af03b14a13c8cdd38e45058fd957bf00a72bbe17feac43b1c15a689c029c732 0.0s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.0942624Z #11 sha256:79b3835561d335125b55d15b510f00002f0a8fc544a15f74b9f13059a1c701c7 447B / 447B 0.0s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.0944527Z #11 sha256:5d2860e0a8119005f3887b3814e7bcd48e2f27a91d53c64ec458f3aba0090ee4 3.31kB / 3.31kB 0.0s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.0946413Z #11 sha256:fd31133e23d87bcc829a1d3614f1c82c8ece76a04efa592d3a8a0dc694159ba6 1.71MB / 1.71MB 0.1s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.0949817Z #11 sha256:3d75e56d73fdaadbfdf0dd14218e00d88560d320f8e8e72508e6b4b67d63aa17 49.93MB / 49.93MB 0.3s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.1210602Z #11 sha256:068fedd6b0f109b8186d00d49327b6fc6747c428fd3c9a8739424ff5f38d7531 28.23MB / 28.23MB 0.5s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.1212435Z #11 extracting sha256:068fedd6b0f109b8186d00d49327b6fc6747c428fd3c9a8739424ff5f38d7531
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.9535782Z #11 ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.9538418Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.9539253Z #12 [stage-1  1/33] FROM docker.io/library/ubuntu:24.04@sha256:786a8b558f7be160c6c8c4a54f9a57274f3b4fb1491cf65146521ae77ff1dc54
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.9540578Z #12 resolve docker.io/library/ubuntu:24.04@sha256:786a8b558f7be160c6c8c4a54f9a57274f3b4fb1491cf65146521ae77ff1dc54 0.0s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.9541838Z #12 sha256:cb259a83ac3dd9fea0b394df41df2b298adf0df938fef5999475af18a751c257 29.73MB / 29.73MB 0.5s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.9543070Z #12 extracting sha256:cb259a83ac3dd9fea0b394df41df2b298adf0df938fef5999475af18a751c257 1.5s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:47.9543824Z #12 DONE 2.0s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.0669750Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.0672884Z #11 [web-builder 1/7] FROM docker.io/library/node:22-slim@sha256:7af03b14a13c8cdd38e45058fd957bf00a72bbe17feac43b1c15a689c029c732
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.0674401Z #11 extracting sha256:068fedd6b0f109b8186d00d49327b6fc6747c428fd3c9a8739424ff5f38d7531 1.5s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.0675650Z #11 DONE 2.1s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.0675866Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.0677253Z #13 [stage-1  2/33] RUN apt-get update && apt-get install -y --no-install-recommends     software-properties-common     curl     git     build-essential     ca-certificates     sudo     vim     nano     htop     jq     gnupg     supervisor     openscad     xvfb     && rm -rf /var/lib/apt/lists/*
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.2359633Z #13 0.197 Get:1 http://security.ubuntu.com/ubuntu noble-security InRelease [126 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.2361980Z #13 0.283 Get:2 http://archive.ubuntu.com/ubuntu noble InRelease [256 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.3584000Z #13 0.406 Get:3 http://archive.ubuntu.com/ubuntu noble-updates InRelease [126 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.4708914Z #13 0.518 Get:4 http://archive.ubuntu.com/ubuntu noble-backports InRelease [126 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.6159687Z #13 0.603 Get:5 http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages [2148 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.6161389Z #13 0.606 Get:6 http://archive.ubuntu.com/ubuntu noble/main amd64 Packages [1808 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.6162813Z #13 0.663 Get:7 http://archive.ubuntu.com/ubuntu noble/multiverse amd64 Packages [331 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.8231454Z #13 0.665 Get:8 http://archive.ubuntu.com/ubuntu noble/universe amd64 Packages [19.3 MB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.8232737Z #13 0.681 Get:9 http://security.ubuntu.com/ubuntu noble-security/universe amd64 Packages [1513 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.8234072Z #13 0.718 Get:10 http://security.ubuntu.com/ubuntu noble-security/multiverse amd64 Packages [48.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.8235869Z #13 0.720 Get:11 http://security.ubuntu.com/ubuntu noble-security/restricted amd64 Packages [3807 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:48.8991539Z #13 0.947 Get:12 http://archive.ubuntu.com/ubuntu noble/restricted amd64 Packages [117 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.2796478Z #13 0.950 Get:13 http://archive.ubuntu.com/ubuntu noble-updates/restricted amd64 Packages [4038 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.4216993Z #13 1.004 Get:14 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages [2525 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.4235889Z #13 1.037 Get:15 http://archive.ubuntu.com/ubuntu noble-updates/multiverse amd64 Packages [54.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.4237297Z #13 1.039 Get:16 http://archive.ubuntu.com/ubuntu noble-updates/universe amd64 Packages [2155 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.5148331Z #13 1.325 Get:17 http://archive.ubuntu.com/ubuntu noble-backports/multiverse amd64 Packages [671 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.5151431Z #13 1.333 Get:18 http://archive.ubuntu.com/ubuntu noble-backports/main amd64 Packages [49.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.5152861Z #13 1.341 Get:19 http://archive.ubuntu.com/ubuntu noble-backports/universe amd64 Packages [35.9 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.9181571Z #13 ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.9183686Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.9184706Z #11 [web-builder 1/7] FROM docker.io/library/node:22-slim@sha256:7af03b14a13c8cdd38e45058fd957bf00a72bbe17feac43b1c15a689c029c732
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.9186561Z #11 extracting sha256:5d2860e0a8119005f3887b3814e7bcd48e2f27a91d53c64ec458f3aba0090ee4 done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.9187821Z #11 extracting sha256:3d75e56d73fdaadbfdf0dd14218e00d88560d320f8e8e72508e6b4b67d63aa17 1.8s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:49.9188859Z #11 DONE 4.0s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:50.1547688Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:50.1551075Z #11 [web-builder 1/7] FROM docker.io/library/node:22-slim@sha256:7af03b14a13c8cdd38e45058fd957bf00a72bbe17feac43b1c15a689c029c732
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:50.1552813Z #11 extracting sha256:fd31133e23d87bcc829a1d3614f1c82c8ece76a04efa592d3a8a0dc694159ba6 0.1s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:50.1554123Z #11 extracting sha256:79b3835561d335125b55d15b510f00002f0a8fc544a15f74b9f13059a1c701c7 0.0s done
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:50.1555244Z #11 DONE 4.1s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:50.1555627Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:50.1555956Z #14 [web-builder 2/7] WORKDIR /workspace
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:51.9374973Z #14 DONE 1.9s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:51.9377503Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:51.9379323Z #13 [stage-1  2/33] RUN apt-get update && apt-get install -y --no-install-recommends     software-properties-common     curl     git     build-essential     ca-certificates     sudo     vim     nano     htop     jq     gnupg     supervisor     openscad     xvfb     && rm -rf /var/lib/apt/lists/*
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:51.9381396Z #13 2.687 Fetched 38.6 MB in 3s (14.9 MB/s)
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:51.9382083Z #13 2.687 Reading package lists...
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:52.1461510Z #13 3.839 Reading package lists...
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:52.1462571Z #13 ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:52.1462759Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:52.1463024Z #15 [web-builder 3/7] COPY package.json package-lock.json ./
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:52.1463586Z #15 DONE 0.0s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:52.1463778Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:52.1464072Z #16 [web-builder 4/7] COPY apps/web/package.json apps/web/package.json
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:52.1465427Z #16 DONE 0.0s
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:52.2958335Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:52.2959528Z #17 [web-builder 5/7] RUN npm ci
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0497070Z #17 ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0497845Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0499730Z #13 [stage-1  2/33] RUN apt-get update && apt-get install -y --no-install-recommends     software-properties-common     curl     git     build-essential     ca-certificates     sudo     vim     nano     htop     jq     gnupg     supervisor     openscad     xvfb     && rm -rf /var/lib/apt/lists/*
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0501816Z #13 3.839 Reading package lists...
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0502582Z #13 5.133 Building dependency tree...
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0503347Z #13 5.429 Reading state information...
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0504216Z #13 5.741 The following additional packages will be installed:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0505799Z #13 5.742   adduser binutils binutils-common binutils-x86-64-linux-gnu bzip2 cpp cpp-13
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0507314Z #13 5.743   cpp-13-x86-64-linux-gnu cpp-x86-64-linux-gnu dbus dbus-bin dbus-daemon
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0508525Z #13 5.744   dbus-session-bus-common dbus-system-bus-common dirmngr distro-info-data
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0509753Z #13 5.745   dpkg-dev fontconfig fontconfig-config fonts-dejavu-core fonts-dejavu-mono
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0511018Z #13 5.745   g++ g++-13 g++-13-x86-64-linux-gnu g++-x86-64-linux-gnu gcc gcc-13
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0512071Z #13 5.746   gcc-13-base gcc-13-x86-64-linux-gnu gcc-x86-64-linux-gnu
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0513174Z #13 5.747   gir1.2-girepository-2.0 gir1.2-glib-2.0 gir1.2-packagekitglib-1.0 git-man
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0515175Z #13 5.747   gnupg-utils gpg gpg-agent gpgconf gpgsm iso-codes keyboxd lib3mf1t64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0516258Z #13 5.747   libapparmor1 libappstream5 libargon2-1 libasan8 libasound2-data
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0529866Z #13 5.748   libasound2t64 libasyncns0 libatomic1 libavahi-client3 libavahi-common-data
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0530969Z #13 5.748   libavahi-common3 libbinutils libboost-filesystem1.83.0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0531967Z #13 5.749   libboost-program-options1.83.0 libbrotli1 libbsd0 libc-dev-bin libc6-dev
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0533075Z #13 5.749   libcairo2 libcap2-bin libcc1-0 libcrypt-dev libcryptsetup12 libctf-nobfd0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0534742Z #13 5.750   libctf0 libcups2t64 libcurl3t64-gnutls libcurl4t64 libdbus-1-3 libdecor-0-0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0536646Z #13 5.750   libdevmapper1.02.1 libdouble-conversion3 libdpkg-perl libdrm-amdgpu1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0537728Z #13 5.751   libdrm-common libdrm-intel1 libdrm2 libduktape207 libdw1t64 libedit2
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0538807Z #13 5.751   libegl-mesa0 libegl1 libelf1t64 liberror-perl libevdev2 libexpat1 libfdisk1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0539944Z #13 5.751   libflac12t64 libfontconfig1 libfontenc1 libfreetype6 libgbm1 libgcc-13-dev
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0541068Z #13 5.752   libgdbm-compat4t64 libgdbm6t64 libgirepository-1.0-1 libgl1 libgl1-mesa-dri
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0542207Z #13 5.752   libglew2.2 libglib2.0-0t64 libglib2.0-bin libglib2.0-data libglu1-mesa
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0543286Z #13 5.753   libglvnd0 libglx-mesa0 libglx0 libgomp1 libgpm2 libgprofng0 libgraphite2-3
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0544409Z #13 5.753   libgssapi-krb5-2 libgstreamer1.0-0 libgudev-1.0-0 libharfbuzz0b libhwasan0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0546176Z #13 5.753   libice6 libicu74 libinput-bin libinput10 libisl23 libitm1 libjansson4
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0547819Z #13 5.754   libjpeg-turbo8 libjpeg8 libjq1 libjson-c5 libk5crypto3 libkeyutils1 libkmod2
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0549458Z #13 5.754   libkrb5-3 libkrb5support0 libksba8 libldap2 libllvm20 liblsan0 liblzma5
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0550523Z #13 5.754   libmd4c0 libmp3lame0 libmpc3 libmpfr6 libmpg123-0t64 libmtdev1t64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0551563Z #13 5.754   libnghttp2-14 libnl-3-200 libnl-genl-3-200 libogg0 libonig5 libopencsg1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0552657Z #13 5.755   libopengl0 libopus0 libpackagekit-glib2-18 libpam-systemd libpciaccess0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0553692Z #13 5.755   libpcre2-16-0 libperl5.38t64 libpixman-1-0 libpng16-16t64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0555961Z #13 5.755   libpolkit-agent-1-0 libpolkit-gobject-1-0 libpsl5t64 libpulse0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0556959Z #13 5.756   libpython3-stdlib libpython3.12-minimal libpython3.12-stdlib
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0557941Z #13 5.756   libpython3.12t64 libqscintilla2-qt5-15 libqscintilla2-qt5-l10n
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0558984Z #13 5.756   libqt5core5t64 libqt5dbus5t64 libqt5gamepad5 libqt5gui5t64 libqt5multimedia5
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0561740Z #13 5.756   libqt5network5t64 libqt5printsupport5t64 libqt5widgets5t64 libquadmath0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0563951Z #13 5.757   libreadline8t64 librtmp1 libsamplerate0 libsasl2-2 libsasl2-modules-db
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0565288Z #13 5.757   libsdl2-2.0-0 libsensors-config libsensors5 libsframe1 libsm6 libsndfile1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0566404Z #13 5.758   libsodium23 libspnav0 libsqlite3-0 libssh-4 libstdc++-13-dev libstemmer0d
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0568147Z #13 5.758   libsystemd-shared libtsan2 libubsan1 libunwind8 libvorbis0a libvorbisenc2
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0569571Z #13 5.758   libvulkan1 libwacom-common libwacom9 libwayland-client0 libwayland-cursor0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0570621Z #13 5.759   libwayland-egl1 libx11-6 libx11-data libx11-xcb1 libxau6 libxaw7
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0572026Z #13 5.759   libxcb-dri3-0 libxcb-glx0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0573039Z #13 5.759   libxcb-present0 libxcb-randr0 libxcb-render-util0 libxcb-render0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0574012Z #13 5.760   libxcb-shape0 libxcb-shm0 libxcb-sync1 libxcb-util1 libxcb-xfixes0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0576376Z #13 5.760   libxcb-xinerama0 libxcb-xinput0 libxcb-xkb1 libxcb1 libxcursor1 libxdmcp6
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0577933Z #13 5.760   libxext6 libxfixes3 libxfont2 libxi6 libxkbcommon-x11-0 libxkbcommon0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0579303Z #13 5.761   libxkbfile1 libxml2 libxmlb2 libxmu6 libxmuu1 libxpm4 libxrandr2 libxrender1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0580653Z #13 5.761   libxshmfence1 libxss1 libxt6t64 libxxf86vm1 libyaml-0-2 libzip4t64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0581708Z #13 5.762   linux-libc-dev lsb-release lto-disabled-list make media-types
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0582757Z #13 5.763   mesa-libgallium netbase openssl packagekit patch perl perl-modules-5.38
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0583843Z #13 5.763   pinentry-curses polkitd python-apt-common python3 python3-apt
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0584916Z #13 5.764   python3-blinker python3-cffi-backend python3-cryptography python3-dbus
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0586230Z #13 5.764   python3-distro python3-gi python3-httplib2 python3-jwt python3-launchpadlib
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0587869Z #13 5.765   python3-lazr.restfulclient python3-lazr.uri python3-minimal python3-oauthlib
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0588922Z #13 5.765   python3-pkg-resources python3-pyparsing python3-six
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0591341Z #13 5.766   python3-software-properties python3-wadllib python3.12 python3.12-minimal
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0594427Z #13 5.766   readline-common rpcsvc-proto sgml-base shared-mime-info systemd systemd-dev
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0606047Z #13 5.767   systemd-sysv tzdata vim-common vim-runtime x11-common x11-xkb-utils xauth
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0606852Z #13 5.767   xkb-data xml-core xserver-common xz-utils
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0607373Z #13 5.769 Suggested packages:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0608023Z #13 5.769   liblocale-gettext-perl cron quota ecryptfs-utils binutils-doc gprofng-gui
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0608924Z #13 5.770   bzip2-doc cpp-doc gcc-13-locales cpp-13-doc default-dbus-session-bus
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0609774Z #13 5.770   | dbus-session-bus dbus-user-session pinentry-gnome3 tor debian-keyring
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0610613Z #13 5.770   g++-multilib g++-13-multilib gcc-13-doc gcc-multilib manpages-dev autoconf
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0611463Z #13 5.771   automake libtool flex bison gdb gcc-doc gcc-13-multilib gdb-x86-64-linux-gnu
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0612394Z #13 5.771   gettext-base git-daemon-run | git-daemon-sysvinit git-doc git-email git-gui
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0613243Z #13 5.771   gitk gitweb git-cvs git-mediawiki git-svn parcimonie xloadimage
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0614366Z #13 5.771   gpg-wks-server scdaemon lm-sensors lsof strace isoquery alsa-utils
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0615423Z #13 5.772   libasound2-plugins glibc-doc cups-common bzr gdbm-l10n glew-utils
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0616281Z #13 5.772   low-memory-monitor gpm krb5-doc krb5-user gstreamer1.0-tools opus-tools
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0617145Z #13 5.772   pciutils pulseaudio libqscintilla2-doc libthai0 qgnomeplatform-qt5
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0618067Z #13 5.772   qt5-image-formats-plugins xdg-utils spacenavd libstdc++-13-doc libwacom-bin
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0619564Z #13 5.773   make-doc hunspell meshlab geomview librecad openscad-testing ed
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0620287Z #13 5.773   diffutils-doc perl-doc libterm-readline-gnu-perl
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0621059Z #13 5.773   | libterm-readline-perl-perl libtap-harness-archive-perl pinentry-doc
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0621908Z #13 5.774   polkitd-pkla python3-doc python3-tk python3-venv python-apt-doc
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0622775Z #13 5.774   python-blinker-doc python-cryptography-doc python3-cryptography-vectors
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0623681Z #13 5.775   python-dbus-doc python3-crypto python3-keyring python3-testresources
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0624556Z #13 5.775   python3-setuptools python-pyparsing-doc python3.12-venv python3.12-doc
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0625677Z #13 5.775   binfmt-support readline-doc sgml-base-doc supervisor-doc systemd-container
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0626602Z #13 5.776   systemd-homed systemd-userdbd systemd-boot libfido2-1 libip4tc2 libqrencode4
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0627494Z #13 5.776   libtss2-esys-3.0.2-0 libtss2-mu-4.0.1-0 libtss2-rc0 libtss2-tcti-device0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0628151Z #13 5.776   ctags vim-doc vim-scripts debhelper
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0628579Z #13 5.776 Recommended packages:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0629180Z #13 5.777   fakeroot libalgorithm-merge-perl less ssh-client gnupg-l10n gpg-wks-client
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0630010Z #13 5.777   alsa-ucm-conf alsa-topology-conf manpages manpages-dev libc-devtools
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0631045Z #13 5.777   libpam-cap default-libdecor-0-plugin-1 | libdecor-0-plugin-1 dmsetup
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0631942Z #13 5.778   libfile-fcntllock-perl liblocale-gettext-perl xdg-user-dirs krb5-locales
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0632803Z #13 5.778   libldap-common dbus-user-session publicsuffix qttranslations5-l10n
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0634342Z #13 5.779   libqt5svg5 qt5-gtk-platformtheme qtwayland5 libsasl2-modules
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0635513Z #13 5.779   mesa-vulkan-drivers | vulkan-icd openscad-mcad appstream packagekit-tools
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0636376Z #13 5.779   unattended-upgrades networkd-dispatcher systemd-timesyncd | time-daemon
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0637109Z #13 5.779   systemd-resolved libnss-systemd xxd xfonts-base
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0637703Z #13 6.453 The following NEW packages will be installed:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0638438Z #13 6.454   adduser binutils binutils-common binutils-x86-64-linux-gnu build-essential
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0639264Z #13 6.454   bzip2 ca-certificates cpp cpp-13 cpp-13-x86-64-linux-gnu
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0640042Z #13 6.455   cpp-x86-64-linux-gnu curl dbus dbus-bin dbus-daemon dbus-session-bus-common
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0640906Z #13 6.455   dbus-system-bus-common dirmngr distro-info-data dpkg-dev fontconfig
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0641719Z #13 6.456   fontconfig-config fonts-dejavu-core fonts-dejavu-mono g++ g++-13
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0642510Z #13 6.456   g++-13-x86-64-linux-gnu g++-x86-64-linux-gnu gcc gcc-13 gcc-13-base
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0643249Z #13 6.457   gcc-13-x86-64-linux-gnu gcc-x86-64-linux-gnu gir1.2-girepository-2.0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0644039Z #13 6.457   gir1.2-glib-2.0 gir1.2-packagekitglib-1.0 git git-man gnupg gnupg-utils gpg
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0644888Z #13 6.458   gpg-agent gpgconf gpgsm htop iso-codes jq keyboxd lib3mf1t64 libapparmor1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0645961Z #13 6.458   libappstream5 libargon2-1 libasan8 libasound2-data libasound2t64 libasyncns0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0646827Z #13 6.458   libatomic1 libavahi-client3 libavahi-common-data libavahi-common3
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0648144Z #13 6.459   libbinutils libboost-filesystem1.83.0 libboost-program-options1.83.0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0649167Z #13 6.459   libbrotli1 libbsd0 libc-dev-bin libc6-dev libcairo2 libcap2-bin libcc1-0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0650208Z #13 6.459   libcrypt-dev libcryptsetup12 libctf-nobfd0 libctf0 libcups2t64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0651055Z #13 6.459   libcurl3t64-gnutls libcurl4t64 libdbus-1-3 libdecor-0-0 libdevmapper1.02.1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0651881Z #13 6.460   libdouble-conversion3 libdpkg-perl libdrm-amdgpu1 libdrm-common
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0652702Z #13 6.460   libdrm-intel1 libdrm2 libduktape207 libdw1t64 libedit2 libegl-mesa0 libegl1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0653530Z #13 6.460   libelf1t64 liberror-perl libevdev2 libexpat1 libfdisk1 libflac12t64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0654584Z #13 6.461   libfontconfig1 libfontenc1 libfreetype6 libgbm1 libgcc-13-dev
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0656002Z #13 6.461   libgdbm-compat4t64 libgdbm6t64 libgirepository-1.0-1 libgl1 libgl1-mesa-dri
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0656859Z #13 6.462   libglew2.2 libglib2.0-0t64 libglib2.0-bin libglib2.0-data libglu1-mesa
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0657680Z #13 6.462   libglvnd0 libglx-mesa0 libglx0 libgomp1 libgpm2 libgprofng0 libgraphite2-3
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0658490Z #13 6.462   libgssapi-krb5-2 libgstreamer1.0-0 libgudev-1.0-0 libharfbuzz0b libhwasan0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0659319Z #13 6.463   libice6 libicu74 libinput-bin libinput10 libisl23 libitm1 libjansson4
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0660156Z #13 6.463   libjpeg-turbo8 libjpeg8 libjq1 libjson-c5 libk5crypto3 libkeyutils1 libkmod2
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0660991Z #13 6.464   libkrb5-3 libkrb5support0 libksba8 libldap2 libllvm20 liblsan0 libmd4c0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0662726Z #13 6.465   libmp3lame0 libmpc3 libmpfr6 libmpg123-0t64 libmtdev1t64 libnghttp2-14
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0663524Z #13 6.465   libnl-3-200 libnl-genl-3-200 libogg0 libonig5 libopencsg1 libopengl0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0664309Z #13 6.466   libopus0 libpackagekit-glib2-18 libpam-systemd libpciaccess0 libpcre2-16-0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0666325Z #13 6.466   libperl5.38t64 libpixman-1-0 libpng16-16t64 libpolkit-agent-1-0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0667110Z #13 6.467   libpolkit-gobject-1-0 libpsl5t64 libpulse0 libpython3-stdlib
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0667862Z #13 6.467   libpython3.12-minimal libpython3.12-stdlib libpython3.12t64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0668689Z #13 6.467   libqscintilla2-qt5-15 libqscintilla2-qt5-l10n libqt5core5t64 libqt5dbus5t64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0669548Z #13 6.467   libqt5gamepad5 libqt5gui5t64 libqt5multimedia5 libqt5network5t64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0670379Z #13 6.468   libqt5printsupport5t64 libqt5widgets5t64 libquadmath0 libreadline8t64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0671190Z #13 6.469   librtmp1 libsamplerate0 libsasl2-2 libsasl2-modules-db libsdl2-2.0-0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0672027Z #13 6.469   libsensors-config libsensors5 libsframe1 libsm6 libsndfile1 libsodium23
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0673169Z #13 6.470   libspnav0 libsqlite3-0 libssh-4 libstdc++-13-dev libstemmer0d
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0673960Z #13 6.470   libsystemd-shared libtsan2 libubsan1 libunwind8 libvorbis0a libvorbisenc2
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0674849Z #13 6.470   libvulkan1 libwacom-common libwacom9 libwayland-client0 libwayland-cursor0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0676503Z #13 6.471   libwayland-egl1 libx11-6 libx11-data libx11-xcb1 libxau6 libxaw7
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0677289Z #13 6.471   libxcb-dri3-0 libxcb-glx0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0678105Z #13 6.472   libxcb-present0 libxcb-randr0 libxcb-render-util0 libxcb-render0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0678908Z #13 6.472   libxcb-shape0 libxcb-shm0 libxcb-sync1 libxcb-util1 libxcb-xfixes0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0679727Z #13 6.472   libxcb-xinerama0 libxcb-xinput0 libxcb-xkb1 libxcb1 libxcursor1 libxdmcp6
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0680979Z #13 6.472   libxext6 libxfixes3 libxfont2 libxi6 libxkbcommon-x11-0 libxkbcommon0
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0681863Z #13 6.473   libxkbfile1 libxml2 libxmlb2 libxmu6 libxmuu1 libxpm4 libxrandr2 libxrender1
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0682744Z #13 6.474   libxshmfence1 libxss1 libxt6t64 libxxf86vm1 libyaml-0-2 libzip4t64
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0683497Z #13 6.475   linux-libc-dev lsb-release lto-disabled-list make media-types
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0684506Z #13 6.475   mesa-libgallium nano netbase openscad openssl packagekit patch perl
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0685505Z #13 6.476   perl-modules-5.38 pinentry-curses polkitd python-apt-common python3
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0686358Z #13 6.477   python3-apt python3-blinker python3-cffi-backend python3-cryptography
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0687223Z #13 6.477   python3-dbus python3-distro python3-gi python3-httplib2 python3-jwt
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0688030Z #13 6.477   python3-launchpadlib python3-lazr.restfulclient python3-lazr.uri
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0688882Z #13 6.477   python3-minimal python3-oauthlib python3-pkg-resources python3-pyparsing
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0690290Z #13 6.477   python3-six python3-software-properties python3-wadllib python3.12
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0691349Z #13 6.478   python3.12-minimal readline-common rpcsvc-proto sgml-base shared-mime-info
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0692812Z #13 6.478   software-properties-common sudo supervisor systemd systemd-dev systemd-sysv
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0693723Z #13 6.479   tzdata vim vim-common vim-runtime x11-common x11-xkb-utils xauth xkb-data
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0694405Z #13 6.479   xml-core xserver-common xvfb xz-utils
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0694928Z #13 6.481 The following packages will be upgraded:
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0695630Z #13 6.482   liblzma5
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0696112Z #13 6.552 1 upgraded, 319 newly installed, 0 to remove and 2 not upgraded.
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0696948Z #13 6.552 Need to get 212 MB of archives.
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0697566Z #13 6.552 After this operation, 827 MB of additional disk space will be used.
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0698684Z #13 6.552 Get:1 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpython3.12-minimal amd64 3.12.3-1ubuntu0.13 [837 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0699924Z #13 6.583 Get:2 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libexpat1 amd64 2.6.1-2ubuntu0.4 [88.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0701374Z #13 6.590 Get:3 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 python3.12-minimal amd64 3.12.3-1ubuntu0.13 [2346 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0702641Z #13 6.614 Get:4 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 python3-minimal amd64 3.12.3-0ubuntu2.1 [27.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0704259Z #13 6.624 Get:5 http://archive.ubuntu.com/ubuntu noble/main amd64 media-types all 10.1.0 [27.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0705834Z #13 6.636 Get:6 http://archive.ubuntu.com/ubuntu noble/main amd64 netbase all 6.4 [13.1 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0706845Z #13 6.646 Get:7 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 tzdata all 2026a-0ubuntu0.24.04.1 [280 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0708064Z #13 6.656 Get:8 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 liblzma5 amd64 5.6.1+really5.4.5-1ubuntu0.3 [127 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0709250Z #13 6.667 Get:9 http://archive.ubuntu.com/ubuntu noble/main amd64 readline-common all 8.2-4build1 [56.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0710355Z #13 6.677 Get:10 http://archive.ubuntu.com/ubuntu noble/main amd64 libreadline8t64 amd64 8.2-4build1 [153 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0711517Z #13 6.688 Get:11 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libsqlite3-0 amd64 3.45.1-1ubuntu2.5 [701 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0713104Z #13 6.707 Get:12 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpython3.12-stdlib amd64 3.12.3-1ubuntu0.13 [2068 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0714380Z #13 6.736 Get:13 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 python3.12 amd64 3.12.3-1ubuntu0.13 [662 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0715793Z #13 6.750 Get:14 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpython3-stdlib amd64 3.12.3-0ubuntu2.1 [10.1 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0717000Z #13 6.764 Get:15 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 python3 amd64 3.12.3-0ubuntu2.1 [23.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0718758Z #13 6.774 Get:16 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libapparmor1 amd64 4.0.1really4.0.1-0ubuntu0.24.04.7 [51.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0720598Z #13 6.789 Get:17 http://archive.ubuntu.com/ubuntu noble/main amd64 libargon2-1 amd64 0~20190702+dfsg-4build1 [20.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0722051Z #13 6.803 Get:18 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libdevmapper1.02.1 amd64 2:1.02.185-3ubuntu3.2 [139 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0723288Z #13 6.819 Get:19 http://archive.ubuntu.com/ubuntu noble/main amd64 libjson-c5 amd64 0.17-1build1 [35.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0724395Z #13 6.832 Get:20 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libcryptsetup12 amd64 2:2.7.0-1ubuntu4.2 [266 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0725765Z #13 6.846 Get:21 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libfdisk1 amd64 2.39.3-9ubuntu6.5 [146 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0726953Z #13 6.860 Get:22 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libkmod2 amd64 31+20240202-2ubuntu7.2 [51.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0728627Z #13 6.875 Get:23 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libsystemd-shared amd64 255.4-1ubuntu8.15 [2076 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0729834Z #13 6.899 Get:24 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 systemd-dev all 255.4-1ubuntu8.15 [106 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0731008Z #13 6.910 Get:25 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 systemd amd64 255.4-1ubuntu8.15 [3475 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0732158Z #13 6.968 Get:26 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 systemd-sysv amd64 255.4-1ubuntu8.15 [11.9 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0733967Z #13 6.969 Get:27 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 perl-modules-5.38 all 5.38.2-3.2ubuntu0.2 [3110 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0736134Z #13 7.004 Get:28 http://archive.ubuntu.com/ubuntu noble/main amd64 libgdbm6t64 amd64 1.23-5.1build1 [34.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0737348Z #13 7.011 Get:29 http://archive.ubuntu.com/ubuntu noble/main amd64 libgdbm-compat4t64 amd64 1.23-5.1build1 [6710 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0738552Z #13 7.019 Get:30 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libperl5.38t64 amd64 5.38.2-3.2ubuntu0.2 [4874 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0739977Z #13 7.072 Get:31 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 perl amd64 5.38.2-3.2ubuntu0.2 [231 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0740993Z #13 7.082 Get:32 http://archive.ubuntu.com/ubuntu noble/main amd64 sgml-base all 1.31 [11.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0742166Z #13 7.094 Get:33 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 python3-pkg-resources all 68.1.2-2ubuntu1.2 [168 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0743927Z #13 7.118 Get:34 http://archive.ubuntu.com/ubuntu noble-updates/universe amd64 supervisor all 4.2.5-1ubuntu0.1 [286 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0745207Z #13 7.128 Get:35 http://archive.ubuntu.com/ubuntu noble/main amd64 adduser all 3.137ubuntu1 [101 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0746237Z #13 7.140 Get:36 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 openssl amd64 3.0.13-0ubuntu3.9 [1002 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0748844Z #13 7.156 Get:37 http://archive.ubuntu.com/ubuntu noble/main amd64 ca-certificates all 20240203 [159 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0750219Z #13 7.165 Get:38 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libdbus-1-3 amd64 1.14.10-4ubuntu4.1 [210 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0751925Z #13 7.178 Get:39 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 dbus-bin amd64 1.14.10-4ubuntu4.1 [39.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0753185Z #13 7.191 Get:40 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 dbus-session-bus-common all 1.14.10-4ubuntu4.1 [80.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0754448Z #13 7.206 Get:41 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 dbus-daemon amd64 1.14.10-4ubuntu4.1 [118 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0756401Z #13 7.218 Get:42 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 dbus-system-bus-common all 1.14.10-4ubuntu4.1 [81.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0757612Z #13 7.231 Get:43 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 dbus amd64 1.14.10-4ubuntu4.1 [24.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0758734Z #13 7.243 Get:44 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 distro-info-data all 0.60ubuntu0.6 [7036 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0760997Z #13 7.257 Get:45 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libglib2.0-0t64 amd64 2.80.0-6ubuntu3.8 [1545 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0762223Z #13 7.279 Get:46 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 gir1.2-glib-2.0 amd64 2.80.0-6ubuntu3.8 [183 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0763375Z #13 7.292 Get:47 http://archive.ubuntu.com/ubuntu noble/main amd64 libgirepository-1.0-1 amd64 1.80.1-1 [81.9 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0764505Z #13 7.308 Get:48 http://archive.ubuntu.com/ubuntu noble/main amd64 gir1.2-girepository-2.0 amd64 1.80.1-1 [24.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0766627Z #13 7.319 Get:49 http://archive.ubuntu.com/ubuntu noble/main amd64 iso-codes all 4.16.0-1 [3492 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0767695Z #13 7.360 Get:50 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libbsd0 amd64 0.12.1-1build1.1 [41.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0768898Z #13 7.370 Get:51 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libcap2-bin amd64 1:2.66-5ubuntu2.4 [34.1 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0770126Z #13 7.381 Get:52 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libelf1t64 amd64 0.190-1.1ubuntu0.1 [57.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0771321Z #13 7.405 Get:53 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libglib2.0-data all 2.80.0-6ubuntu3.8 [49.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0772844Z #13 7.417 Get:54 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libkrb5support0 amd64 1.20.1-6ubuntu2.6 [34.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0774694Z #13 7.426 Get:55 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libk5crypto3 amd64 1.20.1-6ubuntu2.6 [82.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0776075Z #13 7.437 Get:56 http://archive.ubuntu.com/ubuntu noble/main amd64 libkeyutils1 amd64 1.6.3-3build1 [9490 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0777185Z #13 7.448 Get:57 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libkrb5-3 amd64 1.20.1-6ubuntu2.6 [348 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0778597Z #13 7.460 Get:58 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libgssapi-krb5-2 amd64 1.20.1-6ubuntu2.6 [143 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0780871Z #13 7.472 Get:59 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libicu74 amd64 74.2-1ubuntu3.1 [10.9 MB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0783028Z #13 7.592 Get:60 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpam-systemd amd64 255.4-1ubuntu8.15 [235 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0784292Z #13 7.601 Get:61 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libxml2 amd64 2.9.14+dfsg-1.3ubuntu3.7 [764 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0785535Z #13 7.614 Get:62 http://archive.ubuntu.com/ubuntu noble/main amd64 libyaml-0-2 amd64 0.2.5-1build1 [51.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0789002Z #13 7.623 Get:63 http://archive.ubuntu.com/ubuntu noble/main amd64 lsb-release all 12.0-2 [6564 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0791293Z #13 7.633 Get:64 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 python-apt-common all 2.7.7ubuntu5.2 [20.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0792559Z #13 7.642 Get:65 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 python3-apt amd64 2.7.7ubuntu5.2 [169 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0793789Z #13 7.651 Get:66 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-cffi-backend amd64 1.16.0-2build1 [77.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0794917Z #13 7.663 Get:67 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-dbus amd64 1.3.2-5build3 [100 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0796436Z #13 7.676 Get:68 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-gi amd64 3.48.2-1 [232 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0798300Z #13 7.687 Get:69 http://archive.ubuntu.com/ubuntu noble/main amd64 shared-mime-info amd64 2.4-4 [474 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0799430Z #13 7.699 Get:70 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 sudo amd64 1.9.15p5-3ubuntu5.24.04.2 [948 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0800639Z #13 7.714 Get:71 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 vim-common all 2:9.1.0016-1ubuntu7.14 [387 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0802430Z #13 7.729 Get:72 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 xkb-data all 2.41-2ubuntu1.1 [397 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0803646Z #13 7.743 Get:73 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libdrm-common all 2.4.125-1ubuntu0.1~24.04.1 [9174 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0805356Z #13 7.753 Get:74 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libdrm2 amd64 2.4.125-1ubuntu0.1~24.04.1 [41.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0806851Z #13 7.764 Get:75 http://archive.ubuntu.com/ubuntu noble/main amd64 libedit2 amd64 3.1-20230828-1build1 [97.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0807981Z #13 7.774 Get:76 http://archive.ubuntu.com/ubuntu noble/main amd64 libevdev2 amd64 1.13.1+dfsg-1build1 [37.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0809028Z #13 7.787 Get:77 http://archive.ubuntu.com/ubuntu noble/main amd64 libgpm2 amd64 1.20.7-11 [14.1 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0810059Z #13 7.799 Get:78 http://archive.ubuntu.com/ubuntu noble/main amd64 libjansson4 amd64 2.14-2build2 [32.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0811251Z #13 7.810 Get:79 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libnghttp2-14 amd64 1.59.0-1ubuntu0.3 [74.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0812505Z #13 7.822 Get:80 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libnl-3-200 amd64 3.7.0-0.3build1.1 [55.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0814966Z #13 7.833 Get:81 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpng16-16t64 amd64 1.6.43-5ubuntu0.6 [189 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0816893Z #13 7.846 Get:82 http://archive.ubuntu.com/ubuntu noble/main amd64 libpsl5t64 amd64 0.21.2-1.1build1 [57.1 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0818040Z #13 7.860 Get:83 http://archive.ubuntu.com/ubuntu noble/main amd64 libsensors-config all 1:3.6.0-9build1 [5546 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0819152Z #13 7.872 Get:84 http://archive.ubuntu.com/ubuntu noble/main amd64 libsensors5 amd64 1:3.6.0-9build1 [26.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0820200Z #13 7.884 Get:85 http://archive.ubuntu.com/ubuntu noble/main amd64 libxau6 amd64 1:1.0.9-1build6 [7160 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0821562Z #13 7.896 Get:86 http://archive.ubuntu.com/ubuntu noble/main amd64 libxdmcp6 amd64 1:1.1.3-0ubuntu6 [10.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0823638Z #13 7.909 Get:87 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb1 amd64 1.15-1ubuntu2 [47.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0824719Z #13 7.920 Get:88 http://archive.ubuntu.com/ubuntu noble/main amd64 libx11-data all 2:1.8.7-1build1 [115 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0826271Z #13 7.933 Get:89 http://archive.ubuntu.com/ubuntu noble/main amd64 libx11-6 amd64 2:1.8.7-1build1 [650 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0827741Z #13 7.947 Get:90 http://archive.ubuntu.com/ubuntu noble/main amd64 libxext6 amd64 2:1.3.4-1build2 [30.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0828828Z #13 7.959 Get:91 http://archive.ubuntu.com/ubuntu noble/main amd64 libxkbcommon0 amd64 1.6.0-1build1 [122 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0830664Z #13 7.968 Get:92 http://archive.ubuntu.com/ubuntu noble/main amd64 libxmuu1 amd64 2:1.1.3-3build2 [8958 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0832140Z #13 7.978 Get:93 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 nano amd64 7.2-2ubuntu0.2 [282 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0833285Z #13 7.991 Get:94 http://archive.ubuntu.com/ubuntu noble/main amd64 xauth amd64 1:1.1.2-1build1 [25.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0834449Z #13 7.996 Get:95 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 xz-utils amd64 5.6.1+really5.4.5-1ubuntu0.3 [267 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0835927Z #13 8.009 Get:96 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 binutils-common amd64 2.42-4ubuntu2.10 [240 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0837784Z #13 8.019 Get:97 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libsframe1 amd64 2.42-4ubuntu2.10 [15.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0838970Z #13 8.031 Get:98 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libbinutils amd64 2.42-4ubuntu2.10 [577 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0840174Z #13 8.044 Get:99 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libctf-nobfd0 amd64 2.42-4ubuntu2.10 [98.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0841370Z #13 8.055 Get:100 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libctf0 amd64 2.42-4ubuntu2.10 [94.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0842546Z #13 8.066 Get:101 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libgprofng0 amd64 2.42-4ubuntu2.10 [849 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0844072Z #13 8.078 Get:102 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 binutils-x86-64-linux-gnu amd64 2.42-4ubuntu2.10 [2463 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0845567Z #13 8.107 Get:103 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 binutils amd64 2.42-4ubuntu2.10 [18.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0846754Z #13 8.119 Get:104 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libc-dev-bin amd64 2.39-0ubuntu8.7 [20.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0849235Z #13 8.128 Get:105 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 linux-libc-dev amd64 6.8.0-124.124 [1442 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0850449Z #13 8.149 Get:106 http://archive.ubuntu.com/ubuntu noble/main amd64 libcrypt-dev amd64 1:4.4.36-4build1 [112 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0851574Z #13 8.154 Get:107 http://archive.ubuntu.com/ubuntu noble/main amd64 rpcsvc-proto amd64 1.4.2-0ubuntu7 [67.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0853166Z #13 8.169 Get:108 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libc6-dev amd64 2.39-0ubuntu8.7 [2124 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0854472Z #13 8.193 Get:109 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 gcc-13-base amd64 13.3.0-6ubuntu2~24.04.1 [51.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0855941Z #13 8.206 Get:110 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libisl23 amd64 0.26-3build1.1 [680 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0857126Z #13 8.223 Get:111 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libmpfr6 amd64 4.2.1-1build1.1 [353 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0858275Z #13 8.232 Get:112 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libmpc3 amd64 1.3.1-1build1.1 [54.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0859598Z #13 8.241 Get:113 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 cpp-13-x86-64-linux-gnu amd64 13.3.0-6ubuntu2~24.04.1 [10.7 MB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0860921Z #13 8.379 Get:114 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 cpp-13 amd64 13.3.0-6ubuntu2~24.04.1 [1042 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0863465Z #13 8.393 Get:115 http://archive.ubuntu.com/ubuntu noble/main amd64 cpp-x86-64-linux-gnu amd64 4:13.2.0-7ubuntu1 [5326 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0864637Z #13 8.408 Get:116 http://archive.ubuntu.com/ubuntu noble/main amd64 cpp amd64 4:13.2.0-7ubuntu1 [22.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0866496Z #13 8.423 Get:117 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libcc1-0 amd64 14.2.0-4ubuntu2~24.04.1 [48.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0867769Z #13 8.438 Get:118 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libgomp1 amd64 14.2.0-4ubuntu2~24.04.1 [148 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0869331Z #13 8.450 Get:119 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libitm1 amd64 14.2.0-4ubuntu2~24.04.1 [29.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0870552Z #13 8.459 Get:120 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libatomic1 amd64 14.2.0-4ubuntu2~24.04.1 [10.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0871786Z #13 8.469 Get:121 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libasan8 amd64 14.2.0-4ubuntu2~24.04.1 [3027 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0873002Z #13 8.512 Get:122 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 liblsan0 amd64 14.2.0-4ubuntu2~24.04.1 [1322 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0874205Z #13 8.536 Get:123 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libtsan2 amd64 14.2.0-4ubuntu2~24.04.1 [2772 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0875691Z #13 8.562 Get:124 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libubsan1 amd64 14.2.0-4ubuntu2~24.04.1 [1184 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0876944Z #13 8.578 Get:125 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libhwasan0 amd64 14.2.0-4ubuntu2~24.04.1 [1641 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0879320Z #13 8.601 Get:126 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libquadmath0 amd64 14.2.0-4ubuntu2~24.04.1 [153 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0880665Z #13 8.610 Get:127 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libgcc-13-dev amd64 13.3.0-6ubuntu2~24.04.1 [2681 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0882009Z #13 8.643 Get:128 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 gcc-13-x86-64-linux-gnu amd64 13.3.0-6ubuntu2~24.04.1 [21.1 MB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0884557Z #13 8.831 Get:129 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 gcc-13 amd64 13.3.0-6ubuntu2~24.04.1 [494 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0885941Z #13 8.841 Get:130 http://archive.ubuntu.com/ubuntu noble/main amd64 gcc-x86-64-linux-gnu amd64 4:13.2.0-7ubuntu1 [1212 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0887034Z #13 8.851 Get:131 http://archive.ubuntu.com/ubuntu noble/main amd64 gcc amd64 4:13.2.0-7ubuntu1 [5018 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0888233Z #13 8.861 Get:132 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libstdc++-13-dev amd64 13.3.0-6ubuntu2~24.04.1 [2420 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0889948Z #13 8.885 Get:133 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 g++-13-x86-64-linux-gnu amd64 13.3.0-6ubuntu2~24.04.1 [12.2 MB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0891649Z #13 8.986 Get:134 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 g++-13 amd64 13.3.0-6ubuntu2~24.04.1 [16.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0894586Z #13 8.998 Get:135 http://archive.ubuntu.com/ubuntu noble/main amd64 g++-x86-64-linux-gnu amd64 4:13.2.0-7ubuntu1 [964 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0896951Z #13 9.006 Get:136 http://archive.ubuntu.com/ubuntu noble/main amd64 g++ amd64 4:13.2.0-7ubuntu1 [1100 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0897920Z #13 9.017 Get:137 http://archive.ubuntu.com/ubuntu noble/main amd64 make amd64 4.3-4.1build2 [180 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0898945Z #13 9.028 Get:138 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libdpkg-perl all 1.22.6ubuntu6.6 [268 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0900885Z #13 9.037 Get:139 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 bzip2 amd64 1.0.8-5.1build0.1 [34.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0901994Z #13 9.048 Get:140 http://archive.ubuntu.com/ubuntu noble/main amd64 patch amd64 2.7.6-7build3 [104 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0903005Z #13 9.057 Get:141 http://archive.ubuntu.com/ubuntu noble/main amd64 lto-disabled-list all 47 [12.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0904350Z #13 9.068 Get:142 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 dpkg-dev all 1.22.6ubuntu6.6 [1074 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0905710Z #13 9.083 Get:143 http://archive.ubuntu.com/ubuntu noble/main amd64 build-essential amd64 12.10ubuntu1 [4928 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.0906813Z #13 9.096 Get:144 http://archive.ubuntu.com/ubuntu noble/main amd64 libbrotli1 amd64 1.1.0-2build2 [331 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.1535716Z #13 9.106 Get:145 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libsasl2-modules-db amd64 2.1.28+dfsg1-5ubuntu3.1 [20.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.1537726Z #13 9.115 Get:146 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libsasl2-2 amd64 2.1.28+dfsg1-5ubuntu3.1 [53.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.1539584Z #13 9.127 Get:147 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libldap2 amd64 2.6.10+dfsg-0ubuntu0.24.04.1 [198 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.1541910Z #13 9.142 Get:148 http://archive.ubuntu.com/ubuntu noble/main amd64 librtmp1 amd64 2.4+20151223.gitfa8646d.1-2build7 [56.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.1543501Z #13 9.152 Get:149 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libssh-4 amd64 0.10.6-2ubuntu0.4 [190 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.1550430Z #13 9.164 Get:150 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libcurl4t64 amd64 8.5.0-2ubuntu10.9 [342 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.1551950Z #13 9.177 Get:151 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 curl amd64 8.5.0-2ubuntu10.9 [227 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.1555991Z #13 9.188 Get:152 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 gpgconf amd64 2.4.4-2ubuntu17.4 [104 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.1557151Z #13 9.199 Get:153 http://archive.ubuntu.com/ubuntu noble/main amd64 libksba8 amd64 1.6.6-1build1 [122 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.2667555Z #13 9.211 Get:154 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 dirmngr amd64 2.4.4-2ubuntu17.4 [323 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.2669357Z #13 9.224 Get:155 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libfreetype6 amd64 2.13.2+dfsg-1ubuntu0.1 [402 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.2671273Z #13 9.239 Get:156 http://archive.ubuntu.com/ubuntu noble/main amd64 fonts-dejavu-mono all 2.37-8 [502 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.2673441Z #13 9.252 Get:157 http://archive.ubuntu.com/ubuntu noble/main amd64 fonts-dejavu-core all 2.37-8 [835 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.2675676Z #13 9.267 Get:158 http://archive.ubuntu.com/ubuntu noble/main amd64 fontconfig-config amd64 2.15.0-1.1ubuntu2 [37.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.2677277Z #13 9.283 Get:159 http://archive.ubuntu.com/ubuntu noble/main amd64 libfontconfig1 amd64 2.15.0-1.1ubuntu2 [139 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.2679055Z #13 9.297 Get:160 http://archive.ubuntu.com/ubuntu noble/main amd64 fontconfig amd64 2.15.0-1.1ubuntu2 [180 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.2682464Z #13 9.314 Get:161 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpackagekit-glib2-18 amd64 1.2.8-2ubuntu1.5 [120 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.3847480Z #13 9.325 Get:162 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 gir1.2-packagekitglib-1.0 amd64 1.2.8-2ubuntu1.5 [25.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.3849559Z #13 9.336 Get:163 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libcurl3t64-gnutls amd64 8.5.0-2ubuntu10.9 [334 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.3851505Z #13 9.350 Get:164 http://archive.ubuntu.com/ubuntu noble/main amd64 liberror-perl all 0.17029-2 [25.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.3853019Z #13 9.364 Get:165 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 git-man all 1:2.43.0-1ubuntu7.3 [1100 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.3854974Z #13 9.378 Get:166 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 git amd64 1:2.43.0-1ubuntu7.3 [3680 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.3856964Z #13 9.431 Get:167 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 gnupg-utils amd64 2.4.4-2ubuntu17.4 [109 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.4847628Z #13 9.447 Get:168 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 gpg amd64 2.4.4-2ubuntu17.4 [565 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.4855900Z #13 9.462 Get:169 http://archive.ubuntu.com/ubuntu noble/main amd64 pinentry-curses amd64 1.2.1-3ubuntu5 [35.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.4859697Z #13 9.474 Get:170 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 gpg-agent amd64 2.4.4-2ubuntu17.4 [227 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.4861297Z #13 9.486 Get:171 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 gpgsm amd64 2.4.4-2ubuntu17.4 [232 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.4863144Z #13 9.498 Get:172 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 keyboxd amd64 2.4.4-2ubuntu17.4 [78.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.4864687Z #13 9.509 Get:173 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 gnupg all 2.4.4-2ubuntu17.4 [359 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.4866710Z #13 9.521 Get:174 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libnl-genl-3-200 amd64 3.7.0-0.3build1.1 [12.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.4868155Z #13 9.532 Get:175 http://archive.ubuntu.com/ubuntu noble/main amd64 htop amd64 3.3.0-4build1 [171 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.5918907Z #13 9.547 Get:176 http://archive.ubuntu.com/ubuntu noble/main amd64 libonig5 amd64 6.9.9-1build1 [172 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.5920692Z #13 9.555 Get:177 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libjq1 amd64 1.7.1-3ubuntu0.24.04.2 [142 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.5939184Z #13 9.565 Get:178 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 jq amd64 1.7.1-3ubuntu0.24.04.2 [65.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.5940978Z #13 9.577 Get:179 http://archive.ubuntu.com/ubuntu noble/universe amd64 libzip4t64 amd64 1.7.3-1.1ubuntu2 [53.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.5942779Z #13 9.593 Get:180 http://archive.ubuntu.com/ubuntu noble/universe amd64 lib3mf1t64 amd64 1.8.1+ds-4.1build2 [369 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.5944309Z #13 9.606 Get:181 http://archive.ubuntu.com/ubuntu noble/main amd64 libstemmer0d amd64 2.2.0-4build1 [161 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.5946162Z #13 9.617 Get:182 http://archive.ubuntu.com/ubuntu noble/main amd64 libxmlb2 amd64 0.3.18-1 [67.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.5947541Z #13 9.627 Get:183 http://archive.ubuntu.com/ubuntu noble/main amd64 libappstream5 amd64 1.0.2-1build6 [238 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.5949341Z #13 9.639 Get:184 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libasound2-data all 1.2.11-1ubuntu0.2 [21.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.7029041Z #13 9.648 Get:185 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libasound2t64 amd64 1.2.11-1ubuntu0.2 [398 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.7031267Z #13 9.657 Get:186 http://archive.ubuntu.com/ubuntu noble/main amd64 libasyncns0 amd64 0.8-6build4 [11.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.7032651Z #13 9.668 Get:187 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libavahi-common-data amd64 0.8-13ubuntu6.2 [30.1 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.7033684Z #13 9.680 Get:188 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libavahi-common3 amd64 0.8-13ubuntu6.2 [23.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.7034695Z #13 9.690 Get:189 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libavahi-client3 amd64 0.8-13ubuntu6.2 [26.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.7036253Z #13 9.701 Get:190 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libboost-filesystem1.83.0 amd64 1.83.0-2.1ubuntu3.2 [284 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.7040105Z #13 9.716 Get:191 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libboost-program-options1.83.0 amd64 1.83.0-2.1ubuntu3.2 [321 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.7041425Z #13 9.728 Get:192 http://archive.ubuntu.com/ubuntu noble/main amd64 libpixman-1-0 amd64 0.42.2-1build1 [279 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.7042528Z #13 9.739 Get:193 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-render0 amd64 1.15-1ubuntu2 [16.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.7043627Z #13 9.749 Get:194 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-shm0 amd64 1.15-1ubuntu2 [5756 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.8114213Z #13 9.759 Get:195 http://archive.ubuntu.com/ubuntu noble/main amd64 libxrender1 amd64 1:0.9.10-1.1build1 [19.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.8119734Z #13 9.770 Get:196 http://archive.ubuntu.com/ubuntu noble/main amd64 libcairo2 amd64 1.18.0-3build1 [566 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.8120926Z #13 9.787 Get:197 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libcups2t64 amd64 2.4.7-1.2ubuntu7.9 [273 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.8122464Z #13 9.800 Get:198 http://archive.ubuntu.com/ubuntu noble/main amd64 libwayland-client0 amd64 1.22.0-2.1build1 [26.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.8124116Z #13 9.812 Get:199 http://archive.ubuntu.com/ubuntu noble/main amd64 libdecor-0-0 amd64 0.2.2-1build2 [16.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.8125471Z #13 9.824 Get:200 http://archive.ubuntu.com/ubuntu noble/universe amd64 libdouble-conversion3 amd64 3.3.0-1build1 [40.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.8126773Z #13 9.836 Get:201 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libdrm-amdgpu1 amd64 2.4.125-1ubuntu0.1~24.04.1 [21.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.8128066Z #13 9.847 Get:202 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpciaccess0 amd64 0.17-3ubuntu0.24.04.2 [18.9 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.8129347Z #13 9.858 Get:203 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libdrm-intel1 amd64 2.4.125-1ubuntu0.1~24.04.1 [63.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.9977840Z #13 9.870 Get:204 http://archive.ubuntu.com/ubuntu noble/main amd64 libduktape207 amd64 2.7.0+tests-0ubuntu3 [143 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.9979205Z #13 9.880 Get:205 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libdw1t64 amd64 0.190-1.1ubuntu0.1 [261 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:57.9980456Z #13 9.893 Get:206 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libllvm20 amd64 1:20.1.2-0ubuntu1~24.04.2 [30.6 MB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.1580146Z #13 10.21 Get:207 http://archive.ubuntu.com/ubuntu noble/main amd64 libx11-xcb1 amd64 2:1.8.7-1build1 [7800 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.3328766Z #13 10.22 Get:208 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-dri3-0 amd64 1.15-1ubuntu2 [7142 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.3330555Z #13 10.23 Get:209 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-present0 amd64 1.15-1ubuntu2 [5676 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.3332250Z #13 10.24 Get:210 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-randr0 amd64 1.15-1ubuntu2 [17.9 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.3340778Z #13 10.25 Get:211 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-sync1 amd64 1.15-1ubuntu2 [9312 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.3342284Z #13 10.26 Get:212 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-xfixes0 amd64 1.15-1ubuntu2 [10.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.3344183Z #13 10.27 Get:213 http://archive.ubuntu.com/ubuntu noble/main amd64 libxshmfence1 amd64 1.3-1build5 [4764 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.3346011Z #13 10.29 Get:214 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 mesa-libgallium amd64 25.2.8-0ubuntu0.24.04.1 [10.8 MB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.3347496Z #13 10.38 Get:215 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libgbm1 amd64 25.2.8-0ubuntu0.24.04.1 [34.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.4397007Z #13 10.39 Get:216 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libegl-mesa0 amd64 25.2.8-0ubuntu0.24.04.1 [117 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.4400091Z #13 10.40 Get:217 http://archive.ubuntu.com/ubuntu noble/main amd64 libogg0 amd64 1.3.5-3build1 [22.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.4401580Z #13 10.42 Get:218 http://archive.ubuntu.com/ubuntu noble/main amd64 libflac12t64 amd64 1.4.3+ds-2.1ubuntu2 [197 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.4402952Z #13 10.43 Get:219 http://archive.ubuntu.com/ubuntu noble/main amd64 libfontenc1 amd64 1:1.1.8-1build1 [14.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.4404341Z #13 10.45 Get:220 http://archive.ubuntu.com/ubuntu noble/main amd64 libvulkan1 amd64 1.3.275.0-1build1 [142 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.4406064Z #13 10.46 Get:221 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libgl1-mesa-dri amd64 25.2.8-0ubuntu0.24.04.1 [37.9 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.4407440Z #13 10.47 Get:222 http://archive.ubuntu.com/ubuntu noble/main amd64 libglvnd0 amd64 1.7.0-1build1 [69.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.4408688Z #13 10.49 Get:223 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-glx0 amd64 1.15-1ubuntu2 [24.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.5558144Z #13 10.50 Get:224 http://archive.ubuntu.com/ubuntu noble/main amd64 libxxf86vm1 amd64 1:1.1.4-1build4 [9282 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.5559644Z #13 10.51 Get:225 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libglx-mesa0 amd64 25.2.8-0ubuntu0.24.04.1 [110 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.5561584Z #13 10.52 Get:226 http://archive.ubuntu.com/ubuntu noble/main amd64 libglx0 amd64 1.7.0-1build1 [38.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.5562674Z #13 10.53 Get:227 http://archive.ubuntu.com/ubuntu noble/main amd64 libgl1 amd64 1.7.0-1build1 [102 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.5563742Z #13 10.55 Get:228 http://archive.ubuntu.com/ubuntu noble/universe amd64 libglew2.2 amd64 2.2.0-4build1 [187 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.5564959Z #13 10.56 Get:229 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libglib2.0-bin amd64 2.80.0-6ubuntu3.8 [97.9 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.5566471Z #13 10.57 Get:230 http://archive.ubuntu.com/ubuntu noble/main amd64 libgraphite2-3 amd64 1.3.14-2build1 [73.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.5567653Z #13 10.58 Get:231 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libunwind8 amd64 1.6.2-3build1.1 [55.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.5568938Z #13 10.60 Get:232 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libgstreamer1.0-0 amd64 1.24.2-1ubuntu0.1 [1165 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.6650016Z #13 10.62 Get:233 http://archive.ubuntu.com/ubuntu noble/main amd64 libgudev-1.0-0 amd64 1:238-5ubuntu1 [15.9 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.6651526Z #13 10.63 Get:234 http://archive.ubuntu.com/ubuntu noble/main amd64 libharfbuzz0b amd64 8.3.0-2build2 [469 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.6652578Z #13 10.64 Get:235 http://archive.ubuntu.com/ubuntu noble/main amd64 x11-common all 1:7.7+23ubuntu3 [21.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.6653550Z #13 10.65 Get:236 http://archive.ubuntu.com/ubuntu noble/main amd64 libice6 amd64 2:1.0.10-1build3 [41.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.6654762Z #13 10.66 Get:237 http://archive.ubuntu.com/ubuntu noble/main amd64 libwacom-common all 2.10.0-2 [63.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.6656063Z #13 10.67 Get:238 http://archive.ubuntu.com/ubuntu noble/main amd64 libwacom9 amd64 2.10.0-2 [23.9 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.6657263Z #13 10.68 Get:239 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libinput-bin amd64 1.25.0-1ubuntu3.4 [23.1 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.6658559Z #13 10.69 Get:240 http://archive.ubuntu.com/ubuntu noble/main amd64 libmtdev1t64 amd64 1.1.6-1.1build1 [14.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.6660146Z #13 10.70 Get:241 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libinput10 amd64 1.25.0-1ubuntu3.4 [133 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.6661567Z #13 10.71 Get:242 http://archive.ubuntu.com/ubuntu noble/main amd64 libjpeg-turbo8 amd64 2.1.5-2ubuntu2 [150 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.7733642Z #13 10.72 Get:243 http://archive.ubuntu.com/ubuntu noble/main amd64 libjpeg8 amd64 8c-2ubuntu11 [2148 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.7737724Z #13 10.74 Get:244 http://archive.ubuntu.com/ubuntu noble/universe amd64 libmd4c0 amd64 0.4.8-1build1 [42.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.7740121Z #13 10.75 Get:245 http://archive.ubuntu.com/ubuntu noble/main amd64 libmp3lame0 amd64 3.100-6build1 [142 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.7743044Z #13 10.76 Get:246 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libmpg123-0t64 amd64 1.32.5-1ubuntu1.1 [169 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.7746545Z #13 10.78 Get:247 http://archive.ubuntu.com/ubuntu noble/universe amd64 libopencsg1 amd64 1.5.0-1build2 [228 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.7748944Z #13 10.79 Get:248 http://archive.ubuntu.com/ubuntu noble/main amd64 libopus0 amd64 1.4-1build1 [208 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.7751656Z #13 10.80 Get:249 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpcre2-16-0 amd64 10.42-4ubuntu2.1 [210 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.7753029Z #13 10.82 Get:250 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpolkit-gobject-1-0 amd64 124-2ubuntu1.24.04.3 [49.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.8758088Z #13 10.83 Get:251 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpolkit-agent-1-0 amd64 124-2ubuntu1.24.04.3 [17.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.8759773Z #13 10.85 Get:252 http://archive.ubuntu.com/ubuntu noble/main amd64 libvorbis0a amd64 1.3.7-1build3 [97.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.8761272Z #13 10.86 Get:253 http://archive.ubuntu.com/ubuntu noble/main amd64 libvorbisenc2 amd64 1.3.7-1build3 [80.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.8763090Z #13 10.87 Get:254 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libsndfile1 amd64 1.2.2-1ubuntu5.24.04.1 [209 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.8764588Z #13 10.88 Get:255 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpulse0 amd64 1:16.1+dfsg1-2ubuntu10.1 [292 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.8766286Z #13 10.89 Get:256 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libpython3.12t64 amd64 3.12.3-1ubuntu0.13 [2338 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.8767830Z #13 10.92 Get:257 http://archive.ubuntu.com/ubuntu noble/universe amd64 libqscintilla2-qt5-l10n all 2.14.1+dfsg-1build3 [56.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.8769317Z #13 10.92 Get:258 http://archive.ubuntu.com/ubuntu noble/universe amd64 libqt5core5t64 amd64 5.15.13+dfsg-1ubuntu1 [2011 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.9831593Z #13 10.94 Get:259 http://archive.ubuntu.com/ubuntu noble/main amd64 libegl1 amd64 1.7.0-1build1 [28.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.9832864Z #13 10.96 Get:260 http://archive.ubuntu.com/ubuntu noble/universe amd64 libqt5dbus5t64 amd64 5.15.13+dfsg-1ubuntu1 [220 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.9834208Z #13 10.97 Get:261 http://archive.ubuntu.com/ubuntu noble/universe amd64 libqt5network5t64 amd64 5.15.13+dfsg-1ubuntu1 [723 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.9835674Z #13 10.99 Get:262 http://archive.ubuntu.com/ubuntu noble/main amd64 libsm6 amd64 2:1.2.3-1build3 [15.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.9836765Z #13 11.00 Get:263 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-icccm4 amd64 0.4.1-1.1build3 [10.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.9837855Z #13 11.01 Get:264 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-util1 amd64 0.4.0-1build3 [10.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.9838718Z #13 11.02 Get:265 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-image0 amd64 0.4.0-2build1 [10.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:58.9839385Z #13 11.03 Get:266 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-keysyms1 amd64 0.4.0-1build4 [7956 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.0995697Z #13 11.04 Get:267 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-render-util0 amd64 0.3.9-1build4 [9608 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.0998414Z #13 11.05 Get:268 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-shape0 amd64 1.15-1ubuntu2 [6100 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.1001143Z #13 11.06 Get:269 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-xinerama0 amd64 1.15-1ubuntu2 [5410 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.1002761Z #13 11.07 Get:270 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-xinput0 amd64 1.15-1ubuntu2 [33.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.1004977Z #13 11.08 Get:271 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcb-xkb1 amd64 1.15-1ubuntu2 [32.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.1006571Z #13 11.09 Get:272 http://archive.ubuntu.com/ubuntu noble/main amd64 libxkbcommon-x11-0 amd64 1.6.0-1build1 [14.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.1010197Z #13 11.10 Get:273 http://archive.ubuntu.com/ubuntu noble/universe amd64 libqt5gui5t64 amd64 5.15.13+dfsg-1ubuntu1 [3748 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.1013231Z #13 11.15 Get:274 http://archive.ubuntu.com/ubuntu noble/universe amd64 libqt5widgets5t64 amd64 5.15.13+dfsg-1ubuntu1 [2561 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.2046365Z #13 11.18 Get:275 http://archive.ubuntu.com/ubuntu noble/universe amd64 libqt5printsupport5t64 amd64 5.15.13+dfsg-1ubuntu1 [208 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.2050130Z #13 11.19 Get:276 http://archive.ubuntu.com/ubuntu noble/universe amd64 libqscintilla2-qt5-15 amd64 2.14.1+dfsg-1build3 [1154 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.2051670Z #13 11.21 Get:277 http://archive.ubuntu.com/ubuntu noble/main amd64 libsamplerate0 amd64 0.2.2-4build1 [1344 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.2053153Z #13 11.22 Get:278 http://archive.ubuntu.com/ubuntu noble/main amd64 libwayland-cursor0 amd64 1.22.0-2.1build1 [10.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.2054485Z #13 11.23 Get:279 http://archive.ubuntu.com/ubuntu noble/main amd64 libwayland-egl1 amd64 1.22.0-2.1build1 [5628 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.2056225Z #13 11.24 Get:280 http://archive.ubuntu.com/ubuntu noble/main amd64 libxfixes3 amd64 1:6.0.0-2build1 [10.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.2057399Z #13 11.25 Get:281 http://archive.ubuntu.com/ubuntu noble/main amd64 libxcursor1 amd64 1:1.2.1-1build1 [20.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.3144740Z #13 11.26 Get:282 http://archive.ubuntu.com/ubuntu noble/main amd64 libxi6 amd64 2:1.8.1-1build1 [32.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.3147577Z #13 11.27 Get:283 http://archive.ubuntu.com/ubuntu noble/main amd64 libxrandr2 amd64 2:1.5.2-2build1 [19.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.3148930Z #13 11.29 Get:284 http://archive.ubuntu.com/ubuntu noble/main amd64 libxss1 amd64 1:1.2.3-1build3 [7204 B]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.3150385Z #13 11.30 Get:285 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libsdl2-2.0-0 amd64 2.30.0+dfsg-1ubuntu3.1 [686 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.3151845Z #13 11.31 Get:286 http://archive.ubuntu.com/ubuntu noble/universe amd64 libqt5gamepad5 amd64 5.15.13-1 [61.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.3153157Z #13 11.32 Get:287 http://archive.ubuntu.com/ubuntu noble/universe amd64 libqt5multimedia5 amd64 5.15.13-1 [310 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.3154562Z #13 11.34 Get:288 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 libsodium23 amd64 1.0.18-1ubuntu0.24.04.1 [161 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.3156172Z #13 11.35 Get:289 http://archive.ubuntu.com/ubuntu noble/main amd64 libxt6t64 amd64 1:1.2.1-1.2build1 [171 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.3157456Z #13 11.36 Get:290 http://archive.ubuntu.com/ubuntu noble/main amd64 libxmu6 amd64 2:1.1.3-3build2 [47.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.5033798Z #13 11.37 Get:291 http://archive.ubuntu.com/ubuntu noble/main amd64 libxpm4 amd64 1:3.5.17-1build2 [36.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.5046266Z #13 11.38 Get:292 http://archive.ubuntu.com/ubuntu noble/main amd64 libxaw7 amd64 2:1.0.14-1build2 [187 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.5056327Z #13 11.40 Get:293 http://archive.ubuntu.com/ubuntu noble/main amd64 libxfont2 amd64 1:2.0.6-1build1 [93.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.5076312Z #13 11.41 Get:294 http://archive.ubuntu.com/ubuntu noble/main amd64 libxkbfile1 amd64 1:1.1.0-1build4 [70.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.5086233Z #13 11.42 Get:295 http://archive.ubuntu.com/ubuntu noble/main amd64 libopengl0 amd64 1.7.0-1build1 [32.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.5106329Z #13 11.43 Get:296 http://archive.ubuntu.com/ubuntu noble/main amd64 libglu1-mesa amd64 9.0.2-1.1build1 [152 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.5126358Z #13 11.44 Get:297 http://archive.ubuntu.com/ubuntu noble/universe amd64 libspnav0 amd64 1.1-2 [15.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.5136355Z #13 11.45 Get:298 http://archive.ubuntu.com/ubuntu noble/universe amd64 openscad amd64 2021.01-6build4 [3348 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.5146109Z #13 11.52 Get:299 http://archive.ubuntu.com/ubuntu noble/main amd64 xml-core all 0.19 [20.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.5206576Z #13 11.52 Get:300 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 polkitd amd64 124-2ubuntu1.24.04.3 [95.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.6088316Z #13 11.52 Get:301 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-blinker all 1.7.0-1 [14.3 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.6096410Z #13 11.53 Get:302 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 python3-cryptography amd64 41.0.7-4ubuntu0.4 [815 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.6115581Z #13 11.66 Get:303 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-pyparsing all 3.1.1-1 [86.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.7999373Z #13 11.66 Get:304 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-httplib2 all 0.20.4-3 [30.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8019211Z #13 11.66 Get:305 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 python3-jwt all 2.7.0-1ubuntu0.1 [20.2 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8039352Z #13 11.66 Get:306 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-lazr.uri all 1.0.6-3 [13.5 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8055961Z #13 11.67 Get:307 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-wadllib all 1.3.6-5 [35.9 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8076017Z #13 11.67 Get:308 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-distro all 1.9.0-1 [19.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8096165Z #13 11.67 Get:309 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-oauthlib all 3.2.2-1 [89.7 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8098220Z #13 11.67 Get:310 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-lazr.restfulclient all 0.14.6-1 [50.8 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8115941Z #13 11.67 Get:311 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-six all 1.16.0-4 [12.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8144764Z #13 11.68 Get:312 http://archive.ubuntu.com/ubuntu noble/main amd64 python3-launchpadlib all 1.11.0-6 [127 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8156324Z #13 11.69 Get:313 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 python3-software-properties all 0.99.49.4 [30.0 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8175999Z #13 11.70 Get:314 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 packagekit amd64 1.2.8-2ubuntu1.5 [434 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8196198Z #13 11.71 Get:315 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 software-properties-common all 0.99.49.4 [14.4 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8216022Z #13 11.73 Get:316 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 vim-runtime all 2:9.1.0016-1ubuntu7.14 [7283 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.8217495Z #13 11.85 Get:317 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 vim amd64 2:9.1.0016-1ubuntu7.14 [1883 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.9888973Z #13 11.88 Get:318 http://archive.ubuntu.com/ubuntu noble/main amd64 x11-xkb-utils amd64 7.7+8build2 [170 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.9919456Z #13 11.88 Get:319 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 xserver-common all 2:21.1.12-1ubuntu1.5 [34.6 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:58:59.9935942Z #13 11.89 Get:320 http://archive.ubuntu.com/ubuntu noble-updates/universe amd64 xvfb amd64 2:21.1.12-1ubuntu1.5 [877 kB]
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.4696169Z #13 12.52 debconf: delaying package configuration, since apt-utils is not installed
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.5862545Z #13 12.60 Fetched 212 MB in 5s (39.4 MB/s)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.5877054Z #13 12.62 Selecting previously unselected package libpython3.12-minimal:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7156986Z #13 12.62 (Reading database ... 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7157677Z (Reading database ... 5%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7158089Z (Reading database ... 10%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7158441Z (Reading database ... 15%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7172502Z (Reading database ... 20%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7176790Z (Reading database ... 25%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7178911Z (Reading database ... 30%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7179752Z (Reading database ... 35%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7180195Z (Reading database ... 40%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7180619Z (Reading database ... 45%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7181034Z (Reading database ... 50%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7181482Z (Reading database ... 55%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7181901Z (Reading database ... 60%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7182339Z (Reading database ... 65%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7182777Z (Reading database ... 70%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7183213Z (Reading database ... 75%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7183626Z (Reading database ... 80%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7184059Z (Reading database ... 85%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7184478Z (Reading database ... 90%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7184934Z (Reading database ... 95%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7185555Z (Reading database ... 100%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7186156Z (Reading database ... 4381 files and directories currently installed.)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7187103Z #13 12.63 Preparing to unpack .../libpython3.12-minimal_3.12.3-1ubuntu0.13_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7187994Z #13 12.63 Unpacking libpython3.12-minimal:amd64 (3.12.3-1ubuntu0.13) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.7188776Z #13 12.76 Selecting previously unselected package libexpat1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.8496480Z #13 12.77 Preparing to unpack .../libexpat1_2.6.1-2ubuntu0.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.8515958Z #13 12.77 Unpacking libexpat1:amd64 (2.6.1-2ubuntu0.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.8535840Z #13 12.89 Selecting previously unselected package python3.12-minimal.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:00.8551476Z #13 12.89 Preparing to unpack .../python3.12-minimal_3.12.3-1ubuntu0.13_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:01.0078798Z #13 12.90 Unpacking python3.12-minimal (3.12.3-1ubuntu0.13) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:01.0757059Z #13 13.11 Setting up libpython3.12-minimal:amd64 (3.12.3-1ubuntu0.13) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:01.3279776Z #13 13.12 Setting up libexpat1:amd64 (2.6.1-2ubuntu0.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:01.3280898Z #13 13.16 Setting up python3.12-minimal (3.12.3-1ubuntu0.13) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4553172Z #13 15.50 Selecting previously unselected package python3-minimal.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4565791Z #13 15.50 (Reading database ... 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4576324Z (Reading database ... 5%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4595682Z (Reading database ... 10%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4606137Z (Reading database ... 15%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4616905Z (Reading database ... 20%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4635696Z (Reading database ... 25%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4655631Z (Reading database ... 30%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4675643Z (Reading database ... 35%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4685565Z (Reading database ... 40%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4695649Z (Reading database ... 45%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4715582Z (Reading database ... 50%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4735517Z (Reading database ... 55%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4736043Z (Reading database ... 60%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4755644Z (Reading database ... 65%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4775574Z (Reading database ... 70%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4795591Z (Reading database ... 75%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4796209Z (Reading database ... 80%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4815581Z (Reading database ... 85%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4835509Z (Reading database ... 90%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4845592Z (Reading database ... 95%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4855561Z (Reading database ... 100%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4889390Z (Reading database ... 4700 files and directories currently installed.)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.4905894Z #13 15.50 Preparing to unpack .../python3-minimal_3.12.3-0ubuntu2.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.5598860Z #13 15.50 Unpacking python3-minimal (3.12.3-0ubuntu2.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.5610644Z #13 15.60 Selecting previously unselected package media-types.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:03.9493702Z #13 15.99 Preparing to unpack .../media-types_10.1.0_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.1927852Z #13 16.00 Unpacking media-types (10.1.0) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.1955659Z #13 16.05 Selecting previously unselected package netbase.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.1956683Z #13 16.05 Preparing to unpack .../archives/netbase_6.4_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.1975781Z #13 16.06 Unpacking netbase (6.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.1995770Z #13 16.09 Selecting previously unselected package tzdata.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.2015685Z #13 16.09 Preparing to unpack .../tzdata_2026a-0ubuntu0.24.04.1_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.2016675Z #13 16.09 Unpacking tzdata (2026a-0ubuntu0.24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.3809789Z #13 16.33 Preparing to unpack .../liblzma5_5.6.1+really5.4.5-1ubuntu0.3_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.3826942Z #13 16.33 Unpacking liblzma5:amd64 (5.6.1+really5.4.5-1ubuntu0.3) over (5.6.1+really5.4.5-1ubuntu0.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.3855712Z #13 16.39 Setting up liblzma5:amd64 (5.6.1+really5.4.5-1ubuntu0.3) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6141772Z #13 16.43 Selecting previously unselected package readline-common.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6155675Z #13 16.43 (Reading database ... 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6175516Z (Reading database ... 5%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6176271Z (Reading database ... 10%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6195726Z (Reading database ... 15%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6215683Z (Reading database ... 20%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6235711Z (Reading database ... 25%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6236444Z (Reading database ... 30%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6255735Z (Reading database ... 35%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6275526Z (Reading database ... 40%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6295580Z (Reading database ... 45%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6296279Z (Reading database ... 50%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6315694Z (Reading database ... 55%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6335628Z (Reading database ... 60%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6355593Z (Reading database ... 65%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6356222Z (Reading database ... 70%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6375625Z (Reading database ... 75%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6395609Z (Reading database ... 80%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6415499Z (Reading database ... 85%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6416138Z (Reading database ... 90%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6435827Z (Reading database ... 95%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6455590Z (Reading database ... 100%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6456381Z (Reading database ... 5263 files and directories currently installed.)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6475832Z #13 16.47 Preparing to unpack .../0-readline-common_8.2-4build1_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6495723Z #13 16.48 Unpacking readline-common (8.2-4build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.6515778Z #13 16.51 Selecting previously unselected package libreadline8t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.8105683Z #13 16.86 Preparing to unpack .../1-libreadline8t64_8.2-4build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.9131404Z #13 16.95 Adding 'diversion of /lib/x86_64-linux-gnu/libhistory.so.8 to /lib/x86_64-linux-gnu/libhistory.so.8.usr-is-merged by libreadline8t64'
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:04.9134313Z #13 16.96 Adding 'diversion of /lib/x86_64-linux-gnu/libhistory.so.8.2 to /lib/x86_64-linux-gnu/libhistory.so.8.2.usr-is-merged by libreadline8t64'
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.0772110Z #13 16.97 Adding 'diversion of /lib/x86_64-linux-gnu/libreadline.so.8 to /lib/x86_64-linux-gnu/libreadline.so.8.usr-is-merged by libreadline8t64'
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.0773735Z #13 16.97 Adding 'diversion of /lib/x86_64-linux-gnu/libreadline.so.8.2 to /lib/x86_64-linux-gnu/libreadline.so.8.2.usr-is-merged by libreadline8t64'
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.0774839Z #13 16.97 Unpacking libreadline8t64:amd64 (8.2-4build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.3425679Z #13 17.18 Selecting previously unselected package libsqlite3-0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.3426763Z #13 17.19 Preparing to unpack .../2-libsqlite3-0_3.45.1-1ubuntu2.5_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.3427562Z #13 17.19 Unpacking libsqlite3-0:amd64 (3.45.1-1ubuntu2.5) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.3428296Z #13 17.24 Selecting previously unselected package libpython3.12-stdlib:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.3429050Z #13 17.24 Preparing to unpack .../3-libpython3.12-stdlib_3.12.3-1ubuntu0.13_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.3429730Z #13 17.24 Unpacking libpython3.12-stdlib:amd64 (3.12.3-1ubuntu0.13) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.3430325Z #13 17.39 Selecting previously unselected package python3.12.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.5571753Z #13 17.39 Preparing to unpack .../4-python3.12_3.12.3-1ubuntu0.13_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.6430261Z #13 17.39 Unpacking python3.12 (3.12.3-1ubuntu0.13) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.6431016Z #13 17.43 Selecting previously unselected package libpython3-stdlib:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.6432137Z #13 17.43 Preparing to unpack .../5-libpython3-stdlib_3.12.3-0ubuntu2.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.6432908Z #13 17.43 Unpacking libpython3-stdlib:amd64 (3.12.3-0ubuntu2.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.6433545Z #13 17.45 Setting up python3-minimal (3.12.3-0ubuntu2.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.6434123Z #13 17.69 Selecting previously unselected package python3.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7597813Z #13 17.69 (Reading database ... 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7598842Z (Reading database ... 5%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7599252Z (Reading database ... 10%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7599640Z (Reading database ... 15%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7600002Z (Reading database ... 20%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7600361Z (Reading database ... 25%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7601806Z (Reading database ... 30%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7603430Z (Reading database ... 35%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7608573Z (Reading database ... 40%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7608973Z (Reading database ... 45%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7609358Z (Reading database ... 50%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7609740Z (Reading database ... 55%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7611728Z (Reading database ... 60%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7612259Z (Reading database ... 65%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7612615Z (Reading database ... 70%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7612983Z (Reading database ... 75%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7613332Z (Reading database ... 80%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7613981Z (Reading database ... 85%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7614337Z (Reading database ... 90%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7614686Z (Reading database ... 95%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7615395Z (Reading database ... 100%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7615868Z (Reading database ... 5706 files and directories currently installed.)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7617114Z #13 17.71 Preparing to unpack .../00-python3_3.12.3-0ubuntu2.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7617956Z #13 17.72 Unpacking python3 (3.12.3-0ubuntu2.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7621389Z #13 17.76 Selecting previously unselected package libapparmor1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7623928Z #13 17.76 Preparing to unpack .../01-libapparmor1_4.0.1really4.0.1-0ubuntu0.24.04.7_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7628237Z #13 17.76 Unpacking libapparmor1:amd64 (4.0.1really4.0.1-0ubuntu0.24.04.7) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7630620Z #13 17.78 Selecting previously unselected package libargon2-1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7631676Z #13 17.79 Preparing to unpack .../02-libargon2-1_0~20190702+dfsg-4build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7632500Z #13 17.79 Unpacking libargon2-1:amd64 (0~20190702+dfsg-4build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.7633867Z #13 17.81 Selecting previously unselected package libdevmapper1.02.1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8728284Z #13 17.81 Preparing to unpack .../03-libdevmapper1.02.1_2%3a1.02.185-3ubuntu3.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8729527Z #13 17.81 Unpacking libdevmapper1.02.1:amd64 (2:1.02.185-3ubuntu3.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8730345Z #13 17.84 Selecting previously unselected package libjson-c5:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8731237Z #13 17.84 Preparing to unpack .../04-libjson-c5_0.17-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8732781Z #13 17.84 Unpacking libjson-c5:amd64 (0.17-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8733449Z #13 17.86 Selecting previously unselected package libcryptsetup12:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8734342Z #13 17.87 Preparing to unpack .../05-libcryptsetup12_2%3a2.7.0-1ubuntu4.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8735386Z #13 17.87 Unpacking libcryptsetup12:amd64 (2:2.7.0-1ubuntu4.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8736023Z #13 17.90 Selecting previously unselected package libfdisk1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8736711Z #13 17.90 Preparing to unpack .../06-libfdisk1_2.39.3-9ubuntu6.5_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8737475Z #13 17.90 Unpacking libfdisk1:amd64 (2.39.3-9ubuntu6.5) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.8738170Z #13 17.92 Selecting previously unselected package libkmod2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.9970988Z #13 17.92 Preparing to unpack .../07-libkmod2_31+20240202-2ubuntu7.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.9971861Z #13 17.93 Unpacking libkmod2:amd64 (31+20240202-2ubuntu7.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.9972575Z #13 17.95 Selecting previously unselected package libsystemd-shared:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.9973753Z #13 17.95 Preparing to unpack .../08-libsystemd-shared_255.4-1ubuntu8.15_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.9974519Z #13 17.95 Unpacking libsystemd-shared:amd64 (255.4-1ubuntu8.15) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.9975365Z #13 18.01 Selecting previously unselected package systemd-dev.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.9976044Z #13 18.01 Preparing to unpack .../09-systemd-dev_255.4-1ubuntu8.15_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.9976877Z #13 18.01 Unpacking systemd-dev (255.4-1ubuntu8.15) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.9977360Z #13 18.04 Selecting previously unselected package systemd.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:05.9977774Z #13 18.04 Preparing to unpack .../10-systemd_255.4-1ubuntu8.15_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.1650303Z #13 18.06 Unpacking systemd (255.4-1ubuntu8.15) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3613378Z #13 18.31 Setting up libapparmor1:amd64 (4.0.1really4.0.1-0ubuntu0.24.04.7) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3614527Z #13 18.31 Setting up libargon2-1:amd64 (0~20190702+dfsg-4build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3615521Z #13 18.31 Setting up libdevmapper1.02.1:amd64 (2:1.02.185-3ubuntu3.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3616268Z #13 18.32 Setting up libjson-c5:amd64 (0.17-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3616955Z #13 18.32 Setting up libcryptsetup12:amd64 (2:2.7.0-1ubuntu4.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3617633Z #13 18.32 Setting up libfdisk1:amd64 (2.39.3-9ubuntu6.5) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3618288Z #13 18.33 Setting up libkmod2:amd64 (31+20240202-2ubuntu7.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3619015Z #13 18.33 Setting up libsystemd-shared:amd64 (255.4-1ubuntu8.15) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3619720Z #13 18.33 Setting up systemd-dev (255.4-1ubuntu8.15) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3620323Z #13 18.34 Setting up systemd (255.4-1ubuntu8.15) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3621788Z #13 18.35 Created symlink /etc/systemd/system/getty.target.wants/getty@tty1.service → /usr/lib/systemd/system/getty@.service.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3623008Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3623947Z #13 18.36 Created symlink /etc/systemd/system/multi-user.target.wants/remote-fs.target → /usr/lib/systemd/system/remote-fs.target.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3624707Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3634836Z #13 18.36 Created symlink /etc/systemd/system/sysinit.target.wants/systemd-pstore.service → /usr/lib/systemd/system/systemd-pstore.service.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3640242Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3640767Z #13 18.37 Initializing machine ID from random generator.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3641248Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3641955Z #13 18.40 /usr/lib/tmpfiles.d/systemd-network.conf:10: Failed to resolve user 'systemd-network': No such process
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3642595Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3643071Z #13 18.40 /usr/lib/tmpfiles.d/systemd-network.conf:11: Failed to resolve user 'systemd-network': No such process
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3643775Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3644262Z #13 18.40 /usr/lib/tmpfiles.d/systemd-network.conf:12: Failed to resolve user 'systemd-network': No such process
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3644928Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3645602Z #13 18.40 /usr/lib/tmpfiles.d/systemd-network.conf:13: Failed to resolve user 'systemd-network': No such process
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3646269Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3646713Z #13 18.41 /usr/lib/tmpfiles.d/systemd.conf:22: Failed to resolve group 'systemd-journal': No such process
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3647304Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3647737Z #13 18.41 /usr/lib/tmpfiles.d/systemd.conf:23: Failed to resolve group 'systemd-journal': No such process
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.3648313Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4815169Z #13 18.41 /usr/lib/tmpfiles.d/systemd.conf:28: Failed to resolve group 'systemd-journal': No such process
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4816048Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4816665Z #13 18.42 /usr/lib/tmpfiles.d/systemd.conf:29: Failed to resolve group 'systemd-journal': No such process
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4817272Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4817858Z #13 18.42 /usr/lib/tmpfiles.d/systemd.conf:30: Failed to resolve group 'systemd-journal': No such process
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4818590Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4819216Z #13 18.43 Creating group 'systemd-journal' with GID 999.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4819666Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4820267Z #13 18.43 Creating group 'systemd-network' with GID 998.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4820698Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4821229Z #13 18.43 Creating user 'systemd-network' (systemd Network Management) with UID 998 and GID 998.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4821850Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4822098Z #13 18.49 Selecting previously unselected package systemd-sysv.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4822631Z #13 18.49 (Reading database ... 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4823027Z (Reading database ... 5%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4823392Z (Reading database ... 10%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4823726Z (Reading database ... 15%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4824080Z (Reading database ... 20%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4824425Z (Reading database ... 25%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4824771Z (Reading database ... 30%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4825329Z (Reading database ... 35%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4825675Z (Reading database ... 40%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4826013Z (Reading database ... 45%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4826364Z (Reading database ... 50%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4826703Z (Reading database ... 55%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4827054Z (Reading database ... 60%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4827404Z (Reading database ... 65%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4827752Z (Reading database ... 70%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4828107Z (Reading database ... 75%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4828354Z (Reading database ... 80%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4828576Z (Reading database ... 85%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4828797Z (Reading database ... 90%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4829018Z (Reading database ... 95%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4829241Z (Reading database ... 100%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4829867Z (Reading database ... 6756 files and directories currently installed.)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4830661Z #13 18.50 Preparing to unpack .../0-systemd-sysv_255.4-1ubuntu8.15_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4831635Z #13 18.51 Unpacking systemd-sysv (255.4-1ubuntu8.15) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.4832597Z #13 18.53 Selecting previously unselected package perl-modules-5.38.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.6374731Z #13 18.53 Preparing to unpack .../1-perl-modules-5.38_5.38.2-3.2ubuntu0.2_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.6377932Z #13 18.53 Unpacking perl-modules-5.38 (5.38.2-3.2ubuntu0.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.9878773Z #13 18.93 Selecting previously unselected package libgdbm6t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.9881919Z #13 18.99 Preparing to unpack .../2-libgdbm6t64_1.23-5.1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:06.9882860Z #13 19.03 Unpacking libgdbm6t64:amd64 (1.23-5.1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.2265474Z #13 19.09 Selecting previously unselected package libgdbm-compat4t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.2268644Z #13 19.10 Preparing to unpack .../3-libgdbm-compat4t64_1.23-5.1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.2269584Z #13 19.10 Unpacking libgdbm-compat4t64:amd64 (1.23-5.1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.2270402Z #13 19.12 Selecting previously unselected package libperl5.38t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.2271329Z #13 19.12 Preparing to unpack .../4-libperl5.38t64_5.38.2-3.2ubuntu0.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.2272258Z #13 19.12 Unpacking libperl5.38t64:amd64 (5.38.2-3.2ubuntu0.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.3381359Z #13 ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.3383849Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.3384156Z #17 [web-builder 5/7] RUN npm ci
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.3384722Z #17 15.34 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.3385437Z #17 15.34 added 357 packages, and audited 359 packages in 15s
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.4473282Z #17 15.34 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.4475366Z #17 15.34 145 packages are looking for funding
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.4476077Z #17 15.34   run `npm fund` for details
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.4476600Z #17 15.35 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.4477031Z #17 15.35 found 0 vulnerabilities
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.4477535Z #17 15.35 npm notice
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.4478147Z #17 15.35 npm notice New major version of npm available! 10.9.8 -> 11.16.0
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.4479068Z #17 15.35 npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.16.0
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.4480078Z #17 15.35 npm notice To update run: npm install -g npm@11.16.0
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:07.4480665Z #17 15.35 npm notice
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4478422Z #17 DONE 17.5s
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4478910Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4480700Z #13 [stage-1  2/33] RUN apt-get update && apt-get install -y --no-install-recommends     software-properties-common     curl     git     build-essential     ca-certificates     sudo     vim     nano     htop     jq     gnupg     supervisor     openscad     xvfb     && rm -rf /var/lib/apt/lists/*
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4483187Z #13 19.39 Selecting previously unselected package perl.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4484026Z #13 19.39 Preparing to unpack .../5-perl_5.38.2-3.2ubuntu0.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4484903Z #13 19.40 Unpacking perl (5.38.2-3.2ubuntu0.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4485875Z #13 19.43 Selecting previously unselected package sgml-base.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4486614Z #13 19.43 Preparing to unpack .../6-sgml-base_1.31_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4487484Z #13 19.44 Unpacking sgml-base (1.31) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4488229Z #13 19.46 Selecting previously unselected package python3-pkg-resources.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4489237Z #13 19.46 Preparing to unpack .../7-python3-pkg-resources_68.1.2-2ubuntu1.2_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4490186Z #13 19.46 Unpacking python3-pkg-resources (68.1.2-2ubuntu1.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4490988Z #13 19.49 Selecting previously unselected package supervisor.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4491817Z #13 19.50 Preparing to unpack .../8-supervisor_4.2.5-1ubuntu0.1_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4493036Z #13 19.50 Unpacking supervisor (4.2.5-1ubuntu0.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4493763Z #13 19.66 Selecting previously unselected package adduser.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4494831Z #13 19.66 Preparing to unpack .../9-adduser_3.137ubuntu1_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4496712Z #13 19.66 Unpacking adduser (3.137ubuntu1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4515666Z #13 19.75 Setting up adduser (3.137ubuntu1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4516446Z #13 19.93 Selecting previously unselected package openssl.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4517233Z #13 19.93 (Reading database ... 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4518089Z (Reading database ... 5%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4518625Z (Reading database ... 10%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4519147Z (Reading database ... 15%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4519676Z (Reading database ... 20%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4520174Z (Reading database ... 25%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4520688Z (Reading database ... 30%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4521191Z (Reading database ... 35%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4521695Z (Reading database ... 40%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4522209Z (Reading database ... 45%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4522712Z (Reading database ... 50%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4523230Z (Reading database ... 55%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4523862Z (Reading database ... 60%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4524377Z (Reading database ... 65%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4524876Z (Reading database ... 70%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4525565Z (Reading database ... 75%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4526076Z (Reading database ... 80%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4526602Z (Reading database ... 85%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4527105Z (Reading database ... 90%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4527600Z (Reading database ... 95%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4528133Z (Reading database ... 100%
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4528781Z (Reading database ... 9067 files and directories currently installed.)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4529687Z #13 19.95 Preparing to unpack .../000-openssl_3.0.13-0ubuntu3.9_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4530505Z #13 19.99 Unpacking openssl (3.0.13-0ubuntu3.9) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4531276Z #13 20.14 Selecting previously unselected package ca-certificates.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4532137Z #13 20.14 Preparing to unpack .../001-ca-certificates_20240203_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4533155Z #13 20.18 Unpacking ca-certificates (20240203) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4535439Z #13 20.69 Selecting previously unselected package libdbus-1-3:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4536377Z #13 20.69 Preparing to unpack .../002-libdbus-1-3_1.14.10-4ubuntu4.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4537662Z #13 20.69 Unpacking libdbus-1-3:amd64 (1.14.10-4ubuntu4.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4538453Z #13 21.08 Selecting previously unselected package dbus-bin.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4539467Z #13 21.09 Preparing to unpack .../003-dbus-bin_1.14.10-4ubuntu4.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4540110Z #13 21.13 Unpacking dbus-bin (1.14.10-4ubuntu4.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4541165Z #13 21.24 Selecting previously unselected package dbus-session-bus-common.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4541992Z #13 21.24 Preparing to unpack .../004-dbus-session-bus-common_1.14.10-4ubuntu4.1_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4542789Z #13 21.24 Unpacking dbus-session-bus-common (1.14.10-4ubuntu4.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4543428Z #13 21.30 Selecting previously unselected package dbus-daemon.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4544117Z #13 21.30 Preparing to unpack .../005-dbus-daemon_1.14.10-4ubuntu4.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4544774Z #13 21.33 Unpacking dbus-daemon (1.14.10-4ubuntu4.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4545679Z #13 21.38 Selecting previously unselected package dbus-system-bus-common.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4546473Z #13 21.39 Preparing to unpack .../006-dbus-system-bus-common_1.14.10-4ubuntu4.1_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.4547241Z #13 21.43 Unpacking dbus-system-bus-common (1.14.10-4ubuntu4.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.5736254Z #13 21.51 Selecting previously unselected package dbus.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.5737086Z #13 21.51 Preparing to unpack .../007-dbus_1.14.10-4ubuntu4.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.5737661Z #13 21.52 Unpacking dbus (1.14.10-4ubuntu4.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.5738247Z #13 21.54 Selecting previously unselected package distro-info-data.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.5738995Z #13 21.54 Preparing to unpack .../008-distro-info-data_0.60ubuntu0.6_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.5739663Z #13 21.54 Unpacking distro-info-data (0.60ubuntu0.6) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.5740295Z #13 21.56 Selecting previously unselected package libglib2.0-0t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.5741045Z #13 21.56 Preparing to unpack .../009-libglib2.0-0t64_2.80.0-6ubuntu3.8_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.5741764Z #13 21.58 Unpacking libglib2.0-0t64:amd64 (2.80.0-6ubuntu3.8) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.5742419Z #13 21.62 Selecting previously unselected package gir1.2-glib-2.0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7417412Z #13 ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7418108Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7418830Z #18 [web-builder 6/7] COPY apps/web/ apps/web/
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7419641Z #18 DONE 0.3s
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7421899Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7423320Z #13 [stage-1  2/33] RUN apt-get update && apt-get install -y --no-install-recommends     software-properties-common     curl     git     build-essential     ca-certificates     sudo     vim     nano     htop     jq     gnupg     supervisor     openscad     xvfb     && rm -rf /var/lib/apt/lists/*
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7425380Z #13 21.62 Preparing to unpack .../010-gir1.2-glib-2.0_2.80.0-6ubuntu3.8_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7426155Z #13 21.63 Unpacking gir1.2-glib-2.0:amd64 (2.80.0-6ubuntu3.8) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7426929Z #13 21.65 Selecting previously unselected package libgirepository-1.0-1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7427739Z #13 21.65 Preparing to unpack .../011-libgirepository-1.0-1_1.80.1-1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7428459Z #13 21.65 Unpacking libgirepository-1.0-1:amd64 (1.80.1-1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7429180Z #13 21.67 Selecting previously unselected package gir1.2-girepository-2.0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7430576Z #13 21.67 Preparing to unpack .../012-gir1.2-girepository-2.0_1.80.1-1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7431541Z #13 21.67 Unpacking gir1.2-girepository-2.0:amd64 (1.80.1-1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7432163Z #13 21.69 Selecting previously unselected package iso-codes.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7432873Z #13 21.69 Preparing to unpack .../013-iso-codes_4.16.0-1_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.7433435Z #13 21.69 Unpacking iso-codes (4.16.0-1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.8759440Z #13 21.92 Selecting previously unselected package libbsd0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9976379Z #13 21.92 Preparing to unpack .../014-libbsd0_0.12.1-1build1.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9980211Z #13 21.93 Unpacking libbsd0:amd64 (0.12.1-1build1.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9981013Z #13 21.95 Selecting previously unselected package libcap2-bin.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9981803Z #13 21.95 Preparing to unpack .../015-libcap2-bin_1%3a2.66-5ubuntu2.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9982807Z #13 21.95 Unpacking libcap2-bin (1:2.66-5ubuntu2.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9983403Z #13 21.97 Selecting previously unselected package libelf1t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9984113Z #13 21.98 Preparing to unpack .../016-libelf1t64_0.190-1.1ubuntu0.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9984781Z #13 21.98 Unpacking libelf1t64:amd64 (0.190-1.1ubuntu0.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9985588Z #13 22.00 Selecting previously unselected package libglib2.0-data.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9986308Z #13 22.00 Preparing to unpack .../017-libglib2.0-data_2.80.0-6ubuntu3.8_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9987000Z #13 22.00 Unpacking libglib2.0-data (2.80.0-6ubuntu3.8) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9987636Z #13 22.02 Selecting previously unselected package libkrb5support0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9988565Z #13 22.02 Preparing to unpack .../018-libkrb5support0_1.20.1-6ubuntu2.6_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9989294Z #13 22.02 Unpacking libkrb5support0:amd64 (1.20.1-6ubuntu2.6) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:09.9989923Z #13 22.04 Selecting previously unselected package libk5crypto3:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1014347Z #13 22.05 Preparing to unpack .../019-libk5crypto3_1.20.1-6ubuntu2.6_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1018826Z #13 22.05 Unpacking libk5crypto3:amd64 (1.20.1-6ubuntu2.6) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1020069Z #13 22.07 Selecting previously unselected package libkeyutils1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1021048Z #13 22.07 Preparing to unpack .../020-libkeyutils1_1.6.3-3build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1022034Z #13 22.07 Unpacking libkeyutils1:amd64 (1.6.3-3build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1022908Z #13 22.09 Selecting previously unselected package libkrb5-3:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1024025Z #13 22.09 Preparing to unpack .../021-libkrb5-3_1.20.1-6ubuntu2.6_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1024979Z #13 22.09 Unpacking libkrb5-3:amd64 (1.20.1-6ubuntu2.6) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1026426Z #13 22.12 Selecting previously unselected package libgssapi-krb5-2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1027445Z #13 22.12 Preparing to unpack .../022-libgssapi-krb5-2_1.20.1-6ubuntu2.6_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1028425Z #13 22.13 Unpacking libgssapi-krb5-2:amd64 (1.20.1-6ubuntu2.6) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.1029290Z #13 22.15 Selecting previously unselected package libicu74:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.2547832Z #13 22.15 Preparing to unpack .../023-libicu74_74.2-1ubuntu3.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.2550218Z #13 22.15 Unpacking libicu74:amd64 (74.2-1ubuntu3.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.3410426Z #13 22.39 Selecting previously unselected package libpam-systemd:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.4459473Z #13 22.39 Preparing to unpack .../024-libpam-systemd_255.4-1ubuntu8.15_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.4462644Z #13 22.39 Unpacking libpam-systemd:amd64 (255.4-1ubuntu8.15) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.4463692Z #13 22.43 Selecting previously unselected package libxml2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.4464691Z #13 22.43 Preparing to unpack .../025-libxml2_2.9.14+dfsg-1.3ubuntu3.7_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.4465935Z #13 22.44 Unpacking libxml2:amd64 (2.9.14+dfsg-1.3ubuntu3.7) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.4466825Z #13 22.47 Selecting previously unselected package libyaml-0-2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.4467762Z #13 22.47 Preparing to unpack .../026-libyaml-0-2_0.2.5-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.4468641Z #13 22.48 Unpacking libyaml-0-2:amd64 (0.2.5-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.4469442Z #13 22.49 Selecting previously unselected package lsb-release.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5574092Z #13 22.50 Preparing to unpack .../027-lsb-release_12.0-2_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5578688Z #13 22.50 Unpacking lsb-release (12.0-2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5579720Z #13 22.52 Selecting previously unselected package python-apt-common.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5580797Z #13 22.52 Preparing to unpack .../028-python-apt-common_2.7.7ubuntu5.2_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5581746Z #13 22.52 Unpacking python-apt-common (2.7.7ubuntu5.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5582625Z #13 22.54 Selecting previously unselected package python3-apt.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5583554Z #13 22.55 Preparing to unpack .../029-python3-apt_2.7.7ubuntu5.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5584873Z #13 22.55 Unpacking python3-apt (2.7.7ubuntu5.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5585916Z #13 22.58 Selecting previously unselected package python3-cffi-backend:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5586945Z #13 22.58 Preparing to unpack .../030-python3-cffi-backend_1.16.0-2build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5587914Z #13 22.58 Unpacking python3-cffi-backend:amd64 (1.16.0-2build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.5588777Z #13 22.60 Selecting previously unselected package python3-dbus.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.6864530Z #13 22.61 Preparing to unpack .../031-python3-dbus_1.3.2-5build3_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.6867678Z #13 22.61 Unpacking python3-dbus (1.3.2-5build3) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.6868658Z #13 22.65 Selecting previously unselected package python3-gi.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.6869589Z #13 22.65 Preparing to unpack .../032-python3-gi_3.48.2-1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.6870389Z #13 22.65 Unpacking python3-gi (3.48.2-1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.6871139Z #13 22.68 Selecting previously unselected package shared-mime-info.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.6871987Z #13 22.69 Preparing to unpack .../033-shared-mime-info_2.4-4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.6872764Z #13 22.69 Unpacking shared-mime-info (2.4-4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.8852148Z #13 22.73 Selecting previously unselected package sudo.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.8856574Z #13 22.74 Preparing to unpack .../034-sudo_1.9.15p5-3ubuntu5.24.04.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.8857576Z #13 22.74 Unpacking sudo (1.9.15p5-3ubuntu5.24.04.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.8858347Z #13 22.79 Selecting previously unselected package vim-common.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.8859217Z #13 22.79 Preparing to unpack .../035-vim-common_2%3a9.1.0016-1ubuntu7.14_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.8860049Z #13 22.79 Unpacking vim-common (2:9.1.0016-1ubuntu7.14) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.8860758Z #13 22.83 Selecting previously unselected package xkb-data.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.8861847Z #13 22.83 Preparing to unpack .../036-xkb-data_2.41-2ubuntu1.1_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.8862652Z #13 22.83 Unpacking xkb-data (2.41-2ubuntu1.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.8863338Z #13 22.93 Selecting previously unselected package libdrm-common.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.9862735Z #13 22.94 Preparing to unpack .../037-libdrm-common_2.4.125-1ubuntu0.1~24.04.1_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.9866493Z #13 22.94 Unpacking libdrm-common (2.4.125-1ubuntu0.1~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.9867661Z #13 22.97 Selecting previously unselected package libdrm2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.9868665Z #13 22.97 Preparing to unpack .../038-libdrm2_2.4.125-1ubuntu0.1~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.9869629Z #13 22.98 Unpacking libdrm2:amd64 (2.4.125-1ubuntu0.1~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.9870492Z #13 23.01 Selecting previously unselected package libedit2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.9871445Z #13 23.01 Preparing to unpack .../039-libedit2_3.1-20230828-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.9872373Z #13 23.01 Unpacking libedit2:amd64 (3.1-20230828-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.9873225Z #13 23.03 Selecting previously unselected package libevdev2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.9874160Z #13 23.03 Preparing to unpack .../040-libevdev2_1.13.1+dfsg-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:10.9875265Z #13 23.03 Unpacking libevdev2:amd64 (1.13.1+dfsg-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0974492Z #13 23.05 Selecting previously unselected package libgpm2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0978367Z #13 23.06 Preparing to unpack .../041-libgpm2_1.20.7-11_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0979394Z #13 23.06 Unpacking libgpm2:amd64 (1.20.7-11) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0980235Z #13 23.08 Selecting previously unselected package libjansson4:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0981180Z #13 23.08 Preparing to unpack .../042-libjansson4_2.14-2build2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0982072Z #13 23.08 Unpacking libjansson4:amd64 (2.14-2build2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0982931Z #13 23.10 Selecting previously unselected package libnghttp2-14:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0983973Z #13 23.10 Preparing to unpack .../043-libnghttp2-14_1.59.0-1ubuntu0.3_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0985626Z #13 23.10 Unpacking libnghttp2-14:amd64 (1.59.0-1ubuntu0.3) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0986552Z #13 23.12 Selecting previously unselected package libnl-3-200:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0987492Z #13 23.12 Preparing to unpack .../044-libnl-3-200_3.7.0-0.3build1.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0988465Z #13 23.13 Unpacking libnl-3-200:amd64 (3.7.0-0.3build1.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.0989327Z #13 23.14 Selecting previously unselected package libpng16-16t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.1975344Z #13 23.15 Preparing to unpack .../045-libpng16-16t64_1.6.43-5ubuntu0.6_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.1978843Z #13 23.15 Unpacking libpng16-16t64:amd64 (1.6.43-5ubuntu0.6) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.1979872Z #13 23.17 Selecting previously unselected package libpsl5t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.1980874Z #13 23.18 Preparing to unpack .../046-libpsl5t64_0.21.2-1.1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.1981901Z #13 23.18 Unpacking libpsl5t64:amd64 (0.21.2-1.1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.1982773Z #13 23.20 Selecting previously unselected package libsensors-config.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.1983785Z #13 23.21 Preparing to unpack .../047-libsensors-config_1%3a3.6.0-9build1_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.1984749Z #13 23.21 Unpacking libsensors-config (1:3.6.0-9build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.1985871Z #13 23.24 Selecting previously unselected package libsensors5:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.1986860Z #13 23.24 Preparing to unpack .../048-libsensors5_1%3a3.6.0-9build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.1987796Z #13 23.25 Unpacking libsensors5:amd64 (1:3.6.0-9build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.3202050Z #13 23.27 Selecting previously unselected package libxau6:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.3205302Z #13 23.27 Preparing to unpack .../049-libxau6_1%3a1.0.9-1build6_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.3206410Z #13 23.28 Unpacking libxau6:amd64 (1:1.0.9-1build6) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.3207654Z #13 23.30 Selecting previously unselected package libxdmcp6:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.3208623Z #13 23.30 Preparing to unpack .../050-libxdmcp6_1%3a1.1.3-0ubuntu6_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.3209553Z #13 23.30 Unpacking libxdmcp6:amd64 (1:1.1.3-0ubuntu6) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.3210381Z #13 23.33 Selecting previously unselected package libxcb1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.3211280Z #13 23.34 Preparing to unpack .../051-libxcb1_1.15-1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.4230048Z #13 23.34 Unpacking libxcb1:amd64 (1.15-1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.4232405Z #13 23.37 Selecting previously unselected package libx11-data.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.4233299Z #13 23.38 Preparing to unpack .../052-libx11-data_2%3a1.8.7-1build1_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.4234005Z #13 23.38 Unpacking libx11-data (2:1.8.7-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.4234653Z #13 23.46 Selecting previously unselected package libx11-6:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.4235754Z #13 23.47 Preparing to unpack .../053-libx11-6_2%3a1.8.7-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.5272601Z #13 23.47 Unpacking libx11-6:amd64 (2:1.8.7-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.5273519Z #13 23.51 Selecting previously unselected package libxext6:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.5274286Z #13 23.51 Preparing to unpack .../054-libxext6_2%3a1.3.4-1build2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.5275266Z #13 23.51 Unpacking libxext6:amd64 (2:1.3.4-1build2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.5275994Z #13 23.55 Selecting previously unselected package libxkbcommon0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.5276749Z #13 23.55 Preparing to unpack .../055-libxkbcommon0_1.6.0-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.5277444Z #13 23.55 Unpacking libxkbcommon0:amd64 (1.6.0-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.5278095Z #13 23.57 Selecting previously unselected package libxmuu1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.6298115Z #13 23.58 Preparing to unpack .../056-libxmuu1_2%3a1.1.3-3build2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.6299244Z #13 23.58 Unpacking libxmuu1:amd64 (2:1.1.3-3build2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.6300018Z #13 23.60 Selecting previously unselected package nano.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.6300801Z #13 23.61 Preparing to unpack .../057-nano_7.2-2ubuntu0.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.6303777Z #13 23.61 Unpacking nano (7.2-2ubuntu0.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.6315676Z #13 23.65 Selecting previously unselected package xauth.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.6316551Z #13 23.65 Preparing to unpack .../058-xauth_1%3a1.1.2-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.6317398Z #13 23.65 Unpacking xauth (1:1.1.2-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.6318093Z #13 23.67 Selecting previously unselected package xz-utils.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.6318970Z #13 23.68 Preparing to unpack .../059-xz-utils_5.6.1+really5.4.5-1ubuntu0.3_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.7429265Z #13 23.68 Unpacking xz-utils (5.6.1+really5.4.5-1ubuntu0.3) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.7430260Z #13 23.72 Selecting previously unselected package binutils-common:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.7431140Z #13 23.72 Preparing to unpack .../060-binutils-common_2.42-4ubuntu2.10_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.7431979Z #13 23.72 Unpacking binutils-common:amd64 (2.42-4ubuntu2.10) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.7432692Z #13 23.76 Selecting previously unselected package libsframe1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.7433462Z #13 23.76 Preparing to unpack .../061-libsframe1_2.42-4ubuntu2.10_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.7434168Z #13 23.76 Unpacking libsframe1:amd64 (2.42-4ubuntu2.10) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.7436028Z #13 23.79 Selecting previously unselected package libbinutils:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.8469513Z #13 23.79 Preparing to unpack .../062-libbinutils_2.42-4ubuntu2.10_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.8472541Z #13 23.80 Unpacking libbinutils:amd64 (2.42-4ubuntu2.10) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.8473615Z #13 23.84 Selecting previously unselected package libctf-nobfd0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.8475867Z #13 23.84 Preparing to unpack .../063-libctf-nobfd0_2.42-4ubuntu2.10_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.8478003Z #13 23.84 Unpacking libctf-nobfd0:amd64 (2.42-4ubuntu2.10) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.8479823Z #13 23.86 Selecting previously unselected package libctf0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.8483083Z #13 23.87 Preparing to unpack .../064-libctf0_2.42-4ubuntu2.10_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.8485293Z #13 23.87 Unpacking libctf0:amd64 (2.42-4ubuntu2.10) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.8487290Z #13 23.89 Selecting previously unselected package libgprofng0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.8488992Z #13 23.89 Preparing to unpack .../065-libgprofng0_2.42-4ubuntu2.10_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:11.8491013Z #13 23.89 Unpacking libgprofng0:amd64 (2.42-4ubuntu2.10) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.0066743Z #13 23.93 Selecting previously unselected package binutils-x86-64-linux-gnu.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.0068010Z #13 23.94 Preparing to unpack .../066-binutils-x86-64-linux-gnu_2.42-4ubuntu2.10_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.0069023Z #13 23.94 Unpacking binutils-x86-64-linux-gnu (2.42-4ubuntu2.10) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.0069772Z #13 24.05 Selecting previously unselected package binutils.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.2230040Z #13 24.06 Preparing to unpack .../067-binutils_2.42-4ubuntu2.10_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.2232695Z #13 24.06 Unpacking binutils (2.42-4ubuntu2.10) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.2233634Z #13 24.09 Selecting previously unselected package libc-dev-bin.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.2234576Z #13 24.09 Preparing to unpack .../068-libc-dev-bin_2.39-0ubuntu8.7_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.2235689Z #13 24.10 Unpacking libc-dev-bin (2.39-0ubuntu8.7) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.2236524Z #13 24.11 Selecting previously unselected package linux-libc-dev:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.2237471Z #13 24.12 Preparing to unpack .../069-linux-libc-dev_6.8.0-124.124_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.2238337Z #13 24.12 Unpacking linux-libc-dev:amd64 (6.8.0-124.124) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.3455603Z #13 24.39 Selecting previously unselected package libcrypt-dev:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.5778501Z #13 24.40 Preparing to unpack .../070-libcrypt-dev_1%3a4.4.36-4build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.5781067Z #13 24.41 Unpacking libcrypt-dev:amd64 (1:4.4.36-4build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.5782074Z #13 24.43 Selecting previously unselected package rpcsvc-proto.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.5783024Z #13 24.43 Preparing to unpack .../071-rpcsvc-proto_1.4.2-0ubuntu7_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.5784290Z #13 24.44 Unpacking rpcsvc-proto (1.4.2-0ubuntu7) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.5785560Z #13 24.47 Selecting previously unselected package libc6-dev:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.5786553Z #13 24.47 Preparing to unpack .../072-libc6-dev_2.39-0ubuntu8.7_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.5787435Z #13 24.47 Unpacking libc6-dev:amd64 (2.39-0ubuntu8.7) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.6306190Z #13 24.68 Selecting previously unselected package gcc-13-base:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.7605950Z #13 24.68 Preparing to unpack .../073-gcc-13-base_13.3.0-6ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.7609421Z #13 24.68 Unpacking gcc-13-base:amd64 (13.3.0-6ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.7610470Z #13 24.71 Selecting previously unselected package libisl23:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.7611403Z #13 24.72 Preparing to unpack .../074-libisl23_0.26-3build1.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.7612316Z #13 24.72 Unpacking libisl23:amd64 (0.26-3build1.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.7613145Z #13 24.77 Selecting previously unselected package libmpfr6:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.7614038Z #13 24.77 Preparing to unpack .../075-libmpfr6_4.2.1-1build1.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.7614934Z #13 24.77 Unpacking libmpfr6:amd64 (4.2.1-1build1.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.7615917Z #13 24.81 Selecting previously unselected package libmpc3:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.9504541Z #13 24.81 Preparing to unpack .../076-libmpc3_1.3.1-1build1.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.9507286Z #13 24.81 Unpacking libmpc3:amd64 (1.3.1-1build1.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.9508299Z #13 24.84 Selecting previously unselected package cpp-13-x86-64-linux-gnu.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.9509443Z #13 24.84 Preparing to unpack .../077-cpp-13-x86-64-linux-gnu_13.3.0-6ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:12.9510536Z #13 24.85 Unpacking cpp-13-x86-64-linux-gnu (13.3.0-6ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.0137295Z #13 25.06 Selecting previously unselected package cpp-13.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.1210111Z #13 25.07 Preparing to unpack .../078-cpp-13_13.3.0-6ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.1213518Z #13 25.07 Unpacking cpp-13 (13.3.0-6ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.1214529Z #13 25.10 Selecting previously unselected package cpp-x86-64-linux-gnu.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.1216254Z #13 25.10 Preparing to unpack .../079-cpp-x86-64-linux-gnu_4%3a13.2.0-7ubuntu1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.1217310Z #13 25.10 Unpacking cpp-x86-64-linux-gnu (4:13.2.0-7ubuntu1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.1218222Z #13 25.14 Selecting previously unselected package cpp.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.1219174Z #13 25.14 Preparing to unpack .../080-cpp_4%3a13.2.0-7ubuntu1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.1219998Z #13 25.15 Unpacking cpp (4:13.2.0-7ubuntu1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.2290455Z #13 25.17 Selecting previously unselected package libcc1-0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.2294243Z #13 25.17 Preparing to unpack .../081-libcc1-0_14.2.0-4ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.2295670Z #13 25.18 Unpacking libcc1-0:amd64 (14.2.0-4ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.2296542Z #13 25.20 Selecting previously unselected package libgomp1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.2297476Z #13 25.20 Preparing to unpack .../082-libgomp1_14.2.0-4ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.2298393Z #13 25.20 Unpacking libgomp1:amd64 (14.2.0-4ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.2299211Z #13 25.23 Selecting previously unselected package libitm1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.2300099Z #13 25.24 Preparing to unpack .../083-libitm1_14.2.0-4ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.2300962Z #13 25.24 Unpacking libitm1:amd64 (14.2.0-4ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.2301784Z #13 25.28 Selecting previously unselected package libatomic1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.3561733Z #13 25.28 Preparing to unpack .../084-libatomic1_14.2.0-4ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.3564302Z #13 25.28 Unpacking libatomic1:amd64 (14.2.0-4ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.3565559Z #13 25.30 Selecting previously unselected package libasan8:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.3566878Z #13 25.31 Preparing to unpack .../085-libasan8_14.2.0-4ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.3567797Z #13 25.31 Unpacking libasan8:amd64 (14.2.0-4ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.3568648Z #13 25.40 Selecting previously unselected package liblsan0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.4939352Z #13 25.41 Preparing to unpack .../086-liblsan0_14.2.0-4ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.4941740Z #13 25.41 Unpacking liblsan0:amd64 (14.2.0-4ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.4942704Z #13 25.46 Selecting previously unselected package libtsan2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.4943728Z #13 25.46 Preparing to unpack .../087-libtsan2_14.2.0-4ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.4944711Z #13 25.47 Unpacking libtsan2:amd64 (14.2.0-4ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.6058732Z #13 25.54 Selecting previously unselected package libubsan1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.6061554Z #13 25.55 Preparing to unpack .../088-libubsan1_14.2.0-4ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.6062813Z #13 25.55 Unpacking libubsan1:amd64 (14.2.0-4ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.6063782Z #13 25.59 Selecting previously unselected package libhwasan0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.6064822Z #13 25.60 Preparing to unpack .../089-libhwasan0_14.2.0-4ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.6066061Z #13 25.60 Unpacking libhwasan0:amd64 (14.2.0-4ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.6067130Z #13 25.65 Selecting previously unselected package libquadmath0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.7972379Z #13 25.66 Preparing to unpack .../090-libquadmath0_14.2.0-4ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.7975486Z #13 25.66 Unpacking libquadmath0:amd64 (14.2.0-4ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.7976376Z #13 25.69 Selecting previously unselected package libgcc-13-dev:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.7977249Z #13 25.69 Preparing to unpack .../091-libgcc-13-dev_13.3.0-6ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.7978440Z #13 25.70 Unpacking libgcc-13-dev:amd64 (13.3.0-6ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.7979250Z #13 25.84 Selecting previously unselected package gcc-13-x86-64-linux-gnu.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.9529554Z #13 25.85 Preparing to unpack .../092-gcc-13-x86-64-linux-gnu_13.3.0-6ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:13.9532571Z #13 25.85 Unpacking gcc-13-x86-64-linux-gnu (13.3.0-6ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.1997495Z #13 26.25 Selecting previously unselected package gcc-13.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.3066399Z #13 26.25 Preparing to unpack .../093-gcc-13_13.3.0-6ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.3069114Z #13 26.25 Unpacking gcc-13 (13.3.0-6ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.3070017Z #13 26.29 Selecting previously unselected package gcc-x86-64-linux-gnu.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.3071024Z #13 26.29 Preparing to unpack .../094-gcc-x86-64-linux-gnu_4%3a13.2.0-7ubuntu1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.3071926Z #13 26.29 Unpacking gcc-x86-64-linux-gnu (4:13.2.0-7ubuntu1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.3072707Z #13 26.32 Selecting previously unselected package gcc.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.3073578Z #13 26.32 Preparing to unpack .../095-gcc_4%3a13.2.0-7ubuntu1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.3074386Z #13 26.33 Unpacking gcc (4:13.2.0-7ubuntu1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.3076157Z #13 26.35 Selecting previously unselected package libstdc++-13-dev:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.4639991Z #13 26.36 Preparing to unpack .../096-libstdc++-13-dev_13.3.0-6ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.4642518Z #13 26.36 Unpacking libstdc++-13-dev:amd64 (13.3.0-6ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.6033871Z #13 26.65 Selecting previously unselected package g++-13-x86-64-linux-gnu.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.7606053Z #13 26.65 Preparing to unpack .../097-g++-13-x86-64-linux-gnu_13.3.0-6ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.7608635Z #13 26.66 Unpacking g++-13-x86-64-linux-gnu (13.3.0-6ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.8592722Z #13 26.91 Selecting previously unselected package g++-13.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.9717309Z #13 26.91 Preparing to unpack .../098-g++-13_13.3.0-6ubuntu2~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.9720232Z #13 26.91 Unpacking g++-13 (13.3.0-6ubuntu2~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.9721286Z #13 26.93 Selecting previously unselected package g++-x86-64-linux-gnu.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.9722349Z #13 26.94 Preparing to unpack .../099-g++-x86-64-linux-gnu_4%3a13.2.0-7ubuntu1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.9723343Z #13 26.94 Unpacking g++-x86-64-linux-gnu (4:13.2.0-7ubuntu1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.9724163Z #13 26.97 Selecting previously unselected package g++.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.9725280Z #13 26.98 Preparing to unpack .../100-g++_4%3a13.2.0-7ubuntu1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.9726185Z #13 26.98 Unpacking g++ (4:13.2.0-7ubuntu1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:14.9726928Z #13 27.02 Selecting previously unselected package make.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.0726263Z #13 27.03 Preparing to unpack .../101-make_4.3-4.1build2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.0729199Z #13 27.03 Unpacking make (4.3-4.1build2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.0729910Z #13 27.06 Selecting previously unselected package libdpkg-perl.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.0730744Z #13 27.07 Preparing to unpack .../102-libdpkg-perl_1.22.6ubuntu6.6_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.0731544Z #13 27.07 Unpacking libdpkg-perl (1.22.6ubuntu6.6) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.0732187Z #13 27.12 Selecting previously unselected package bzip2.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.1783887Z #13 27.13 Preparing to unpack .../103-bzip2_1.0.8-5.1build0.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.1786832Z #13 27.13 Unpacking bzip2 (1.0.8-5.1build0.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.1787729Z #13 27.15 Selecting previously unselected package patch.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.1788614Z #13 27.16 Preparing to unpack .../104-patch_2.7.6-7build3_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.1789454Z #13 27.16 Unpacking patch (2.7.6-7build3) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.1790251Z #13 27.19 Selecting previously unselected package lto-disabled-list.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.1791535Z #13 27.19 Preparing to unpack .../105-lto-disabled-list_47_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.1792352Z #13 27.19 Unpacking lto-disabled-list (47) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.1793126Z #13 27.22 Selecting previously unselected package dpkg-dev.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.3014568Z #13 27.23 Preparing to unpack .../106-dpkg-dev_1.22.6ubuntu6.6_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.3018479Z #13 27.25 Unpacking dpkg-dev (1.22.6ubuntu6.6) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.3019458Z #13 27.32 Selecting previously unselected package build-essential.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.3020619Z #13 27.32 Preparing to unpack .../107-build-essential_12.10ubuntu1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.3021530Z #13 27.33 Unpacking build-essential (12.10ubuntu1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.3022386Z #13 27.35 Selecting previously unselected package libbrotli1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.4046315Z #13 27.35 Preparing to unpack .../108-libbrotli1_1.1.0-2build2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.4049435Z #13 27.36 Unpacking libbrotli1:amd64 (1.1.0-2build2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.4050495Z #13 27.39 Selecting previously unselected package libsasl2-modules-db:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.4051607Z #13 27.39 Preparing to unpack .../109-libsasl2-modules-db_2.1.28+dfsg1-5ubuntu3.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.4052686Z #13 27.39 Unpacking libsasl2-modules-db:amd64 (2.1.28+dfsg1-5ubuntu3.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.4053591Z #13 27.42 Selecting previously unselected package libsasl2-2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.4054510Z #13 27.42 Preparing to unpack .../110-libsasl2-2_2.1.28+dfsg1-5ubuntu3.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.4055630Z #13 27.42 Unpacking libsasl2-2:amd64 (2.1.28+dfsg1-5ubuntu3.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.4056457Z #13 27.45 Selecting previously unselected package libldap2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5162630Z #13 27.46 Preparing to unpack .../111-libldap2_2.6.10+dfsg-0ubuntu0.24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5165730Z #13 27.46 Unpacking libldap2:amd64 (2.6.10+dfsg-0ubuntu0.24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5166752Z #13 27.48 Selecting previously unselected package librtmp1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5167756Z #13 27.49 Preparing to unpack .../112-librtmp1_2.4+20151223.gitfa8646d.1-2build7_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5169076Z #13 27.49 Unpacking librtmp1:amd64 (2.4+20151223.gitfa8646d.1-2build7) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5169911Z #13 27.51 Selecting previously unselected package libssh-4:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5170744Z #13 27.51 Preparing to unpack .../113-libssh-4_0.10.6-2ubuntu0.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5171533Z #13 27.51 Unpacking libssh-4:amd64 (0.10.6-2ubuntu0.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5172298Z #13 27.54 Selecting previously unselected package libcurl4t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5173158Z #13 27.54 Preparing to unpack .../114-libcurl4t64_8.5.0-2ubuntu10.9_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5174003Z #13 27.54 Unpacking libcurl4t64:amd64 (8.5.0-2ubuntu10.9) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.5174705Z #13 27.56 Selecting previously unselected package curl.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6346591Z #13 27.57 Preparing to unpack .../115-curl_8.5.0-2ubuntu10.9_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6349830Z #13 27.57 Unpacking curl (8.5.0-2ubuntu10.9) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6350695Z #13 27.59 Selecting previously unselected package gpgconf.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6351543Z #13 27.59 Preparing to unpack .../116-gpgconf_2.4.4-2ubuntu17.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6352329Z #13 27.59 Unpacking gpgconf (2.4.4-2ubuntu17.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6353066Z #13 27.62 Selecting previously unselected package libksba8:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6353875Z #13 27.62 Preparing to unpack .../117-libksba8_1.6.6-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6354624Z #13 27.62 Unpacking libksba8:amd64 (1.6.6-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6355872Z #13 27.64 Selecting previously unselected package dirmngr.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6356648Z #13 27.64 Preparing to unpack .../118-dirmngr_2.4.4-2ubuntu17.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6357400Z #13 27.66 Unpacking dirmngr (2.4.4-2ubuntu17.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.6358135Z #13 27.68 Selecting previously unselected package libfreetype6:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.7458221Z #13 27.69 Preparing to unpack .../119-libfreetype6_2.13.2+dfsg-1ubuntu0.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.7461303Z #13 27.69 Unpacking libfreetype6:amd64 (2.13.2+dfsg-1ubuntu0.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.7462517Z #13 27.72 Selecting previously unselected package fonts-dejavu-mono.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.7463481Z #13 27.72 Preparing to unpack .../120-fonts-dejavu-mono_2.37-8_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.7464322Z #13 27.72 Unpacking fonts-dejavu-mono (2.37-8) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.7465370Z #13 27.77 Selecting previously unselected package fonts-dejavu-core.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.7466369Z #13 27.77 Preparing to unpack .../121-fonts-dejavu-core_2.37-8_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.7467232Z #13 27.79 Unpacking fonts-dejavu-core (2.37-8) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.9379304Z #13 27.83 Selecting previously unselected package fontconfig-config.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.9381700Z #13 27.83 Preparing to unpack .../122-fontconfig-config_2.15.0-1.1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:15.9731622Z #13 28.02 Unpacking fontconfig-config (2.15.0-1.1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.0846566Z #13 28.06 Selecting previously unselected package libfontconfig1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.0849379Z #13 28.06 Preparing to unpack .../123-libfontconfig1_2.15.0-1.1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.0850320Z #13 28.06 Unpacking libfontconfig1:amd64 (2.15.0-1.1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.0851189Z #13 28.09 Selecting previously unselected package fontconfig.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.0852174Z #13 28.09 Preparing to unpack .../124-fontconfig_2.15.0-1.1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.0853038Z #13 28.10 Unpacking fontconfig (2.15.0-1.1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.0854193Z #13 28.13 Selecting previously unselected package libpackagekit-glib2-18:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.2078133Z #13 28.14 Preparing to unpack .../125-libpackagekit-glib2-18_1.2.8-2ubuntu1.5_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.2081018Z #13 28.14 Unpacking libpackagekit-glib2-18:amd64 (1.2.8-2ubuntu1.5) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.2081990Z #13 28.18 Selecting previously unselected package gir1.2-packagekitglib-1.0.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.2083083Z #13 28.18 Preparing to unpack .../126-gir1.2-packagekitglib-1.0_1.2.8-2ubuntu1.5_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.2084423Z #13 28.18 Unpacking gir1.2-packagekitglib-1.0 (1.2.8-2ubuntu1.5) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.2085488Z #13 28.21 Selecting previously unselected package libcurl3t64-gnutls:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.2086442Z #13 28.21 Preparing to unpack .../127-libcurl3t64-gnutls_8.5.0-2ubuntu10.9_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.2087351Z #13 28.22 Unpacking libcurl3t64-gnutls:amd64 (8.5.0-2ubuntu10.9) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.4502983Z #13 28.25 Selecting previously unselected package liberror-perl.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.4506169Z #13 28.26 Preparing to unpack .../128-liberror-perl_0.17029-2_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.4506951Z #13 28.26 Unpacking liberror-perl (0.17029-2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.4507617Z #13 28.29 Selecting previously unselected package git-man.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.4508440Z #13 28.29 Preparing to unpack .../129-git-man_1%3a2.43.0-1ubuntu7.3_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.4509242Z #13 28.30 Unpacking git-man (1:2.43.0-1ubuntu7.3) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.4509910Z #13 28.34 Selecting previously unselected package git.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.4510657Z #13 28.34 Preparing to unpack .../130-git_1%3a2.43.0-1ubuntu7.3_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.4511385Z #13 28.35 Unpacking git (1:2.43.0-1ubuntu7.3) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.4971160Z #13 28.54 Selecting previously unselected package gnupg-utils.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.6059229Z #13 28.55 Preparing to unpack .../131-gnupg-utils_2.4.4-2ubuntu17.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.6062432Z #13 28.55 Unpacking gnupg-utils (2.4.4-2ubuntu17.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.6063182Z #13 28.58 Selecting previously unselected package gpg.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.6063977Z #13 28.58 Preparing to unpack .../132-gpg_2.4.4-2ubuntu17.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.6064709Z #13 28.58 Unpacking gpg (2.4.4-2ubuntu17.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.6065599Z #13 28.62 Selecting previously unselected package pinentry-curses.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.6066893Z #13 28.62 Preparing to unpack .../133-pinentry-curses_1.2.1-3ubuntu5_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.6067741Z #13 28.63 Unpacking pinentry-curses (1.2.1-3ubuntu5) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.6068463Z #13 28.65 Selecting previously unselected package gpg-agent.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.7059603Z #13 28.66 Preparing to unpack .../134-gpg-agent_2.4.4-2ubuntu17.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.7063419Z #13 28.66 Unpacking gpg-agent (2.4.4-2ubuntu17.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.7064580Z #13 28.69 Selecting previously unselected package gpgsm.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.7065798Z #13 28.69 Preparing to unpack .../135-gpgsm_2.4.4-2ubuntu17.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.7066647Z #13 28.70 Unpacking gpgsm (2.4.4-2ubuntu17.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.7067481Z #13 28.72 Selecting previously unselected package keyboxd.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.7068713Z #13 28.73 Preparing to unpack .../136-keyboxd_2.4.4-2ubuntu17.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.7069591Z #13 28.73 Unpacking keyboxd (2.4.4-2ubuntu17.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.7070443Z #13 28.75 Selecting previously unselected package gnupg.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.7071329Z #13 28.75 Preparing to unpack .../137-gnupg_2.4.4-2ubuntu17.4_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.8076530Z #13 28.76 Unpacking gnupg (2.4.4-2ubuntu17.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.8077806Z #13 28.78 Selecting previously unselected package libnl-genl-3-200:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.8078975Z #13 28.79 Preparing to unpack .../138-libnl-genl-3-200_3.7.0-0.3build1.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.8080018Z #13 28.79 Unpacking libnl-genl-3-200:amd64 (3.7.0-0.3build1.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.8080876Z #13 28.81 Selecting previously unselected package htop.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.8081715Z #13 28.82 Preparing to unpack .../139-htop_3.3.0-4build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.8082529Z #13 28.82 Unpacking htop (3.3.0-4build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.8083317Z #13 28.85 Selecting previously unselected package libonig5:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.9157234Z #13 28.86 Preparing to unpack .../140-libonig5_6.9.9-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.9160159Z #13 28.86 Unpacking libonig5:amd64 (6.9.9-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.9161595Z #13 28.89 Selecting previously unselected package libjq1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.9162595Z #13 28.90 Preparing to unpack .../141-libjq1_1.7.1-3ubuntu0.24.04.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.9163542Z #13 28.90 Unpacking libjq1:amd64 (1.7.1-3ubuntu0.24.04.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.9164340Z #13 28.93 Selecting previously unselected package jq.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.9165358Z #13 28.93 Preparing to unpack .../142-jq_1.7.1-3ubuntu0.24.04.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.9166239Z #13 28.94 Unpacking jq (1.7.1-3ubuntu0.24.04.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:16.9167046Z #13 28.96 Selecting previously unselected package libzip4t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.0421324Z #13 28.97 Preparing to unpack .../143-libzip4t64_1.7.3-1.1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.0424220Z #13 28.97 Unpacking libzip4t64:amd64 (1.7.3-1.1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.0425552Z #13 29.01 Selecting previously unselected package lib3mf1t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.0426606Z #13 29.01 Preparing to unpack .../144-lib3mf1t64_1.8.1+ds-4.1build2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.0427543Z #13 29.01 Unpacking lib3mf1t64:amd64 (1.8.1+ds-4.1build2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.0428403Z #13 29.04 Selecting previously unselected package libstemmer0d:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.0429368Z #13 29.05 Preparing to unpack .../145-libstemmer0d_2.2.0-4build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.0430229Z #13 29.05 Unpacking libstemmer0d:amd64 (2.2.0-4build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.0431036Z #13 29.09 Selecting previously unselected package libxmlb2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.1530079Z #13 29.09 Preparing to unpack .../146-libxmlb2_0.3.18-1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.1532722Z #13 29.10 Unpacking libxmlb2:amd64 (0.3.18-1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.1533932Z #13 29.13 Selecting previously unselected package libappstream5:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.1535391Z #13 29.13 Preparing to unpack .../147-libappstream5_1.0.2-1build6_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.1536817Z #13 29.13 Unpacking libappstream5:amd64 (1.0.2-1build6) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.1537682Z #13 29.16 Selecting previously unselected package libasound2-data.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.1538677Z #13 29.16 Preparing to unpack .../148-libasound2-data_1.2.11-1ubuntu0.2_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.1539607Z #13 29.16 Unpacking libasound2-data (1.2.11-1ubuntu0.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.1540487Z #13 29.20 Selecting previously unselected package libasound2t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.2590852Z #13 29.21 Preparing to unpack .../149-libasound2t64_1.2.11-1ubuntu0.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.2592304Z #13 29.21 Unpacking libasound2t64:amd64 (1.2.11-1ubuntu0.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.2593396Z #13 29.24 Selecting previously unselected package libasyncns0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.2594373Z #13 29.24 Preparing to unpack .../150-libasyncns0_0.8-6build4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.2595466Z #13 29.25 Unpacking libasyncns0:amd64 (0.8-6build4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.2596384Z #13 29.28 Selecting previously unselected package libavahi-common-data:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.2597381Z #13 29.28 Preparing to unpack .../151-libavahi-common-data_0.8-13ubuntu6.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.2598393Z #13 29.28 Unpacking libavahi-common-data:amd64 (0.8-13ubuntu6.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.2599296Z #13 29.31 Selecting previously unselected package libavahi-common3:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.3736446Z #13 29.31 Preparing to unpack .../152-libavahi-common3_0.8-13ubuntu6.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.3740264Z #13 29.31 Unpacking libavahi-common3:amd64 (0.8-13ubuntu6.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.3741346Z #13 29.34 Selecting previously unselected package libavahi-client3:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.3742386Z #13 29.34 Preparing to unpack .../153-libavahi-client3_0.8-13ubuntu6.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.3743335Z #13 29.34 Unpacking libavahi-client3:amd64 (0.8-13ubuntu6.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.3744298Z #13 29.37 Selecting previously unselected package libboost-filesystem1.83.0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.3745734Z #13 29.38 Preparing to unpack .../154-libboost-filesystem1.83.0_1.83.0-2.1ubuntu3.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.3747177Z #13 29.38 Unpacking libboost-filesystem1.83.0:amd64 (1.83.0-2.1ubuntu3.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.3748250Z #13 29.42 Selecting previously unselected package libboost-program-options1.83.0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.4933670Z #13 29.43 Preparing to unpack .../155-libboost-program-options1.83.0_1.83.0-2.1ubuntu3.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.4937103Z #13 29.43 Unpacking libboost-program-options1.83.0:amd64 (1.83.0-2.1ubuntu3.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.4938188Z #13 29.47 Selecting previously unselected package libpixman-1-0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.4939081Z #13 29.47 Preparing to unpack .../156-libpixman-1-0_0.42.2-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.4939877Z #13 29.48 Unpacking libpixman-1-0:amd64 (0.42.2-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.4940647Z #13 29.51 Selecting previously unselected package libxcb-render0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.4941552Z #13 29.51 Preparing to unpack .../157-libxcb-render0_1.15-1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.4942337Z #13 29.52 Unpacking libxcb-render0:amd64 (1.15-1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.4943097Z #13 29.54 Selecting previously unselected package libxcb-shm0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.6237080Z #13 29.54 Preparing to unpack .../158-libxcb-shm0_1.15-1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.6239078Z #13 29.54 Unpacking libxcb-shm0:amd64 (1.15-1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.6240046Z #13 29.56 Selecting previously unselected package libxrender1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.6241031Z #13 29.57 Preparing to unpack .../159-libxrender1_1%3a0.9.10-1.1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.6241963Z #13 29.57 Unpacking libxrender1:amd64 (1:0.9.10-1.1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.6242828Z #13 29.59 Selecting previously unselected package libcairo2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.6243751Z #13 29.59 Preparing to unpack .../160-libcairo2_1.18.0-3build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.6244647Z #13 29.59 Unpacking libcairo2:amd64 (1.18.0-3build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.6246148Z #13 29.63 Selecting previously unselected package libcups2t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.6247131Z #13 29.64 Preparing to unpack .../161-libcups2t64_2.4.7-1.2ubuntu7.9_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.6248041Z #13 29.64 Unpacking libcups2t64:amd64 (2.4.7-1.2ubuntu7.9) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7236100Z #13 29.67 Selecting previously unselected package libwayland-client0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7239856Z #13 29.68 Preparing to unpack .../162-libwayland-client0_1.22.0-2.1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7241073Z #13 29.68 Unpacking libwayland-client0:amd64 (1.22.0-2.1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7242024Z #13 29.70 Selecting previously unselected package libdecor-0-0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7243006Z #13 29.71 Preparing to unpack .../163-libdecor-0-0_0.2.2-1build2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7243889Z #13 29.71 Unpacking libdecor-0-0:amd64 (0.2.2-1build2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7244789Z #13 29.74 Selecting previously unselected package libdouble-conversion3:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7246127Z #13 29.74 Preparing to unpack .../164-libdouble-conversion3_3.3.0-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7247148Z #13 29.74 Unpacking libdouble-conversion3:amd64 (3.3.0-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7248055Z #13 29.76 Selecting previously unselected package libdrm-amdgpu1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7249103Z #13 29.77 Preparing to unpack .../165-libdrm-amdgpu1_2.4.125-1ubuntu0.1~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.7250176Z #13 29.77 Unpacking libdrm-amdgpu1:amd64 (2.4.125-1ubuntu0.1~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.8410505Z #13 29.80 Selecting previously unselected package libpciaccess0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.8416174Z #13 29.81 Preparing to unpack .../166-libpciaccess0_0.17-3ubuntu0.24.04.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.8417888Z #13 29.81 Unpacking libpciaccess0:amd64 (0.17-3ubuntu0.24.04.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.8419485Z #13 29.84 Selecting previously unselected package libdrm-intel1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.8421093Z #13 29.84 Preparing to unpack .../167-libdrm-intel1_2.4.125-1ubuntu0.1~24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.8422741Z #13 29.85 Unpacking libdrm-intel1:amd64 (2.4.125-1ubuntu0.1~24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:17.8424620Z #13 29.89 Selecting previously unselected package libduktape207:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.0725695Z #13 29.89 Preparing to unpack .../168-libduktape207_2.7.0+tests-0ubuntu3_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.0728194Z #13 29.90 Unpacking libduktape207:amd64 (2.7.0+tests-0ubuntu3) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.0729151Z #13 29.92 Selecting previously unselected package libdw1t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.0730085Z #13 29.93 Preparing to unpack .../169-libdw1t64_0.190-1.1ubuntu0.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.0730963Z #13 29.93 Unpacking libdw1t64:amd64 (0.190-1.1ubuntu0.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.0731797Z #13 29.97 Selecting previously unselected package libllvm20:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.0732729Z #13 29.97 Preparing to unpack .../170-libllvm20_1%3a20.1.2-0ubuntu1~24.04.2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.0733698Z #13 29.97 Unpacking libllvm20:amd64 (1:20.1.2-0ubuntu1~24.04.2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.7007341Z #13 30.75 Selecting previously unselected package libx11-xcb1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.8011628Z #13 30.75 Preparing to unpack .../171-libx11-xcb1_2%3a1.8.7-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.8015365Z #13 30.75 Unpacking libx11-xcb1:amd64 (2:1.8.7-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.8016357Z #13 30.78 Selecting previously unselected package libxcb-dri3-0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.8017317Z #13 30.79 Preparing to unpack .../172-libxcb-dri3-0_1.15-1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.8018256Z #13 30.79 Unpacking libxcb-dri3-0:amd64 (1.15-1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.8019094Z #13 30.81 Selecting previously unselected package libxcb-present0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.8020193Z #13 30.82 Preparing to unpack .../173-libxcb-present0_1.15-1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.8021086Z #13 30.82 Unpacking libxcb-present0:amd64 (1.15-1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.8021932Z #13 30.84 Selecting previously unselected package libxcb-randr0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.8023212Z #13 30.85 Preparing to unpack .../174-libxcb-randr0_1.15-1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.8024101Z #13 30.85 Unpacking libxcb-randr0:amd64 (1.15-1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.9145971Z #13 30.88 Selecting previously unselected package libxcb-sync1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.9147034Z #13 30.88 Preparing to unpack .../175-libxcb-sync1_1.15-1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.9147925Z #13 30.88 Unpacking libxcb-sync1:amd64 (1.15-1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.9148692Z #13 30.91 Selecting previously unselected package libxcb-xfixes0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.9149539Z #13 30.91 Preparing to unpack .../176-libxcb-xfixes0_1.15-1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.9150342Z #13 30.91 Unpacking libxcb-xfixes0:amd64 (1.15-1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.9151109Z #13 30.93 Selecting previously unselected package libxshmfence1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.9151931Z #13 30.94 Preparing to unpack .../177-libxshmfence1_1.3-1build5_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.9152721Z #13 30.94 Unpacking libxshmfence1:amd64 (1.3-1build5) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:18.9155673Z #13 30.96 Selecting previously unselected package mesa-libgallium:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.0727298Z #13 30.96 Preparing to unpack .../178-mesa-libgallium_25.2.8-0ubuntu0.24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.0731953Z #13 30.97 Unpacking mesa-libgallium:amd64 (25.2.8-0ubuntu0.24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.3192596Z #13 31.23 Selecting previously unselected package libgbm1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.3195529Z #13 31.23 Preparing to unpack .../179-libgbm1_25.2.8-0ubuntu0.24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.3196620Z #13 31.23 Unpacking libgbm1:amd64 (25.2.8-0ubuntu0.24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.3197504Z #13 31.26 Selecting previously unselected package libegl-mesa0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.3198505Z #13 31.27 Preparing to unpack .../180-libegl-mesa0_25.2.8-0ubuntu0.24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.3199454Z #13 31.27 Unpacking libegl-mesa0:amd64 (25.2.8-0ubuntu0.24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.3200317Z #13 31.31 Selecting previously unselected package libogg0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.3201505Z #13 31.31 Preparing to unpack .../181-libogg0_1.3.5-3build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.3202270Z #13 31.32 Unpacking libogg0:amd64 (1.3.5-3build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.3203032Z #13 31.37 Selecting previously unselected package libflac12t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.4334872Z #13 31.37 Preparing to unpack .../182-libflac12t64_1.4.3+ds-2.1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.4337182Z #13 31.37 Unpacking libflac12t64:amd64 (1.4.3+ds-2.1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.4338094Z #13 31.40 Selecting previously unselected package libfontenc1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.4339005Z #13 31.41 Preparing to unpack .../183-libfontenc1_1%3a1.1.8-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.4339817Z #13 31.42 Unpacking libfontenc1:amd64 (1:1.1.8-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.4340583Z #13 31.44 Selecting previously unselected package libvulkan1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.4341532Z #13 31.44 Preparing to unpack .../184-libvulkan1_1.3.275.0-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.4342456Z #13 31.45 Unpacking libvulkan1:amd64 (1.3.275.0-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.5349070Z #13 31.48 Selecting previously unselected package libgl1-mesa-dri:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.5352485Z #13 31.49 Preparing to unpack .../185-libgl1-mesa-dri_25.2.8-0ubuntu0.24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.5353677Z #13 31.49 Unpacking libgl1-mesa-dri:amd64 (25.2.8-0ubuntu0.24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.5354595Z #13 31.53 Selecting previously unselected package libglvnd0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.5355703Z #13 31.53 Preparing to unpack .../186-libglvnd0_1.7.0-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.5356590Z #13 31.54 Unpacking libglvnd0:amd64 (1.7.0-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.5357443Z #13 31.57 Selecting previously unselected package libxcb-glx0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.5358393Z #13 31.58 Preparing to unpack .../187-libxcb-glx0_1.15-1ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.6469262Z #13 31.58 Unpacking libxcb-glx0:amd64 (1.15-1ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.6470617Z #13 31.61 Selecting previously unselected package libxxf86vm1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.6471772Z #13 31.62 Preparing to unpack .../188-libxxf86vm1_1%3a1.1.4-1build4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.6472691Z #13 31.62 Unpacking libxxf86vm1:amd64 (1:1.1.4-1build4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.6473566Z #13 31.65 Selecting previously unselected package libglx-mesa0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.6474550Z #13 31.66 Preparing to unpack .../189-libglx-mesa0_25.2.8-0ubuntu0.24.04.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.6475746Z #13 31.66 Unpacking libglx-mesa0:amd64 (25.2.8-0ubuntu0.24.04.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.6476642Z #13 31.69 Selecting previously unselected package libglx0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7791114Z #13 31.69 Preparing to unpack .../190-libglx0_1.7.0-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7794185Z #13 31.70 Unpacking libglx0:amd64 (1.7.0-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7795481Z #13 31.74 Selecting previously unselected package libgl1:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7796446Z #13 31.74 Preparing to unpack .../191-libgl1_1.7.0-1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7797212Z #13 31.75 Unpacking libgl1:amd64 (1.7.0-1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7797938Z #13 31.77 Selecting previously unselected package libglew2.2:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7798741Z #13 31.78 Preparing to unpack .../192-libglew2.2_2.2.0-4build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7799486Z #13 31.78 Unpacking libglew2.2:amd64 (2.2.0-4build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7800175Z #13 31.83 Selecting previously unselected package libglib2.0-bin.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7800798Z #13 ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7801113Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7801495Z #19 [web-builder 7/7] RUN npm run build --workspace=apps/web
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7802186Z #19 0.254 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7802615Z #19 0.254 > web@0.0.0 build
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7803094Z #19 0.254 > tsc -b && vite build
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.7803576Z #19 0.254 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.8968060Z #19 ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.8971370Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.8973218Z #13 [stage-1  2/33] RUN apt-get update && apt-get install -y --no-install-recommends     software-properties-common     curl     git     build-essential     ca-certificates     sudo     vim     nano     htop     jq     gnupg     supervisor     openscad     xvfb     && rm -rf /var/lib/apt/lists/*
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.8975886Z #13 31.83 Preparing to unpack .../193-libglib2.0-bin_2.80.0-6ubuntu3.8_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.8976734Z #13 31.83 Unpacking libglib2.0-bin (2.80.0-6ubuntu3.8) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.8977488Z #13 31.86 Selecting previously unselected package libgraphite2-3:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.8978372Z #13 31.87 Preparing to unpack .../194-libgraphite2-3_1.3.14-2build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.8979185Z #13 31.87 Unpacking libgraphite2-3:amd64 (1.3.14-2build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.8980031Z #13 31.90 Selecting previously unselected package libunwind8:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.8980894Z #13 31.91 Preparing to unpack .../195-libunwind8_1.6.2-3build1.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:19.8981703Z #13 31.91 Unpacking libunwind8:amd64 (1.6.2-3build1.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.0087965Z #13 31.94 Selecting previously unselected package libgstreamer1.0-0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.0091394Z #13 31.96 Preparing to unpack .../196-libgstreamer1.0-0_1.24.2-1ubuntu0.1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.0092380Z #13 31.96 Unpacking libgstreamer1.0-0:amd64 (1.24.2-1ubuntu0.1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.0093253Z #13 32.03 Selecting previously unselected package libgudev-1.0-0:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.0094269Z #13 32.03 Preparing to unpack .../197-libgudev-1.0-0_1%3a238-5ubuntu1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.0095314Z #13 32.03 Unpacking libgudev-1.0-0:amd64 (1:238-5ubuntu1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.0096177Z #13 32.06 Selecting previously unselected package libharfbuzz0b:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.1152462Z #13 32.06 Preparing to unpack .../198-libharfbuzz0b_8.3.0-2build2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.1155410Z #13 32.06 Unpacking libharfbuzz0b:amd64 (8.3.0-2build2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.1156590Z #13 32.10 Selecting previously unselected package x11-common.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.1157465Z #13 32.11 Preparing to unpack .../199-x11-common_1%3a7.7+23ubuntu3_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.1158280Z #13 32.12 Unpacking x11-common (1:7.7+23ubuntu3) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.1158986Z #13 32.16 Selecting previously unselected package libice6:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.2828735Z #13 32.16 Preparing to unpack .../200-libice6_2%3a1.0.10-1build3_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.2829752Z #13 32.17 Unpacking libice6:amd64 (2:1.0.10-1build3) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.2830482Z #13 32.20 Selecting previously unselected package libwacom-common.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.2831290Z #13 32.20 Preparing to unpack .../201-libwacom-common_2.10.0-2_all.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.2831994Z #13 32.20 Unpacking libwacom-common (2.10.0-2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.2832664Z #13 32.33 Selecting previously unselected package libwacom9:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.4446096Z #13 32.33 Preparing to unpack .../202-libwacom9_2.10.0-2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.4446662Z #13 32.34 Unpacking libwacom9:amd64 (2.10.0-2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.5028078Z #13 32.55 Selecting previously unselected package libinput-bin.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.6862036Z #13 32.56 Preparing to unpack .../203-libinput-bin_1.25.0-1ubuntu3.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.6863700Z #13 32.58 Unpacking libinput-bin (1.25.0-1ubuntu3.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.7095784Z #13 32.76 Selecting previously unselected package libmtdev1t64:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.8989931Z #13 32.76 Preparing to unpack .../204-libmtdev1t64_1.1.6-1.1build1_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.8990791Z #13 32.76 Unpacking libmtdev1t64:amd64 (1.1.6-1.1build1) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.8991434Z #13 32.79 Selecting previously unselected package libinput10:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.8992178Z #13 32.79 Preparing to unpack .../205-libinput10_1.25.0-1ubuntu3.4_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:20.8992850Z #13 32.80 Unpacking libinput10:amd64 (1.25.0-1ubuntu3.4) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.4410874Z #13 34.49 Selecting previously unselected package libjpeg-turbo8:amd64.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5290046Z #13 34.49 Preparing to unpack .../206-libjpeg-turbo8_2.1.5-2ubuntu2_amd64.deb ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5291188Z #13 34.50 Unpacking libjpeg-turbo8:amd64 (2.1.5-2ubuntu2) ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5291952Z #13 CANCELED
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5294398Z 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5295336Z #19 [web-builder 7/7] RUN npm run build --workspace=apps/web
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5296568Z #19 10.97 file:///workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs:507
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5298976Z #19 10.97 		if (loadErrors.length > 0) throw new Error("Cannot find native binding. npm has a bug related to optional dependencies (https://github.com/npm/cli/issues/4828). Please try `npm i` again after removing both package-lock.json and node_modules directory.", { cause: loadErrors.reduce((err, cur) => {
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5303939Z #19 10.97 		                                 ^
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5304816Z #19 10.97 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5306534Z #19 10.97 Error: Cannot find native binding. npm has a bug related to optional dependencies (https://github.com/npm/cli/issues/4828). Please try `npm i` again after removing both package-lock.json and node_modules directory.
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5309281Z #19 10.97     at file:///workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs:507:36
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5310802Z #19 10.97     at file:///workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs:9:49
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5311912Z #19 10.97     at file:///workspace/apps/web/node_modules/rolldown/dist/shared/parse-Bg2pr2Q5.mjs:3:46
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5312847Z #19 10.97     at ModuleJob.run (node:internal/modules/esm/module_job:343:25)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5313834Z #19 10.97     at async onImport.tracePromise.__proto__ (node:internal/modules/esm/loader:681:26)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5317938Z #19 10.97     at async CAC.<anonymous> (file:///workspace/apps/web/node_modules/vite/dist/node/cli.js:763:28) {
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5320989Z #19 10.97   [cause]: Error: Cannot find module '@rolldown/binding-linux-x64-gnu'
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5322678Z #19 10.97   Require stack:
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5324265Z #19 10.97   - /workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5325649Z #19 10.97       at Function._resolveFilename (node:internal/modules/cjs/loader:1430:15)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5326692Z #19 10.97       ... 5 lines matching cause stack trace ...
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5327763Z #19 10.97       at require (node:internal/modules/helpers:147:16)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5329035Z #19 10.97       at requireNative (file:///workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs:277:21)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5330615Z #19 10.97       at file:///workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs:475:18
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5332536Z #19 10.97       at file:///workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs:9:49 {
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5334388Z #19 10.97     code: 'MODULE_NOT_FOUND',
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5335637Z #19 10.97     requireStack: [
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5336570Z #19 10.97       '/workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs'
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5337692Z #19 10.97     ],
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5338732Z #19 10.97     cause: Error: Cannot find module '../rolldown-binding.linux-x64-gnu.node'
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5339831Z #19 10.97     Require stack:
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5340773Z #19 10.97     - /workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5342043Z #19 10.97         at Function._resolveFilename (node:internal/modules/cjs/loader:1430:15)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5343064Z #19 10.97         at defaultResolveImpl (node:internal/modules/cjs/loader:1040:19)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5344230Z #19 10.97         at resolveForCJSWithHooks (node:internal/modules/cjs/loader:1045:22)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5345481Z #19 10.97         at Function._load (node:internal/modules/cjs/loader:1216:25)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5346701Z #19 10.97         at wrapModuleLoad (node:internal/modules/cjs/loader:254:19)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5347741Z #19 10.97         at Module.require (node:internal/modules/cjs/loader:1527:12)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5349845Z #19 10.97         at require (node:internal/modules/helpers:147:16)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5351385Z #19 10.97         at requireNative (file:///workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs:272:12)
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5353341Z #19 10.97         at file:///workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs:475:18
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5355482Z #19 10.97         at file:///workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs:9:49 {
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5357067Z #19 10.97       code: 'MODULE_NOT_FOUND',
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5358023Z #19 10.97       requireStack: [
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5359010Z #19 10.97         '/workspace/apps/web/node_modules/rolldown/dist/shared/binding-CXquf8ay.mjs'
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5360105Z #19 10.97       ]
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5360715Z #19 10.97     }
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5361188Z #19 10.97   }
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5361648Z #19 10.97 }
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5362086Z #19 10.97 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5362541Z #19 10.97 Node.js v22.22.3
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5363149Z #19 10.98 npm error Lifecycle script `build` failed with error:
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5363793Z #19 10.98 npm error code 1
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5364328Z #19 10.98 npm error path /workspace/apps/web
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5365286Z #19 10.98 npm error workspace web@0.0.0
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5365904Z #19 10.98 npm error location /workspace/apps/web
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5366552Z #19 10.98 npm error command failed
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5367098Z #19 10.99 npm error command sh -c tsc -b && vite build
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5367775Z #19 ERROR: process "/bin/sh -c npm run build --workspace=apps/web" did not complete successfully: exit code: 1
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5368388Z ------
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5368800Z  > [web-builder 7/7] RUN npm run build --workspace=apps/web:
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5369498Z 10.97 }
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5369830Z 10.97 
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5370171Z 10.97 Node.js v22.22.3
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5370611Z 10.98 npm error Lifecycle script `build` failed with error:
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5371087Z 10.98 npm error code 1
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5371478Z 10.98 npm error path /workspace/apps/web
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5371907Z 10.98 npm error workspace web@0.0.0
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5372331Z 10.98 npm error location /workspace/apps/web
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5372761Z 10.98 npm error command failed
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5373506Z 10.99 npm error command sh -c tsc -b && vite build
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5374103Z ------
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5410458Z Dockerfile:15
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5425667Z --------------------
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5436090Z   13 |     RUN npm ci
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5436518Z   14 |     COPY apps/web/ apps/web/
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5436998Z   15 | >>> RUN npm run build --workspace=apps/web
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5437451Z   16 |     
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5437779Z   17 |     # Stage 2: Production runtime image
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5438228Z --------------------
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5439047Z ERROR: failed to build: failed to solve: process "/bin/sh -c npm run build --workspace=apps/web" did not complete successfully: exit code: 1
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.5806289Z ##[group]Reference
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.6833753Z builder-9f02d814-dffe-4818-8820-f78b2bddeb2a/builder-9f02d814-dffe-4818-8820-f78b2bddeb2a0/luffmcljwpb5d5n4hhz7pvlc8
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.6845946Z ##[endgroup]
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.6846706Z ##[group]Check build summary support
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.6849664Z Build summary supported!
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.6850599Z ##[endgroup]
build-and-push	Build and Load (Local Test)	2026-06-05T15:59:22.6882204Z ##[error]buildx failed with: ERROR: failed to build: failed to solve: process "/bin/sh -c npm run build --workspace=apps/web" did not complete successfully: exit code: 1
```

---

## 5. python-quality (Run #27025468181)
- **Branch**: `dev`
- **Commit SHA**: `2ceded12d1146c23d62b4b8c7c6aeb3d831bb82f`
- **Time**: 2026-06-05T15:58:28Z
- **URL**: [View run on GitHub](https://github.com/burhop/wright/actions/runs/27025468181)

### Failed Log Output
```text
python-quality	Run Tests with pytest	﻿2026-06-05T15:58:50.6930010Z ##[group]Run uv run pytest
python-quality	Run Tests with pytest	2026-06-05T15:58:50.6930326Z [36;1muv run pytest[0m
python-quality	Run Tests with pytest	2026-06-05T15:58:50.6957355Z shell: /usr/bin/bash -e {0}
python-quality	Run Tests with pytest	2026-06-05T15:58:50.6957619Z env:
python-quality	Run Tests with pytest	2026-06-05T15:58:50.6957875Z   UV_CACHE_DIR: /home/runner/work/_temp/setup-uv-cache
python-quality	Run Tests with pytest	2026-06-05T15:58:50.6958278Z   pythonLocation: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:58:50.6958753Z   PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib/pkgconfig
python-quality	Run Tests with pytest	2026-06-05T15:58:50.6959215Z   Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:58:50.6959610Z   Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:58:50.6960013Z   Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.13.13/x64
python-quality	Run Tests with pytest	2026-06-05T15:58:50.6960418Z   LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.13.13/x64/lib
python-quality	Run Tests with pytest	2026-06-05T15:58:50.6960759Z ##[endgroup]
python-quality	Run Tests with pytest	2026-06-05T15:58:54.1102589Z ============================= test session starts ==============================
python-quality	Run Tests with pytest	2026-06-05T15:58:54.1103726Z platform linux -- Python 3.13.13, pytest-9.0.3, pluggy-1.6.0
python-quality	Run Tests with pytest	2026-06-05T15:58:54.1105071Z rootdir: /home/runner/work/wright/wright
python-quality	Run Tests with pytest	2026-06-05T15:58:54.1110186Z configfile: pyproject.toml
python-quality	Run Tests with pytest	2026-06-05T15:58:54.1110839Z plugins: asyncio-1.4.0, anyio-4.13.0
python-quality	Run Tests with pytest	2026-06-05T15:58:54.1111963Z asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
python-quality	Run Tests with pytest	2026-06-05T15:58:54.1113518Z collected 45 items
python-quality	Run Tests with pytest	2026-06-05T15:58:54.1113852Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:54.3840920Z apps/api/tests/test_hermes_adapter.py ........                           [ 17%]
python-quality	Run Tests with pytest	2026-06-05T15:58:54.6018132Z apps/api/tests/test_mcp_api.py .............                             [ 46%]
python-quality	Run Tests with pytest	2026-06-05T15:58:54.6759125Z apps/api/tests/test_webmcp.py ..                                         [ 51%]
python-quality	Run Tests with pytest	2026-06-05T15:58:55.5397716Z apps/api/tests/test_workspace_api.py .......FFF........                  [ 91%]
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6337923Z packages/tool_registry/tests/test_registry.py ....                       [100%]
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6338874Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6339461Z =================================== FAILURES ===================================
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6340541Z __________________________ test_git_status_and_commit __________________________
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6341267Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6341826Z client = <starlette.testclient.TestClient object at 0x7f72f5befac0>
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6342580Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6342976Z     def test_git_status_and_commit(client):
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6343766Z         # Add a file first (will be untracked 'U')
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6344928Z         client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6345545Z             "/api/workspace/files",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6346457Z             json={"session_id": "test-session", "path": "/untracked.txt", "type": "file"},
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6347389Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6347920Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6348444Z         # Check Git Status
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6349069Z         response = client.get(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6349896Z             "/api/workspace/git/status", params={"session_id": "test-session"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6350777Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6351367Z         assert response.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6352085Z         data = response.json()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6352793Z         assert "branch_name" in data
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6353521Z         assert len(data["changes"]) > 0
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6354460Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6355029Z         # Commit changes
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6355691Z         response_commit = client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6356426Z             "/api/workspace/git/commit",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6357290Z             json={"session_id": "test-session", "message": "feat: test git commit"},
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6358189Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6358773Z >       assert response_commit.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6359511Z E       assert 500 == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6360172Z E        +  where 500 = <Response [500 Internal Server Error]>.status_code
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6360772Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6361184Z apps/api/tests/test_workspace_api.py:272: AssertionError
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6362507Z ----------------------------- Captured stdout call -----------------------------
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6363890Z {"event": "Initialized local Git repository in workspace /tmp/tmp6oe7tifj", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:54.826283Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6366073Z {"event": "Created default .gitignore in /tmp/tmp6oe7tifj/.gitignore", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:54.826494Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6368029Z {"event": "Failed to commit changes: Command '['git', 'commit', '-m', 'feat: test git commit']' returned non-zero exit status 128.", "level": "error", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:54.845590Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6369578Z ___________________________ test_git_diff_and_revert ___________________________
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6370153Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6370586Z self = <core.workspace.WorkspaceManager object at 0x7f72f59f1390>
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6371304Z rel_path = '/diff_test.txt'
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6371699Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6372033Z     def revert_file(self, rel_path: str) -> None:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6372764Z         """Revert a file back to HEAD state or delete if untracked."""
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6373482Z         abs_path = self.sanitize_path(rel_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6374606Z         is_untracked = False
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6375120Z         try:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6375594Z             res_status = subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6376208Z                 ["git", "status", "--porcelain", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6376828Z                 cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6377373Z                 capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6377903Z                 text=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6378378Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6378876Z             if res_status.stdout.startswith("??"):
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6379481Z                 is_untracked = True
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6380021Z         except Exception:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6380509Z             pass
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6380945Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6381377Z         if is_untracked:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6381880Z             if os.path.isdir(abs_path):
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6382439Z                 import shutil
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6382927Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6383378Z                 shutil.rmtree(abs_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6383941Z             elif os.path.exists(abs_path):
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6384852Z                 os.remove(abs_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6385393Z         else:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6385814Z             try:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6386498Z                 subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6387130Z                     ["git", "reset", "HEAD", "--", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6387754Z                     cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6388303Z                     capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6388831Z                 )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6389278Z >               subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6389851Z                     ["git", "checkout", "HEAD", "--", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6390477Z                     cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6391030Z                     capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6391562Z                     check=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6392047Z                 )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6392375Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6392704Z packages/core/src/core/workspace.py:770: 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6393352Z _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6393961Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6394571Z input = None, capture_output = True, timeout = None, check = True
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6395443Z popenargs = (['git', 'checkout', 'HEAD', '--', '/tmp/tmplld_wzks/diff_test.txt'],)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6396313Z kwargs = {'cwd': '/tmp/tmplld_wzks', 'stderr': -1, 'stdout': -1}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6397169Z process = <Popen: returncode: 128 args: ['git', 'checkout', 'HEAD', '--', '/tmp/tmplld...>
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6398078Z stdout = b'', stderr = b'fatal: invalid reference: HEAD\n', retcode = 128
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6398919Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6399220Z     def run(*popenargs,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6399889Z             input=None, capture_output=False, timeout=None, check=False, **kwargs):
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6400806Z         """Run command with arguments and return a CompletedProcess instance.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6401523Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6402126Z         The returned instance will have attributes args, returncode, stdout and
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6403143Z         stderr. By default, stdout and stderr are not captured, and those attributes
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6404285Z         will be None. Pass stdout=PIPE and/or stderr=PIPE in order to capture them,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6405122Z         or pass capture_output=True to capture both.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6405709Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6406243Z         If check is True and the exit code was non-zero, it raises a
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6407139Z         CalledProcessError. The CalledProcessError object will have the return code
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6408113Z         in the returncode attribute, and output & stderr attributes if those streams
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6408875Z         were captured.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6409347Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6409888Z         If timeout (seconds) is given and the process takes too long,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6410842Z          a TimeoutExpired exception will be raised.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6411429Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6411949Z         There is an optional argument "input", allowing you to
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6412761Z         pass bytes or a string to the subprocess's stdin.  If you use this argument
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6413634Z         you may not also use the Popen constructor's "stdin" argument, as
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6414521Z         it will be used internally.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6415060Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6415669Z         By default, all communication is in bytes, and therefore any "input" should
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6416569Z         be bytes, and the stdout and stderr will be bytes. If in text mode, any
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6417457Z         "input" should be a string, and stdout and stderr will be strings decoded
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6418329Z         according to locale encoding, or by "encoding" if set. Text mode is
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6419201Z         triggered by setting any of text, encoding, errors or universal_newlines.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6419919Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6420478Z         The other arguments are the same as for the Popen constructor.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6421181Z         """
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6421624Z         if input is not None:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6422161Z             if kwargs.get('stdin') is not None:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6422881Z                 raise ValueError('stdin and input arguments may not both be used.')
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6423611Z             kwargs['stdin'] = PIPE
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6424279Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6424733Z         if capture_output:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6425403Z             if kwargs.get('stdout') is not None or kwargs.get('stderr') is not None:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6426284Z                 raise ValueError('stdout and stderr arguments may not be used '
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6427025Z                                  'with capture_output.')
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6427617Z             kwargs['stdout'] = PIPE
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6428158Z             kwargs['stderr'] = PIPE
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6428673Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6429159Z         with Popen(*popenargs, **kwargs) as process:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6429757Z             try:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6430548Z                 stdout, stderr = process.communicate(input, timeout=timeout)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6431341Z             except TimeoutExpired as exc:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6431924Z                 process.kill()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6432454Z                 if _mswindows:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6433061Z                     # Windows accumulates the output in a single blocking
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6434029Z                     # read() call run on child threads, with the timeout
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6435386Z                     # being done in a join() on those threads.  communicate()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6436193Z                     # _after_ kill() is required to collect that and add it
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6436873Z                     # to the exception.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6437517Z                     exc.stdout, exc.stderr = process.communicate()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6438179Z                 else:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6438769Z                     # POSIX _communicate already populated the output so
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6439496Z                     # far into the TimeoutExpired exception.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6440148Z                     process.wait()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6440680Z                 raise
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6442226Z             except:  # Including KeyboardInterrupt, communicate handled that.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6442996Z                 process.kill()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6443649Z                 # We don't call process.wait() as .__exit__ does that for us.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6444568Z                 raise
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6445075Z             retcode = process.poll()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6445645Z             if check and retcode:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6446276Z >               raise CalledProcessError(retcode, process.args,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6446993Z                                          output=stdout, stderr=stderr)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6448383Z E               subprocess.CalledProcessError: Command '['git', 'checkout', 'HEAD', '--', '/tmp/tmplld_wzks/diff_test.txt']' returned non-zero exit status 128.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6449379Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6449942Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/subprocess.py:577: CalledProcessError
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6450672Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6451109Z The above exception was the direct cause of the following exception:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6451694Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6452129Z client = <starlette.testclient.TestClient object at 0x7f72f5befdf0>
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6452715Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6453033Z     def test_git_diff_and_revert(client):
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6453639Z         # Setup - Create file and commit it
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6454426Z         client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6454945Z             "/api/workspace/files",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6455686Z             json={"session_id": "test-session", "path": "/diff_test.txt", "type": "file"},
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6456455Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6456897Z         client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6457397Z             "/api/workspace/git/commit",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6458087Z             json={"session_id": "test-session", "message": "initial commit"},
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6458788Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6459206Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6459754Z         # Modify file content manually on disk by resolving its path
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6460466Z         from api.config import DATABASE_PATH
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6461141Z         from core.workspace import get_workspace_by_session
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6461758Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6462436Z         workspace = get_workspace_by_session(DATABASE_PATH, "test-session")
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6463324Z         file_path = os.path.join(workspace["local_path"], "diff_test.txt")
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6464238Z         with open(file_path, "w") as f:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6464858Z             f.write("modified content here")
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6465424Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6465841Z         # Get Diff
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6466322Z         response_diff = client.get(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6466880Z             "/api/workspace/git/diff",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6467584Z             params={"session_id": "test-session", "path": "/diff_test.txt"},
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6468278Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6468757Z         assert response_diff.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6469388Z         assert "diff" in response_diff.json()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6469951Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6470364Z         # Revert
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6470854Z >       response_revert = client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6471437Z             "/api/workspace/git/revert",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6476131Z             json={"session_id": "test-session", "path": "/diff_test.txt"},
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6476884Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6477210Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6477685Z apps/api/tests/test_workspace_api.py:312: 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6478428Z _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6479288Z .venv/lib/python3.13/site-packages/starlette/testclient.py:560: in post
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6480027Z     return super().post(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6480683Z .venv/lib/python3.13/site-packages/httpx/_client.py:1144: in post
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6481367Z     return self.request(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6482054Z .venv/lib/python3.13/site-packages/starlette/testclient.py:459: in request
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6482808Z     return super().request(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6483459Z .venv/lib/python3.13/site-packages/httpx/_client.py:825: in request
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6484586Z     return self.send(request, auth=auth, follow_redirects=follow_redirects)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6485411Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6486149Z .venv/lib/python3.13/site-packages/httpx/_client.py:914: in send
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6486871Z     response = self._send_handling_auth(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6488200Z .venv/lib/python3.13/site-packages/httpx/_client.py:942: in _send_handling_auth
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6488996Z     response = self._send_handling_redirects(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6489820Z .venv/lib/python3.13/site-packages/httpx/_client.py:979: in _send_handling_redirects
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6490660Z     response = self._send_single_request(request)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6491278Z                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6492041Z .venv/lib/python3.13/site-packages/httpx/_client.py:1014: in _send_single_request
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6492864Z     response = transport.handle_request(request)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6493474Z                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6494511Z .venv/lib/python3.13/site-packages/starlette/testclient.py:362: in handle_request
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6495302Z     raise exc
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6495963Z .venv/lib/python3.13/site-packages/starlette/testclient.py:359: in handle_request
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6496797Z     portal.call(self.app, scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6497551Z .venv/lib/python3.13/site-packages/anyio/from_thread.py:334: in call
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6498399Z     return cast(T_Retval, self.start_task_soon(func, *args).result())
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6499130Z                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6500019Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/concurrent/futures/_base.py:456: in result
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6500871Z     return self.__get_result()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6501361Z            ^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6502150Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/concurrent/futures/_base.py:401: in __get_result
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6503030Z     raise self._exception
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6503669Z .venv/lib/python3.13/site-packages/anyio/from_thread.py:259: in _call_func
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6504616Z     retval = await retval_or_awaitable
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6505166Z              ^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6505858Z .venv/lib/python3.13/site-packages/fastapi/applications.py:1159: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6506658Z     await super().__call__(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6507420Z .venv/lib/python3.13/site-packages/starlette/applications.py:90: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6508238Z     await self.middleware_stack(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6509102Z .venv/lib/python3.13/site-packages/starlette/middleware/errors.py:186: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6509891Z     raise exc
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6510567Z .venv/lib/python3.13/site-packages/starlette/middleware/errors.py:164: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6511399Z     await self.app(scope, receive, _send)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6512188Z .venv/lib/python3.13/site-packages/starlette/middleware/base.py:191: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6513313Z     with recv_stream, send_stream, collapse_excgroups():
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6513981Z                                    ^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6515019Z /opt/hostedtoolcache/Python/3.13.13/x64/lib/python3.13/contextlib.py:162: in __exit__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6515844Z     self.gen.throw(value)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6516567Z .venv/lib/python3.13/site-packages/starlette/_utils.py:87: in collapse_excgroups
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6517334Z     raise exc
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6518014Z .venv/lib/python3.13/site-packages/starlette/middleware/base.py:193: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6518899Z     response = await self.dispatch_func(request, call_next)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6519579Z                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6520245Z apps/api/src/api/middleware/tracing.py:119: in dispatch
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6520924Z     response = await call_next(request)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6521514Z                ^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6522393Z .venv/lib/python3.13/site-packages/starlette/middleware/base.py:168: in call_next
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6523293Z     raise app_exc from app_exc.__cause__ or app_exc.__context__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6524371Z .venv/lib/python3.13/site-packages/starlette/middleware/base.py:144: in coro
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6525559Z     await self.app(scope, receive_or_disconnect, send_no_error)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6526434Z .venv/lib/python3.13/site-packages/starlette/middleware/cors.py:88: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6527239Z     await self.app(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6528030Z .venv/lib/python3.13/site-packages/starlette/middleware/exceptions.py:63: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6529001Z     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6530214Z .venv/lib/python3.13/site-packages/starlette/_exception_handler.py:53: in wrapped_app
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6531083Z     raise exc
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6531794Z .venv/lib/python3.13/site-packages/starlette/_exception_handler.py:42: in wrapped_app
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6532637Z     await app(scope, receive, sender)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6533449Z .venv/lib/python3.13/site-packages/fastapi/middleware/asyncexitstack.py:18: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6534531Z     await self.app(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6535296Z .venv/lib/python3.13/site-packages/starlette/routing.py:660: in __call__
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6536135Z     await self.middleware_stack(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6536907Z .venv/lib/python3.13/site-packages/starlette/routing.py:680: in app
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6537636Z     await route.handle(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6538383Z .venv/lib/python3.13/site-packages/starlette/routing.py:276: in handle
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6539120Z     await self.app(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6539811Z .venv/lib/python3.13/site-packages/fastapi/routing.py:134: in app
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6540651Z     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6541633Z .venv/lib/python3.13/site-packages/starlette/_exception_handler.py:53: in wrapped_app
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6542454Z     raise exc
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6543117Z .venv/lib/python3.13/site-packages/starlette/_exception_handler.py:42: in wrapped_app
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6543944Z     await app(scope, receive, sender)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6544854Z .venv/lib/python3.13/site-packages/fastapi/routing.py:120: in app
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6545571Z     response = await f(request)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6546088Z                ^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6546720Z .venv/lib/python3.13/site-packages/fastapi/routing.py:674: in app
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6547459Z     raw_response = await run_endpoint_function(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6548273Z .venv/lib/python3.13/site-packages/fastapi/routing.py:328: in run_endpoint_function
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6549100Z     return await dependant.call(**values)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6549664Z            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6550553Z packages/core/src/core/tracing.py:48: in async_wrapper
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6551198Z     result = await func(*args, **kwargs)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6551750Z              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6552404Z apps/api/src/api/routers/workspace.py:271: in git_revert_endpoint
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6553121Z     mgr.revert_file(body.path)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6553739Z _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6554474Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6554894Z self = <core.workspace.WorkspaceManager object at 0x7f72f59f1390>
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6555620Z rel_path = '/diff_test.txt'
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6555998Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6556348Z     def revert_file(self, rel_path: str) -> None:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6557085Z         """Revert a file back to HEAD state or delete if untracked."""
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6557812Z         abs_path = self.sanitize_path(rel_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6558402Z         is_untracked = False
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6558912Z         try:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6559383Z             res_status = subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6560005Z                 ["git", "status", "--porcelain", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6560620Z                 cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6561492Z                 capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6562042Z                 text=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6562517Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6563014Z             if res_status.stdout.startswith("??"):
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6563605Z                 is_untracked = True
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6564318Z         except Exception:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6564832Z             pass
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6565284Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6565753Z         if is_untracked:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6566276Z             if os.path.isdir(abs_path):
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6566838Z                 import shutil
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6567341Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6567781Z                 shutil.rmtree(abs_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6568369Z             elif os.path.exists(abs_path):
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6568949Z                 os.remove(abs_path)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6569484Z         else:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6569929Z             try:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6570389Z                 subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6570973Z                     ["git", "reset", "HEAD", "--", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6571607Z                     cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6572171Z                     capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6572960Z                 )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6573543Z                 subprocess.run(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6574378Z                     ["git", "checkout", "HEAD", "--", abs_path],
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6575029Z                     cwd=self.base_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6575595Z                     capture_output=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6576134Z                     check=True,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6576626Z                 )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6577101Z             except Exception as e:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6577760Z                 logger.error("Failed to revert file %s: %s", rel_path, e)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6578505Z >               raise RuntimeError(f"Failed to revert file: {e}")
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6579684Z E               RuntimeError: Failed to revert file: Command '['git', 'checkout', 'HEAD', '--', '/tmp/tmplld_wzks/diff_test.txt']' returned non-zero exit status 128.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6580665Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6581035Z packages/core/src/core/workspace.py:778: RuntimeError
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6581800Z ----------------------------- Captured stdout call -----------------------------
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6583208Z {"event": "Initialized local Git repository in workspace /tmp/tmplld_wzks", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:54.900919Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6585107Z {"event": "Created default .gitignore in /tmp/tmplld_wzks/.gitignore", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:54.901091Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.6586973Z {"event": "Failed to commit changes: Command '['git', 'commit', '-m', 'initial commit']' returned non-zero exit status 128.", "level": "error", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:54.913857Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8687143Z {"event": "Failed to revert file /diff_test.txt: Command '['git', 'checkout', 'HEAD', '--', '/tmp/tmplld_wzks/diff_test.txt']' returned non-zero exit status 128.", "level": "error", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:54.928884Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8690188Z _________________ test_workspace_config_and_remote_operations __________________
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8691065Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8691558Z client = <starlette.testclient.TestClient object at 0x7f72f5beff00>
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8692140Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8692495Z     def test_workspace_config_and_remote_operations(client):
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8693185Z         import subprocess
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8693660Z         import shutil
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8694393Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8694857Z         # 1. GET config initially
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8695365Z         response = client.get(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8695978Z             "/api/workspace/config", params={"session_id": "test-session"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8696640Z         )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8697056Z         assert response.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8698030Z         data = response.json()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8698541Z         assert "workspace_id" in data
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8699073Z         assert data["git_remote_url"] is None
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8699617Z         assert data["git_username"] is None
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8700162Z         assert data["has_token"] is False
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8700652Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8701065Z         # 2. Create a bare remote repository
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8701611Z         remote_dir = tempfile.mkdtemp()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8702100Z         try:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8702658Z             subprocess.run(["git", "init", "--bare"], cwd=remote_dir, check=True)
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8703325Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8703734Z             # Configure remote URL
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8704592Z             response_config = client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8705174Z                 "/api/workspace/config",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8705674Z                 json={
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8706128Z                     "session_id": "test-session",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8706707Z                     "git_remote_url": remote_dir,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8707260Z                     "git_username": "test-user",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8707812Z                     "git_token": "test-token",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8708315Z                 },
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8708706Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8709154Z             assert response_config.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8709797Z             assert response_config.json()["success"] is True
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8710382Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8710792Z             # Verify settings updated in GET
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8711313Z             response = client.get(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8711960Z                 "/api/workspace/config", params={"session_id": "test-session"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8712640Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8713046Z             data = response.json()
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8713574Z             assert data["git_remote_url"] == remote_dir
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8714405Z             assert data["git_username"] == "test-user"
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8715008Z             assert data["has_token"] is True
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8715522Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8715936Z             # 3. Create a local file and commit it
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8716470Z             client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8716932Z                 "/api/workspace/files",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8717420Z                 json={
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8717869Z                     "session_id": "test-session",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8718416Z                     "path": "/push_test.txt",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8718934Z                     "type": "file",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8719400Z                 },
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8719794Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8720466Z             client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8720953Z                 "/api/workspace/git/commit",
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8721630Z                 json={"session_id": "test-session", "message": "feat: test remote push"},
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8722307Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8722703Z     
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8723095Z             # 4. Push to remote
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8723570Z             push_res = client.post(
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8724406Z                 "/api/workspace/git/push", json={"session_id": "test-session"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8725125Z             )
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8725683Z >           assert push_res.status_code == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8726174Z E           assert 500 == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8726716Z E            +  where 500 = <Response [500 Internal Server Error]>.status_code
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8727213Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8727520Z apps/api/tests/test_workspace_api.py:383: AssertionError
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8728228Z ----------------------------- Captured stdout call -----------------------------
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8728949Z Initialized empty Git repository in /tmp/tmph_gm5qn9/
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8730094Z {"event": "Initialized local Git repository in workspace /tmp/tmp89takbty", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:55.347713Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8732003Z {"event": "Created default .gitignore in /tmp/tmp89takbty/.gitignore", "level": "info", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:55.347879Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8733915Z {"event": "Failed to commit changes: Command '['git', 'commit', '-m', 'feat: test remote push']' returned non-zero exit status 128.", "level": "error", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:55.360507Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8736812Z {"event": "Failed to push changes: Command '['git', 'push', '/tmp/tmph_gm5qn9', 'master']' returned non-zero exit status 1.\nStderr: error: src refspec master does not match any\nerror: failed to push some refs to '/tmp/tmph_gm5qn9'\n", "level": "error", "trace_id": "no-active-span", "timestamp": "2026-06-05T15:58:55.369119Z"}
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8738816Z ----------------------------- Captured stderr call -----------------------------
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8739645Z hint: Using 'master' as the name for the initial branch. This default branch name
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8740506Z hint: will change to "main" in Git 3.0. To configure the initial branch name
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8741346Z hint: to use in all of your new repositories, which will suppress this warning,
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8742011Z hint: call:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8742361Z hint:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8742789Z hint: 	git config --global init.defaultBranch <name>
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8743305Z hint:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8743798Z hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8744905Z hint: 'development'. The just-created branch can be renamed via this command:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8745561Z hint:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8745922Z hint: 	git branch -m <name>
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8746349Z hint:
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8746894Z hint: Disable this message with "git config set advice.defaultBranchName false"
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8747634Z =============================== warnings summary ===============================
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8748322Z .venv/lib/python3.13/site-packages/fastapi/testclient.py:1
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8749876Z   /home/runner/work/wright/wright/.venv/lib/python3.13/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8751472Z     from starlette.testclient import TestClient as TestClient  # noqa
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8751998Z 
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8752408Z -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8753167Z =========================== short test summary info ============================
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8754212Z FAILED apps/api/tests/test_workspace_api.py::test_git_status_and_commit - assert 500 == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8755401Z  +  where 500 = <Response [500 Internal Server Error]>.status_code
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8756888Z FAILED apps/api/tests/test_workspace_api.py::test_git_diff_and_revert - RuntimeError: Failed to revert file: Command '['git', 'checkout', 'HEAD', '--', '/tmp/tmplld_wzks/diff_test.txt']' returned non-zero exit status 128.
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8758659Z FAILED apps/api/tests/test_workspace_api.py::test_workspace_config_and_remote_operations - assert 500 == 200
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8759627Z  +  where 500 = <Response [500 Internal Server Error]>.status_code
python-quality	Run Tests with pytest	2026-06-05T15:58:55.8760343Z =================== 3 failed, 42 passed, 1 warning in 2.93s ====================
python-quality	Run Tests with pytest	2026-06-05T15:58:56.0750339Z ##[error]Process completed with exit code 1.
```

---

# Selected sidecar derivative; no change to the Wright base image or upstream kit.
FROM ghcr.io/casys-ai/mcp-modelica@sha256:326784ce8ac6608ac7ec9047b4c5e13643bf94a6cdb417917a4131e465db0d4e
COPY . /app/
WORKDIR /app
# Native compiler facts, never manually fabricated metadata.
RUN deno run --cached-only --allow-read=/app,/opt/modelica-libraries --allow-write=/app/models --allow-run=omc scripts/derive-wright-parameter-schema.ts
RUN deno check --cached-only server.ts

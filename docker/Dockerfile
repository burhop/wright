# =============================================================================
# Wright Agent Container — Full Stack Production Image
# =============================================================================
# Includes: Wright API + Frontend, Hermes Agent, Hermes WebUI, OpenSCAD
# Managed by supervisord (Wright API on :8000, Hermes WebUI on :8788 internal)
# =============================================================================

# Stage 1: Build the Vite frontend
FROM node:26-slim AS web-builder
WORKDIR /workspace
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci
COPY apps/web/ apps/web/
RUN npm run build --workspace=apps/web

# Stage 2: Production runtime image
FROM ubuntu:24.04

# Prevent interactive prompts during apt commands
ENV DEBIAN_FRONTEND=noninteractive

# ── System packages (base + OpenSCAD + Xvfb + supervisor) ─────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    git \
    build-essential \
    ca-certificates \
    sudo \
    vim \
    nano \
    htop \
    jq \
    gnupg \
    supervisor \
    openscad \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# ── Python 3.13 (deadsnakes PPA) ──────────────────────────────────────────
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.13 \
    python3.13-venv \
    python3.13-dev \
    pipx \
    && rm -rf /var/lib/apt/lists/*

# ── Node.js 22 ────────────────────────────────────────────────────────────
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# ── uv (Python package manager) ───────────────────────────────────────────
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ── micromamba ─────────────────────────────────────────────────────────────
RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
    | tar -xvj -C /usr/local bin/micromamba

# ── Create agent user (UID 1000) ──────────────────────────────────────────
RUN userdel -r ubuntu && \
    useradd -m -u 1000 -s /bin/bash agent && \
    echo "agent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# ── Install Hermes Agent from PyPI (pinned version) ───────────────────────
# Uses uv tool install for an isolated venv with CLI on PATH
ENV UV_TOOL_DIR=/opt/uv-tools
ENV UV_TOOL_BIN_DIR=/usr/local/bin
RUN uv tool install hermes-agent==0.15.2 --python 3.13

# ── Install Hermes WebUI from GitHub (pinned tag) ─────────────────────────
# The WebUI imports hermes-agent at runtime, so it must be in the same venv.
RUN git clone --branch v0.51.135 --depth 1 \
    https://github.com/nesquena/hermes-webui.git /opt/hermes-webui && \
    uv venv /opt/hermes-webui/.venv --python 3.13 && \
    uv pip install --python /opt/hermes-webui/.venv/bin/python \
        -r /opt/hermes-webui/requirements.txt \
        hermes-agent==0.15.2 && \
    chown -R agent:agent /opt/hermes-webui

# ── Wright workspace setup ────────────────────────────────────────────────
WORKDIR /workspace
RUN chown agent:agent /workspace

# Copy dependency configs first for better layer caching
COPY pyproject.toml uv.lock ./
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY packages/core/pyproject.toml packages/core/pyproject.toml
COPY packages/agent_adapters/pyproject.toml packages/agent_adapters/pyproject.toml
COPY packages/tool_registry/pyproject.toml packages/tool_registry/pyproject.toml
COPY packages/data_vault/pyproject.toml packages/data_vault/pyproject.toml

# Sync dependencies using Python 3.13 (no dev packages)
RUN uv sync --python 3.13 --all-packages --no-install-workspace --no-dev

# Copy python codebases
COPY packages/ packages/
COPY apps/api/ apps/api/

# Re-run uv sync to install the workspace itself
RUN uv sync --python 3.13 --all-packages --no-dev

# ── Copy built frontend from Stage 1 ──────────────────────────────────────
COPY --from=web-builder /workspace/apps/web/dist /workspace/apps/web/dist

# ── Container manifest (read-only, baked into image) ──────────────────────
COPY docker/container-manifest.md /container-manifest.md
RUN chmod 444 /container-manifest.md

# ── OpenSCAD headless wrapper ─────────────────────────────────────────────
COPY scripts/openscad-headless.sh /usr/local/bin/openscad-headless
RUN chmod +x /usr/local/bin/openscad-headless

# ── Supervisord configuration ─────────────────────────────────────────────
COPY docker/supervisord.conf /etc/supervisor/conf.d/wright.conf

# ── Entrypoint script ─────────────────────────────────────────────────────
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ── Fix ownership ─────────────────────────────────────────────────────────
RUN chown -R agent:agent /workspace

# ── Log directories ───────────────────────────────────────────────────────
RUN touch /var/log/agent-startup.log /var/log/agent-changes.log && \
    chown agent:agent /var/log/agent-startup.log /var/log/agent-changes.log && \
    chmod 664 /var/log/agent-startup.log /var/log/agent-changes.log

# Supervisor needs writable log directory
RUN mkdir -p /var/log/supervisor && \
    chown -R agent:agent /var/log/supervisor

# ── OCI Image Metadata Labels ─────────────────────────────────────────────
ARG VERSION=unknown
ARG REVISION=unknown
ARG CREATED=unknown

LABEL org.opencontainers.image.title="Wright" \
      org.opencontainers.image.description="Local-first AI mechanical engineer — CAD generation, FEA, and manufacturing automation powered by multi-agent LLMs" \
      org.opencontainers.image.url="https://github.com/burhop/wright" \
      org.opencontainers.image.source="https://github.com/burhop/wright" \
      org.opencontainers.image.documentation="https://burhop.github.io/wright/" \
      org.opencontainers.image.vendor="burhop" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.created="${CREATED}"

# ── Runtime user and working directory ────────────────────────────────────
USER agent
WORKDIR /home/agent

# Wright API (external)
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/wright.conf"]

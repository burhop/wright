# =============================================================================
# Wright Agent Container - Full Stack Production Image
# =============================================================================
# Includes: Wright API + Frontend, Hermes Agent, Hermes WebUI.
# MCP-specific host software is installed during selected MCP validation/use.
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
FROM ubuntu:26.04

ENV DEBIAN_FRONTEND=noninteractive

# System packages: Wright runtime, operator utilities, and supervisor.
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    git \
    bzip2 \
    ca-certificates \
    sudo \
    vim \
    nano \
    htop \
    jq \
    gnupg \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Python 3.13.
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.13 \
    python3.13-venv \
    python3.13-dev \
    pipx \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get purge -y --auto-remove software-properties-common gnupg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# uv and micromamba support dynamic MCP package/dependency installation.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
    | tar -xvj -C /usr/local bin/micromamba

# Create agent user (UID 1000).
RUN userdel -r ubuntu && \
    useradd -m -u 1000 -s /bin/bash agent && \
    echo "agent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install Hermes Agent from PyPI with the Wright plugin in the same tool env.
ENV UV_TOOL_DIR=/opt/uv-tools
ENV UV_TOOL_BIN_DIR=/usr/local/bin
COPY hermes-plugin-wright/ /opt/hermes-plugins/wright/
RUN uv tool install hermes-agent==0.15.2 --python 3.13 --with /opt/hermes-plugins/wright/ && \
    rm -rf /root/.cache/uv

# Wright workspace setup.
WORKDIR /workspace
RUN chown agent:agent /workspace

USER agent

# Copy dependency configs first for better layer caching.
COPY --chown=agent:agent pyproject.toml uv.lock ./
COPY --chown=agent:agent apps/api/pyproject.toml apps/api/pyproject.toml
COPY --chown=agent:agent packages/core/pyproject.toml packages/core/pyproject.toml
COPY --chown=agent:agent packages/agent_adapters/pyproject.toml packages/agent_adapters/pyproject.toml
COPY --chown=agent:agent packages/tool_registry/pyproject.toml packages/tool_registry/pyproject.toml
COPY --chown=agent:agent packages/data_vault/pyproject.toml packages/data_vault/pyproject.toml

# Sync dependencies using Python 3.13 without dev packages.
RUN uv sync --python 3.13 --all-packages --no-install-workspace --no-dev && \
    rm -rf /home/agent/.cache/uv

COPY --chown=agent:agent packages/ packages/
COPY --chown=agent:agent apps/api/ apps/api/

# Install the workspace packages.
RUN uv sync --python 3.13 --all-packages --no-dev && \
    rm -rf /home/agent/.cache/uv

# Copy built frontend from Stage 1.
COPY --chown=agent:agent --from=web-builder /workspace/apps/web/dist /workspace/apps/web/dist

# Generate backend third-party license file using pip-licenses via uv.
RUN uv run --no-dev --with pip-licenses pip-licenses --with-license-file --output-file=/workspace/apps/web/dist/third-party-licenses-api.txt && \
    rm -rf /home/agent/.cache/uv

USER root

COPY docker/container-manifest.md /container-manifest.md
RUN chmod 444 /container-manifest.md

COPY docker/supervisord.conf /etc/supervisor/conf.d/wright.conf

COPY docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

RUN touch /var/log/agent-startup.log /var/log/agent-changes.log && \
    chown agent:agent /var/log/agent-startup.log /var/log/agent-changes.log && \
    chmod 664 /var/log/agent-startup.log /var/log/agent-changes.log

RUN mkdir -p /var/log/supervisor && \
    chown -R agent:agent /var/log/supervisor

ARG VERSION=unknown
ARG REVISION=unknown
ARG CREATED=unknown

LABEL org.opencontainers.image.title="Wright" \
      org.opencontainers.image.description="Local-first AI mechanical engineer - CAD generation, FEA, and manufacturing automation powered by multi-agent LLMs" \
      org.opencontainers.image.url="https://github.com/burhop/wright" \
      org.opencontainers.image.source="https://github.com/burhop/wright" \
      org.opencontainers.image.documentation="https://burhop.github.io/wright/" \
      org.opencontainers.image.vendor="burhop" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.created="${CREATED}"

USER agent
WORKDIR /home/agent

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/wright.conf"]

# =============================================================================
# Wright Agent Container - Full Stack Production Image
# =============================================================================
# Includes: Wright API + Frontend, Hermes Agent gateway integration.
# MCP-specific host software is installed during selected MCP validation/use.
# Managed by supervisord (Wright API on :8000, Hermes gateway on :8642 internal)
# =============================================================================

# Stage 1: Build the Vite frontend
FROM node:26-slim AS web-builder
WORKDIR /workspace
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci
COPY apps/web/ apps/web/
RUN npm run build --workspace=apps/web

# Stage 2: Clean Hermes runtime base built from public sources.
FROM python:3.13-slim AS hermes-base

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/opt/hermes/bin:/opt/hermes/.venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
ENV HERMES_HOME=/home/agent/.hermes

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN uv venv /opt/hermes/.venv --python /usr/local/bin/python3.13 && \
    uv pip install --python /opt/hermes/.venv/bin/python hermes-agent==0.17.0 aiohttp && \
    mkdir -p /opt/hermes/bin && \
    ln -s /opt/hermes/.venv/bin/hermes /opt/hermes/bin/hermes && \
    rm -rf /root/.cache/uv

# Stage 3: Production runtime image
FROM hermes-base

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/opt/hermes/bin:/opt/hermes/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV HOME=/home/agent
ENV HERMES_HOME=/home/agent/.hermes
ENV HERMES_PROFILE=wright
ENV DATABASE_PATH=/home/agent/.local/share/wright/state.db

# System packages: Wright operator utilities and supervisor. Hermes, Python,
# Node.js, and uv come from the Hermes base image.
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    bzip2 \
    ca-certificates \
    curl \
    sudo \
    vim \
    nano \
    htop \
    jq \
    gnupg \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# micromamba supports dynamic MCP package/dependency installation.
RUN curl --fail --location --retry 5 --retry-all-errors \
        --output /tmp/micromamba.tar.bz2 \
        https://micro.mamba.pm/api/micromamba/linux-64/latest && \
    tar -xjf /tmp/micromamba.tar.bz2 -C /usr/local bin/micromamba && \
    rm -f /tmp/micromamba.tar.bz2

# Keep the inherited Hermes runtime patched for public-alpha image scans.
RUN uv pip install --python /opt/hermes/.venv/bin/python --upgrade \
        "cryptography>=49.0.0" \
        "python-multipart>=0.0.32" \
        "starlette>=1.3.1" \
        "tornado>=6.5.6" && \
    rm -rf /root/.cache/uv /home/agent/.cache/uv

# Create agent user (UID 1000).
RUN useradd -m -u 1000 -s /bin/bash agent && \
    echo "agent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    chown -R agent:agent /home/agent

# Wright workspace setup.
WORKDIR /workspace
RUN chown agent:agent /workspace

USER agent

# Copy dependency configs first for better layer caching.
COPY --chown=agent:agent pyproject.toml uv.lock ./
COPY --chown=agent:agent apps/api/pyproject.toml apps/api/pyproject.toml
COPY --chown=agent:agent hermes-plugin-wright/pyproject.toml hermes-plugin-wright/pyproject.toml
COPY --chown=agent:agent packages/core/pyproject.toml packages/core/pyproject.toml
COPY --chown=agent:agent packages/agent_adapters/pyproject.toml packages/agent_adapters/pyproject.toml
COPY --chown=agent:agent packages/tool_registry/pyproject.toml packages/tool_registry/pyproject.toml
COPY --chown=agent:agent packages/data_vault/pyproject.toml packages/data_vault/pyproject.toml
COPY --chown=agent:agent packages/workspace_service/pyproject.toml packages/workspace_service/pyproject.toml

# Sync dependencies using Python 3.13 without dev packages.
RUN uv sync --python 3.13 --all-packages --no-install-workspace --no-dev && \
    rm -rf /home/agent/.cache/uv

COPY --chown=agent:agent packages/ packages/
COPY --chown=agent:agent apps/api/ apps/api/
COPY --chown=agent:agent hermes-plugin-wright/ hermes-plugin-wright/

USER root

# Install the Wright plugin in the Hermes runtime with its local package
# dependencies after the workspace sources are available.
RUN uv pip install --python /opt/hermes/.venv/bin/python \
        /workspace/packages/core \
        /workspace/packages/tool_registry \
        /workspace/hermes-plugin-wright && \
    rm -rf /root/.cache/uv /home/agent/.cache/uv && \
    chown -R agent:agent /home/agent

USER agent

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
      org.opencontainers.image.description="Public-alpha, local-first agent orchestration for physical engineering workflows" \
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

# =============================================================================
# Wright Agent Container - Full Stack Production Image
# =============================================================================
# Includes: Wright API + Frontend, Hermes Agent gateway integration.
# MCP-specific host software is installed during selected MCP validation/use.
# Managed by supervisord (Wright API on :8000, Hermes gateway on :8642 internal)
# =============================================================================

# Stage 1: Build the Vite frontend
FROM node:26.5.1-slim@sha256:deae974a69e140f44f434ab29cb519fb5f8fe250fd364b8ca446bd0761acdc6a AS web-builder
WORKDIR /workspace
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci
COPY apps/web/ apps/web/
RUN npm run build --workspace=apps/web

# Stage 2: Clean Hermes runtime base built from public sources.
FROM python:3.13.13-slim@sha256:aa938a849bcb82dce8f49480f056ab82bf5c1c3ebc294f0430f37b6820e7f286 AS hermes-base

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/opt/hermes/bin:/opt/hermes/.venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
ENV HERMES_HOME=/home/agent/.hermes

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.26@sha256:9a23023be68b2ed09750ae636228e903a54a05ea56ed03a934d00fe9fbeded4b /uv /usr/local/bin/uv

RUN uv venv /opt/hermes/.venv --python /usr/local/bin/python3.13 && \
    uv pip install --python /opt/hermes/.venv/bin/python \
        hermes-agent==0.19.0 aiohttp==3.13.3 && \
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
ENV FRONTEND_DIST_DIR=/workspace/apps/web/dist
ENV WRIGHT_WORKSPACES_DIR=/home/agent/workspace
ENV WRIGHT_WORKSPACE_PATH=/home/agent/workspace
ENV WRIGHT_MCP_BUNDLE=
ENV WRIGHT_MCP_HERMES_CONFIG=
ENV WRIGHT_MCP_STATUS=

# System packages: Wright operator utilities and supervisor. Hermes, Python,
# Node.js, and uv come from the Hermes base image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    bzip2 \
    ca-certificates \
    curl \
    libssl3t64 \
    openssl \
    openssl-provider-legacy \
    vim \
    nano \
    htop \
    jq \
    gnupg \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# micromamba supports dynamic MCP package/dependency installation. Keep the
# archive URL/checksum architecture-specific so native GB10/arm64 builds do not
# accidentally download the linux-64 artifact.
ARG TARGETARCH
ARG MICROMAMBA_VERSION=2.5.0
ARG MICROMAMBA_AMD64_SHA256=cec496f2299f9ceb5f5e23fc2ccf081fffda0c4bc87a6fdab575bf1e04f103b6
ARG MICROMAMBA_ARM64_SHA256=6ec1517c8c89c875a8fa93f9c66abd4fe3dd147341376bdc37b57c526bc13e44
RUN set -eux; \
    case "${TARGETARCH:-amd64}" in \
      amd64) micromamba_arch="linux-64"; micromamba_sha="${MICROMAMBA_AMD64_SHA256}" ;; \
      arm64) micromamba_arch="linux-aarch64"; micromamba_sha="${MICROMAMBA_ARM64_SHA256}" ;; \
      *) echo "Unsupported Docker TARGETARCH for micromamba: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    curl --fail --location --retry 5 --retry-all-errors \
        --output /tmp/micromamba.tar.bz2 \
        "https://micro.mamba.pm/api/micromamba/${micromamba_arch}/${MICROMAMBA_VERSION}"; \
    echo "${micromamba_sha}  /tmp/micromamba.tar.bz2" | sha256sum --check --strict; \
    tar -xjf /tmp/micromamba.tar.bz2 -C /usr/local bin/micromamba && \
    rm -f /tmp/micromamba.tar.bz2

# Keep the inherited Hermes runtime patched for public-alpha image scans.
# Hermes 0.19.0 exactly pins older cryptography and Pillow releases. Wright
# installs the security-fixed releases below and the exact-image smoke gate
# runs `uv pip check`, accepting only those two version-specific metadata
# conflicts through scripts/reconcile_hermes_pip_check.py. Trivy remains
# independently blocking for all non-exempt fixable High/Critical findings.
RUN uv pip install --python /opt/hermes/.venv/bin/python \
        "cryptography==49.0.0" \
        "pillow==12.3.0" \
        "pyasn1==0.6.4" \
        "python-multipart==0.0.32" \
        "starlette==1.3.1" \
        "tornado==6.5.6" && \
    rm -rf /root/.cache/uv /home/agent/.cache/uv

# Create agent user (UID 1000).
RUN useradd -m -u 1000 -s /bin/bash agent && \
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
COPY --chown=agent:agent README.md README.md
COPY --chown=agent:agent src/ src/

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
RUN chmod 444 /etc/supervisor/conf.d/wright.conf

COPY docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod 755 /entrypoint.sh

RUN touch /var/log/agent-startup.log /var/log/agent-changes.log && \
    chown agent:agent /var/log/agent-startup.log /var/log/agent-changes.log && \
    chmod 664 /var/log/agent-startup.log /var/log/agent-changes.log

RUN mkdir -p /var/log/supervisor && \
    chown -R agent:agent /var/log/supervisor

RUN mkdir -p /home/agent/.config /home/agent/.cache /home/agent/.local/share && \
    chown -R agent:agent /home/agent/.config /home/agent/.cache /home/agent/.local

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

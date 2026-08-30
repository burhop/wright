# =============================================================================
# Wright Agent Container - Full Stack Production Image
# =============================================================================
# Includes: Wright API + Frontend, Hermes Agent gateway integration.
# MCP-specific host software is installed during selected MCP validation/use.
# Managed by supervisord (Wright API on :8000, Hermes gateway on :8642 internal)
# =============================================================================

# Stage 1: Build the Vite frontend
FROM node:26-slim@sha256:4ebb5ace66f15a24c14c492e01a8beeed4fddf970a856109f5126e703e5fe503 AS web-builder
WORKDIR /workspace
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci
# npm 12.0.2 still bundles fixed upstream dependencies at vulnerable versions.
# Replace only those three nested packages in a temporary clean project so the
# global npm CLI remains functional without inheriting a vulnerable bundle.
RUN npm install --global npm@12.0.2
RUN set -eux; \
    mkdir -p /tmp/npm-security-overrides; \
    cd /tmp/npm-security-overrides; \
    npm init -y >/dev/null; \
    npm install --omit=dev brace-expansion@5.0.9 ip-address@10.3.1 tar@7.5.22 >/dev/null; \
    rm -rf /usr/local/lib/node_modules/npm/node_modules/brace-expansion /usr/local/lib/node_modules/npm/node_modules/ip-address /usr/local/lib/node_modules/npm/node_modules/tar; \
    cp -a node_modules/brace-expansion /usr/local/lib/node_modules/npm/node_modules/brace-expansion; \
    cp -a node_modules/ip-address /usr/local/lib/node_modules/npm/node_modules/ip-address; \
    cp -a node_modules/tar /usr/local/lib/node_modules/npm/node_modules/tar; \
    node -e "const version=require('/usr/local/lib/node_modules/npm/node_modules/tar/package.json').version; if(version !== '7.5.22') throw new Error('unexpected npm tar override '+version)"; \
    rm -rf /tmp/npm-security-overrides
COPY apps/web/ apps/web/
RUN npm run build --workspace=apps/web

# Stage 2: Clean Hermes runtime base built from public sources.
FROM python:3.13-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a AS hermes-base

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/opt/hermes/bin:/opt/hermes/.venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
ENV HERMES_HOME=/home/agent/.hermes

RUN apt-get update && apt-get install -y --no-install-recommends \
    bsdutils \
    ca-certificates \
    curl \
    git \
    libblkid1 \
    liblastlog2-2 \
    libmount1 \
    libsmartcols1 \
    libuuid1 \
    login \
    mount \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.26@sha256:9a23023be68b2ed09750ae636228e903a54a05ea56ed03a934d00fe9fbeded4b /uv /usr/local/bin/uv

RUN uv pip install --system "msgpack==1.2.1" "setuptools==84.0.0" && \
    rm -rf /root/.cache/uv

# pip 26.2.1 vendors vulnerable msgpack and a deprecated setuptools
# pkg_resources compatibility module. The supported pip CLI does not use that
# module, so replace msgpack, remove it, and update its inventory together.
RUN set -eux; \
    pip_vendor=/usr/local/lib/python3.13/site-packages/pip/_vendor; \
    mkdir -p /tmp/pip-security-overrides; \
    uv pip install --target /tmp/pip-security-overrides "msgpack==1.2.1"; \
    rm -rf "${pip_vendor}/msgpack" "${pip_vendor}/pkg_resources"; \
    cp -a /tmp/pip-security-overrides/msgpack "${pip_vendor}/msgpack"; \
    sed -i \
      -e "s/msgpack==1.1.2/msgpack==1.2.1/" \
      -e "s/setuptools==70.3.0/setuptools==78.1.1/" \
      "${pip_vendor}/vendor.txt"; \
    sed -i \
      -e "s/msgpack@1.1.2/msgpack@1.2.1/g" \
      -e "s/setuptools@70.3.0/setuptools@78.1.1/g" \
      "${pip_vendor}/bom.cdx.json"; \
    rm -rf /tmp/pip-security-overrides /root/.cache/uv

RUN uv venv /opt/hermes/.venv --python /usr/local/bin/python3.13 && \
    uv pip install --python /opt/hermes/.venv/bin/python \
        hermes-agent==0.19.0 aiohttp==3.14.3 && \
    mkdir -p /opt/hermes/bin && \
    ln -s /opt/hermes/.venv/bin/hermes /opt/hermes/bin/hermes && \
    rm -rf /root/.cache/uv

# Stage 3: Production runtime image
FROM debian:trixie-slim@sha256:3a39a0592364683e6bab97937b72cad5a8fa6dcbbee90edb3bb48c7f8e94f258

COPY --from=hermes-base /usr/local /usr/local
COPY --from=hermes-base /opt/hermes /opt/hermes

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
ENV WRIGHT_RIVET_WORKFLOWS_ENABLED=1
ENV WRIGHT_RIVET_RUNNER_ENABLED=1
ENV WRIGHT_RIVET_EDITOR_ENABLED=1
ENV WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED=1
ENV WRIGHT_SURFACES_ENABLED=1
ENV WRIGHT_SURFACES_LIVE_APPS_ENABLED=1

# System packages: Wright operator utilities and supervisor. Hermes, Python,
# and uv come from the Hermes base image. The Rivet runtime uses the same
# pinned Node.js distribution as the frontend build stage.
RUN apt-get update && apt-get install -y --no-install-recommends \
    bsdutils \
    bzip2 \
    ca-certificates \
    curl \
    libblkid1 \
    liblastlog2-2 \
    libmount1 \
    libsmartcols1 \
    libuuid1 \
    libatomic1 \
    libssl3t64 \
    login \
    mount \
    openssl \
    openssl-provider-legacy \
    vim \
    nano \
    htop \
    jq \
    gnupg \
    supervisor \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

COPY --from=web-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=web-builder /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && \
    ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx && \
    node --version && npm --version

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
        "cryptography==50.0.0" \
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
COPY --chown=agent:agent packages/model_registry/pyproject.toml packages/model_registry/pyproject.toml
COPY --chown=agent:agent packages/workspace_service/pyproject.toml packages/workspace_service/pyproject.toml

# Sync dependencies using Python 3.13 without dev packages.
RUN uv sync --python 3.13 --all-packages --no-install-workspace --no-dev && \
    rm -rf /home/agent/.cache/uv

COPY --chown=agent:agent packages/ packages/
COPY --chown=agent:agent apps/api/ apps/api/
COPY --chown=agent:agent hermes-plugin-wright/ hermes-plugin-wright/
COPY --chown=agent:agent README.md README.md
COPY --chown=agent:agent src/ src/
COPY --chown=agent:agent integrations/rivet/editor/ integrations/rivet/editor/
COPY --chown=agent:agent integrations/rivet/runner/ integrations/rivet/runner/

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

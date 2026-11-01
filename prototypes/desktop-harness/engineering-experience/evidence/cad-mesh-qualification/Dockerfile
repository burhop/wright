# Qualification-only selected provider composition; no Wright base-image changes.
FROM wright-desktop-oasis-selected:20261015-01 AS oasis
FROM ghcr.io/casys-ai/mcp-calculix@sha256:82ce8628279e03c8f492f156bb928e5703ea1fcb2d7c465826faf38f7389a778
COPY --from=oasis /selected /selected
COPY --from=oasis /home/agent/.local/share/uv/python /home/agent/.local/share/uv/python
ENV PYTHONPATH="" PYTHONDONTWRITEBYTECODE=1 PYVISTA_OFF_SCREEN=true
WORKDIR /workspace
ENTRYPOINT ["/selected/venv/bin/python"]
CMD ["-m", "server"]

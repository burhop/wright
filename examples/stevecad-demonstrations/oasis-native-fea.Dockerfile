# Selected-provider environment only. Never use this as Wright's base image.
# Both inputs must be recorded by digest before building. OASiS source/protocol
# remains unchanged; the second image supplies native Gmsh/CalculiX prerequisites.
ARG OASIS_IMAGE=wright-083-oasis-clean-selected:003
ARG NATIVE_FEA_IMAGE=ghcr.io/casys-ai/mcp-calculix@sha256:82ce8628279e03c8f492f156bb928e5703ea1fcb2d7c465826faf38f7389a778
FROM ${OASIS_IMAGE} AS selected_oasis
FROM ${NATIVE_FEA_IMAGE}
COPY --from=selected_oasis /selected /selected
WORKDIR /workspace
ENTRYPOINT ["/selected/uv-cache/environments-v2/472067e4499fe17e/04f42031aeb6e97f/bin/python"]
CMD ["-m", "server"]

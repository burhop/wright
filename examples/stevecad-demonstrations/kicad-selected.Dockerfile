# Isolated external provider environment, never Wright's base Docker image.
# Verify/record this prerequisite image ID before building. It contains historical
# campaign files; the entrypoint below exclusively uses a fresh upstream install.
ARG KICAD_HOST_IMAGE=wright:kicad-campaign-qualified-base-20260912
FROM ${KICAD_HOST_IMAGE}
USER root
WORKDIR /opt/stevecad-kicad
COPY . /opt/stevecad-kicad
RUN apt-get update && apt-get install --no-install-recommends -y git curl && rm -rf /var/lib/apt/lists/*
RUN test "$(git rev-parse HEAD)" = "f754c12e10210a0d40345a06050aae47191d3999"
RUN uv sync --frozen --no-dev --python /usr/bin/python3
RUN curl --fail --location --output /opt/freerouting-2.2.3.jar https://github.com/freerouting/freerouting/releases/download/v2.2.3/freerouting-2.2.3.jar
ENV FREEROUTER_JAR=/opt/freerouting-2.2.3.jar
ENV KICAD_CLI_PATH=/usr/bin/kicad-cli
ENV KICAD_SEARCH_PATHS=/workspace
USER agent
WORKDIR /workspace
ENTRYPOINT ["/opt/stevecad-kicad/.venv/bin/kicad-mcp"]
CMD []

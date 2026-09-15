# Selected prerequisite image only. Wright base remains unchanged.
FROM wright:standard-linux-amd64-mcp-isolated
USER root
RUN apt-get update && apt-get install -y --no-install-recommends kicad=9.0.2+dfsg-1 kicad-symbols=9.0.2-1 kicad-footprints=9.0.2-1 && rm -rf /var/lib/apt/lists/*
COPY source /opt/kicad-mcp
COPY repair_drc_stdout.py /opt/repair_drc_stdout.py
RUN python /opt/repair_drc_stdout.py /opt/kicad-mcp
WORKDIR /opt/kicad-mcp
ENV PYTHONPATH=""
RUN uv sync --frozen --no-dev --python 3.13
RUN kicad-cli --version && /usr/bin/python3 -c 'import pcbnew; print(pcbnew.GetBuildVersion())'
RUN mkdir -p /work && chown -R agent:agent /opt/kicad-mcp /work
USER agent
WORKDIR /work
USER root
COPY --from=eclipse-temurin@sha256:15090d159279e5c158473eccb48cd87f57b3e3a47511a797eb5a7a7ea6f86b0f /opt/java/openjdk /opt/java/openjdk
COPY freerouting-2.2.4.jar /opt/freerouting-2.2.4.jar
RUN echo 'f5ed374182900ccc78e473518bbb9f6b869f4a07159495f663a76f52bb10523b  /opt/freerouting-2.2.4.jar' | sha256sum -c - && /opt/java/openjdk/bin/java -version
ENV JAVA_HOME=/opt/java/openjdk
ENV PATH=/opt/java/openjdk/bin:$PATH
ENV FREEROUTER_JAR=/opt/freerouting-2.2.4.jar
COPY native_rule_check.py server.py /opt/wright-kicad/
USER agent
ENTRYPOINT ["/opt/kicad-mcp/.venv/bin/python", "/opt/wright-kicad/server.py"]

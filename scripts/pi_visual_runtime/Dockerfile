FROM wright:standard-linux-amd64-mcp-isolated
# Verified local base ID: sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73
# Selected companion only; the Wright base image stays unchanged.
RUN python -m venv /tmp/pi-visual-env && \
    /tmp/pi-visual-env/bin/python -m pip install --no-cache-dir \
    mcp==1.30.0 pypdf==6.9.1 pypdfium2==5.13.0 Pillow==12.3.0
ENTRYPOINT ["sleep", "infinity"]

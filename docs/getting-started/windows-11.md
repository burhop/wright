# Windows 11

Use Docker Desktop with Linux containers for Wright's public alpha. The Wright appliance is not a Windows desktop GUI container.

## Steps

1. Install Docker Desktop and enable the WSL 2 backend.
2. Configure `docker/.env` with `LLM_API_URL`, `LLM_API_KEY`, and `LLM_API_MODEL`.
3. Start Wright with the Docker quickstart.
4. Open `http://localhost:8080`.

## Verification

```powershell
curl http://localhost:8080/api/health
```

Hermes Desktop can run natively on Windows and connect to Wright or use the plugin flow; that is separate from the Linux container appliance.

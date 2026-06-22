# Quickstart: Distribution & Container Integration

This guide provides steps to install and test the plugin in both local and Docker container environments.

---

## 1. Local Development Install

To install the plugin locally in editable mode so changes are reflected instantly:

```bash
# From the repository root directory
pip install -e ./hermes-plugin-wright
```

### Verification
Run the verification script to load the registered entry point and verify imports:

```bash
python hermes-plugin-wright/verify_plugin.py
```

---

## 2. Docker Appliance Integration

To build and verify the production Docker image containing the plugin:

### Build the Image
```bash
docker build -t wright-appliance:latest -f docker/Dockerfile .
```

### Run the Container
```bash
docker run -d -p 8000:8000 --name wright-app wright-appliance:latest
```

### Verification in Container
Attach to the running container and check if the `wright` plugin is registered with Hermes:

```bash
docker exec -it wright-app /usr/local/bin/hermes plugins list
```
*(This should list `wright` as a registered and active plugin).*

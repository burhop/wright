# Quick Start (Docker Deployment)

The fastest way to deploy and run the Wright appliance is using **Docker Compose**. This packages the FastAPI gateway, React frontend, and scientific solvers (FreeCAD, CalculiX, OpenSCAD) into a single execution stack.

---

## 1. Setup Environment Variables

Create a `.env` file at the root of the project to configure your LLM backend endpoint:

```env
LLM_API_URL=https://generativelanguage.googleapis.com/v1beta
LLM_API_KEY=your-api-key-here
LLM_API_MODEL=gemini-3.5-flash
```

---

## 2. Boot the Container Stack

Run the compose command from your project root:

```bash
# Pull/Build and start containers in the background
docker compose up -d --build
```

Verify that the services are running:

```bash
docker compose ps
```

---

## 3. Access the Appliance

Once started, the services are available on the following host ports:

*   **Frontend Dashboard UI**: Open `http://localhost:8080/` in your browser.
*   **FastAPI API Swagger Docs**: Navigate to `http://localhost:8080/docs` to test endpoint routes.

---

## 4. Stopping the Services

To shut down the container runtime and stop the services:

```bash
docker compose down
```

!!! tip "Data Persistence"
    All agent workspaces, chat logs, database records, and custom configurations are preserved in local Docker volumes and will persist across restarts.

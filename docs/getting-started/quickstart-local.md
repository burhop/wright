# Quick Start (Local Setup)

For active developer iteration or environments where Docker compose is unavailable, Wright can be configured and run directly on your host machine.

---

## 1. Local Python Setup

Wright utilizes `uv` as its workspace virtual environment manager.

```bash
# 1. Install uv if not already present
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Sync workspace dependencies
uv sync
```

Create a `.env` file at the project root:
```env
LLM_API_URL=https://generativelanguage.googleapis.com/v1beta
LLM_API_KEY=your-api-key-here
LLM_API_MODEL=gemini-3.5-flash
```

---

## 2. Launch the Backend API Gateway

Run the API gateway web server:

```bash
# Activate virtual environment and start backend
source .venv/bin/activate
uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload
```

The FastAPI Swagger interactive guide will be accessible at:
`http://127.0.0.1:8000/docs`

---

## 3. Launch the Frontend Dashboard

In a separate terminal window, build and run the frontend web assets:

```bash
# Install packages
npm install

# Run the dev server
npm run dev
```

The React dashboard UI will spin up and run on:
`http://localhost:5173/`

---

## 4. Run Verification Suite

To verify that the local installation is working:

```bash
# Run backend pytest suite
pytest
```

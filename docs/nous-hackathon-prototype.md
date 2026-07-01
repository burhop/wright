# Nous Hackathon Prototype

This prototype stack is for the Hermes Agent Accelerated Business Hackathon. It
runs Wright with Hermes Agent, Stripe payment tooling, the official NemoClaw
source checkout, and a Vite dev UI for fast demo iteration.

The stack keeps the normal Wright Docker appliance untouched. It uses separate
named volumes and localhost-only ports.

## What Is Included

- Wright API on container port `8000`, host port `8088`.
- Wright Vite dev UI on container port `5173`, host port `5188`.
- Hermes gateway on container port `8642`, host port `8643`.
- Hermes optional payment skills:
  - `official/payments/stripe-link-cli`
  - `official/payments/stripe-projects`
  - `official/payments/mpp-agent`
- Stripe CLIs:
  - `stripe` from `@stripe/cli`
  - `link-cli` from `@stripe/link-cli`
  - `mppx`
- Official NemoClaw source checkout at `/opt/nemoclaw`.

NemoClaw/OpenShell policy enforcement is host/runtime infrastructure. The image
includes the official NemoClaw source checkout for reference, but the operator
should activate the NemoHermes/OpenShell gateway explicitly when a sandboxed run
is needed.

## Start

Create or update `docker/.env` with an OpenAI-compatible model endpoint:

```bash
cp docker/.env.example docker/.env
```

For a local model server on the host:

```env
LLM_API_URL=http://host.docker.internal:8000/v1
LLM_API_KEY=not-needed
LLM_API_MODEL=local-model-name
```

For the hackathon, set `LLM_API_MODEL` to the Nemotron route your provider
exposes. The image defaults Hermes to `nvidia/nemotron-3-ultra:free`, but that
still requires a configured provider or an authenticated Hermes/Nous Portal
setup.

Run:

```bash
docker compose -f docker-compose.hackathon.yml up -d --build
```

Open the fast-iteration UI:

```text
http://localhost:5188
```

Health checks:

```bash
curl http://localhost:8088/api/health
curl -H "Authorization: Bearer wright-local-dev" http://localhost:8643/health
```

## Fast Wright Code Updates

Most source changes do not need an image rebuild:

- `apps/`, `packages/`, and `hermes-plugin-wright/` are bind-mounted.
- API changes reload through `uvicorn --reload`.
- UI changes reload through Vite HMR at `http://localhost:5188`.

When Python dependencies or the Hermes plugin need to be refreshed:

```powershell
.\scripts\hackathon-update-wright.ps1
```

When the Dockerfile, package manifests, or system tooling changed:

```powershell
.\scripts\hackathon-update-wright.ps1 -Rebuild
```

Linux/macOS equivalent:

```bash
bash scripts/hackathon-update-wright.sh
bash scripts/hackathon-update-wright.sh --rebuild
```

## Stripe Setup

Inside the running container:

```bash
docker compose -f docker-compose.hackathon.yml exec agent bash
stripe --version
stripe plugin list
link-cli --help
```

For test-mode work without a full account, Stripe supports:

```bash
stripe sandbox create --email you@example.com --non-interactive
```

For real Link payments:

```bash
link-cli auth status
link-cli auth login --client-name "Wright Hackathon" --interval 5 --timeout 300
```

Treat all Stripe Projects and Link actions as real spend/provisioning flows.
Surface tier, total, provider, and approval prompts before confirming.

## NemoClaw / OpenShell Path

The container includes the official NemoClaw source checkout:

```bash
docker compose -f docker-compose.hackathon.yml exec agent bash -lc "ls /opt/nemoclaw"
```

For an actual OpenShell-enforced Hermes run, use NVIDIA's NemoHermes installer
on the host or target Linux VM:

```bash
export NEMOCLAW_AGENT=hermes
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
```

If NemoClaw is already installed:

```bash
nemohermes onboard
```

That creates and manages the OpenShell sandbox that runs Hermes. In that model,
NemoClaw is the outer runtime and Wright should be mounted, uploaded, or baked
into the NemoHermes sandbox rather than trying to make the Wright appliance
silently own OpenShell from inside another container.

## Useful Logs

```bash
docker compose -f docker-compose.hackathon.yml logs -f agent
docker compose -f docker-compose.hackathon.yml exec agent supervisorctl -c /etc/supervisor/conf.d/wright-hackathon.conf status
docker compose -f docker-compose.hackathon.yml exec agent tail -100 /var/log/hackathon-setup.log
```

Stop while keeping volumes:

```bash
docker compose -f docker-compose.hackathon.yml down
```

Reset prototype volumes:

```bash
docker compose -f docker-compose.hackathon.yml down -v
```

# MBAs — MANI Business Automation System

MBAs is the Hostinger-first foundation for **MANI Business AI**: AI employees for Indian businesses across phone, WhatsApp, web chat, and the operations dashboard.

It is deliberately a **Business Automation System**, not only a voice bot. The core owns business data, permissions, audit logs, workflows, and provider routing. Voice, LLM, telephony, calendar, payment, and WhatsApp providers plug into controlled adapters.

## First production slice

- Multi-tenant PostgreSQL schema with tenant isolation-ready fields
- FastAPI gateway with health, tenant, conversation and guarded-action endpoints
- Redis-backed background worker shell
- Next.js operations dashboard
- PostgreSQL + pgvector, Redis, Caddy, Prometheus, Grafana and Loki via Docker Compose
- LiveKit / SIP configuration templates (disabled until phone provider credentials are supplied)
- Hostinger Ubuntu deployment script and backup-aware deployment guide

## Architecture

```text
Phone / WhatsApp / Web
          |
 Communication adapters
          |
 Agent runtime -> guarded action gateway -> Business OS
          |                                  |
 Voice / LLM router                    Postgres + pgvector
          |                                  |
 Sarvam / other providers              Redis / audit log / workers
```

## Local start

```bash
make install
make dev
```

Open `http://localhost:3000` for the dashboard and `http://localhost:8000/docs` for the API.

The development overlay binds the dashboard and API to the loopback interface only. The base, deployment-oriented Compose stack publishes only Caddy on ports 80/443. Common development commands are:

```bash
make setup          # create .env without overwriting an existing file
make install        # install locked frontend and backend development dependencies
make dev            # build and start the Compose stack
make check          # backend tests, frontend tests, Compose validation
make logs           # follow service logs
make down           # stop the stack
```

The API exposes `/healthz` for process liveness and `/readyz` for database readiness. Every HTTP response includes `X-Correlation-ID`; callers may supply that header to preserve an identifier across services. Application request logs are structured JSON.

## Phase boundaries

This change implements the Phase 0 foundation only. Authentication, tenant enforcement/RLS policies, car-travel operations, guarded workflow execution, agent runtime, web chat, WhatsApp, payments, LiveKit/SIP, and voice are later phases and must arrive in separate reviewed pull requests. Existing schema and API placeholders are not production-ready authorization boundaries.

See [ADR 0001](docs/adr/0001-hostinger-compose-foundation.md) for the accepted Hostinger-first deployment decision and [the deployment runbook](docs/hostinger-deployment.md) for manual host preparation. No production deployment is performed by the development workflow.

## Hostinger deployment

Use a Hostinger KVM VPS with Ubuntu 24.04, Docker Engine and a domain with DNS pointing at the VPS. See [docs/hostinger-deployment.md](docs/hostinger-deployment.md). The first deployment uses external streaming STT/TTS and LLM providers; it does not require a permanent GPU.

## Safety model

An AI worker must never directly modify business data. It requests a named action; the gateway validates the tenant, permission, payload, and approval policy, then records an immutable audit entry. Finance, refunds, destructive actions and high discounts must use human approval.

## Repository layout

```text
apps/dashboard          Next.js operator dashboard
services/api            Business API and guarded action gateway
services/worker         Background workflow worker
packages/contracts      Shared OpenAPI/domain contracts (reserved)
infrastructure          Caddy, monitoring and LiveKit templates
db/migrations           PostgreSQL schema
docs                    Architecture and deployment operations
```

## Roadmap

1. Complete car-travel pilot: leads, vehicles, quotes, bookings, payment links and WhatsApp follow-up.
2. Add LiveKit + SIP and Sarvam streaming speech adapters.
3. Add the agent runtime, knowledge ingestion and evaluation suite.
4. Add subscription metering, tenant onboarding and industry templates.

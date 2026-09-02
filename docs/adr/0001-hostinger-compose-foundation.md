# ADR 0001: Hostinger-first Compose foundation

- Status: Accepted
- Date: 2026-09-02

## Context

The first MBAs pilot needs a low-complexity, affordable deployment that retains clear service boundaries and can grow after evidence shows a need.

## Decision

Run the foundation on an Ubuntu 24.04 Hostinger VPS with Docker Compose. Caddy is the only public entry point. FastAPI, Next.js, PostgreSQL with pgvector, Redis, and the worker remain on private Compose networks. AI inference stays with external providers, so no permanent GPU is required.

Kubernetes, voice, telephony, WhatsApp, and payment integrations are outside Phase 0.

## Consequences

Operations stay understandable for the pilot and all configuration remains versioned. The single host is not highly available; backups, restore drills, capacity monitoring, and a later evidence-based scaling decision are required before production readiness.

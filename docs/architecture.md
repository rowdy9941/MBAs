# MBAs architecture decisions

## Core boundary

MBAs owns tenants, businesses, customers, conversations, business records, permissions, workflow state and audit events. Models and communications providers are replaceable adapters.

## Request path

1. A channel adapter authenticates and normalizes an inbound event.
2. The conversation service retrieves only the current business snapshot, customer memory and relevant records.
3. The agent may answer, request a tool/action, or hand off to a human.
4. The action gateway maps the action to Green, Yellow or Red risk.
5. Green actions can execute after validation; Yellow and Red remain pending for a human policy or approval workflow.
6. Every decision and result is written to `audit_events`.

## Provider routing

Start with Sarvam streaming STT/TTS for Indian language calls and an external LLM router. Add local GPU inference only when measured traffic economics justify it. The provider interface must report latency, cost, model/version, errors and fallback reason for every request.

## Tenant safety

All business records include `tenant_id`. The production API must set a request-scoped tenant database setting and enforce it using PostgreSQL RLS policies; the initial migration enables RLS so it cannot be overlooked when authentication is introduced.


# MBAs — MANI Business Automation System

## Master Product, Architecture, Engineering and Deployment Blueprint

**Document status:** Build-grade master plan  
**Version:** 1.0  
**Initial deployment target:** Hostinger VPS, Ubuntu 24.04, Docker Compose  
**Initial market:** Indian small and medium businesses  
**First pilot:** Sri Raghavendra Car Travels / car-rental and travel operations  

---

## 1. Executive summary

MBAs is the **MANI Business Automation System**: a multi-tenant Business AI Operating System that provides autonomous, governed AI employees for Indian businesses.

The product is not merely a voice bot, an ElevenLabs clone, a chatbot, a CRM wrapper, or a collection of disconnected automations. It combines:

- Phone, WhatsApp, web chat, Telegram, email and future channels.
- AI receptionists, sales agents, booking agents, support agents, collections agents and managers.
- A structured Business OS for customers, leads, services, inventory, bookings, orders, invoices, payments and tasks.
- Shared customer identity, memory and conversation history across every channel.
- Indian-language voice and text intelligence, including Telugu, Hindi, English, Hinglish and Telglish.
- Deterministic tools and workflows that execute real business actions safely.
- Knowledge ingestion from websites, PDFs, spreadsheets, documents, FAQs and business databases.
- Provider-independent routing for STT, TTS, LLMs, telephony and integrations.
- Evaluation, cost accounting, auditability, approval gates and human handoff.

The central promise is:

> **A business owner can create an AI employee that answers customers, understands the business, performs approved operations, remembers context, and improves outcomes across phone, WhatsApp and web.**

The initial system must be affordable and deployable on a Hostinger VPS. Expensive AI inference remains external until measured usage justifies a dedicated GPU. The architecture must be modular enough to move to multiple VPS nodes, private cloud, on-premise GPU infrastructure or Kubernetes later without rewriting the product core.

---

## 2. Product vision and positioning

### 2.1 Product category

MBAs creates a new category between CRM, contact centre, workflow automation and AI agents:

**AI Workforce + Business Operating System for Indian businesses.**

### 2.2 What customers buy

Customers do not primarily buy AI tokens or voice minutes. They buy measurable business results:

- More calls answered.
- Faster lead response.
- More bookings and appointments.
- Fewer missed follow-ups.
- Consistent multilingual customer support.
- Lower administrative workload.
- Better customer records and operational visibility.
- Safe automation with human approval for sensitive actions.

### 2.3 Differentiation

MBAs should compete on the complete operational loop:

1. Receive a customer interaction.
2. Identify the customer and language.
3. Understand the request and business context.
4. Retrieve verified facts or live operational data.
5. Perform a permitted action.
6. Verify the result.
7. Communicate the result.
8. Record the interaction and outcome.
9. Schedule follow-up when required.
10. Measure cost, latency, accuracy and conversion.

Voice quality is important, but the moat is the combination of Indian-language intelligence, business memory, structured operations, safe tool execution, omnichannel identity and continuous evaluation.

### 2.4 Initial customer segments

Start with businesses where calls and WhatsApp messages directly lead to bookings or revenue:

1. Car travel and taxi businesses.
2. Clinics and diagnostic centres.
3. Salons and wellness centres.
4. Hotels and small hospitality operators.
5. Restaurants and catering.
6. Real-estate agencies.
7. Education and coaching centres.
8. Local service businesses.

Do not build every vertical simultaneously. The first production template must be car travel. Reuse the platform core and add vertical packs after the first pilot is reliable.

---

## 3. Product principles

### 3.1 Business truth before model fluency

The model must never guess prices, availability, booking status, payment status, policies or operational facts. The answer-source priority is:

1. Live tool result.
2. Structured Business OS data.
3. Verified business knowledge.
4. Customer memory.
5. Retrieved documents.
6. General model knowledge only when allowed.

### 3.2 AI proposes; control plane decides and executes

The agent plane can understand, plan, compose and request actions. The deterministic control plane authenticates, authorizes, validates, applies business rules, requests approval, executes, verifies, logs and reconciles.

An LLM must never receive unrestricted database write access, shell access, raw production credentials or direct payment authority.

### 3.3 Provider independence

STT, TTS, LLM, telephony, messaging, email, maps, calendar and payment providers must be behind internal interfaces. Every provider request records model/version, latency, cost, result, error and fallback reason.

### 3.4 Start simple operationally

Initial deployment:

- One Hostinger KVM-class VPS.
- Ubuntu 24.04.
- Docker Compose.
- PostgreSQL + pgvector.
- Redis.
- Caddy.
- FastAPI services.
- Next.js dashboard.
- External AI providers.

Do not begin with Kubernetes, Kafka, ten databases or a permanent GPU. Introduce complexity only after observability proves a need.

### 3.5 Human control is a product feature

Sensitive actions need confirmation or approval. Handoff should preserve context so a human can continue without asking the customer to repeat everything.

### 3.6 Measure every important outcome

Record latency, accuracy, tool success, cost, conversion, escalation, cancellation, customer satisfaction and provider reliability. Improvement must be evidence-driven.

---

## 4. System context

```text
Business owner / staff
        |
        v
MBAs Dashboard and Admin
        |
        v
MANI Business OS <------ Customers via phone / WhatsApp / web / Telegram / email
        |                                      |
        +------------------+-------------------+
                           v
                Communication Gateway
                           |
                           v
                   Agent Runtime
                           |
        +------------------+-------------------+
        |                  |                   |
        v                  v                   v
   Knowledge OS        Memory OS            Tool OS
        |                  |                   |
        +------------------+-------------------+
                           v
               Deterministic Control Plane
                           |
                           v
                  Business operations
```

---

## 5. Layered architecture

### Layer 0 — Experience and interfaces

User-facing surfaces:

- Business-owner dashboard.
- Staff console.
- Super-admin console.
- Customer web chat widget.
- Mobile-responsive PWA.
- Voice call experience.
- WhatsApp conversation experience.
- Future mobile apps and partner portal.

Responsibilities:

- Tenant onboarding.
- Business configuration.
- AI employee configuration.
- Live conversations and handoff.
- Approvals inbox.
- Customer/lead/booking views.
- Knowledge management.
- Workflow builder.
- Analytics, billing and usage.
- Provider and integration setup.

### Layer 1 — Edge and communication gateway

Normalizes every inbound and outbound channel into a shared event model.

Adapters:

- SIP/telephony.
- LiveKit WebRTC rooms.
- WhatsApp Business Platform.
- Web chat/WebSocket.
- Telegram.
- Email.
- SMS later.

Canonical event fields:

```text
event_id
tenant_id
business_id
channel
external_conversation_id
external_user_id
customer_identity_candidates
direction
content_type
text/audio/media
language_hint
timestamp
provider_metadata
```

The gateway validates signatures, applies rate limits, deduplicates retries, stores raw-event references, and publishes a normalized event.

### Layer 2 — Realtime voice engine

The voice pipeline is optimized for latency and interruption handling:

```text
Audio input
  -> echo/noise handling
  -> voice activity detection
  -> streaming speech-to-text
  -> language state and entity correction
  -> turn detection
  -> agent runtime
  -> response planning
  -> streaming text-to-speech
  -> audio output
```

Core capabilities:

- Barge-in: stop TTS when the customer interrupts.
- Streaming transcription.
- Endpoint detection.
- Partial-response generation.
- Short conversational voice responses.
- Call transfer and human handoff.
- DTMF support where required.
- Recording and consent policy.
- Call-quality metrics.
- Provider fallback.

Provider direction:

- LiveKit for realtime rooms/WebRTC and SIP integration.
- Indian SIP/telephony providers such as Exotel, Airtel IQ or Tata, selected after compliance and pricing validation.
- Sarvam as the primary early Indian-language STT/TTS candidate.
- Voicebox/Qwen/Chatterbox as a future voice laboratory and local/private voice option.
- Premium cloud voice provider as an optional route.

Target perceived response initiation for ordinary, non-tool turns: approximately 600–1,200 ms under healthy provider/network conditions. This is an engineering target, not a guaranteed external-provider SLA.

### Layer 3 — Indian Language Intelligence

This layer sits above raw STT and below the agent runtime.

Persistent session state:

```text
primary_language
secondary_language
script_preference
code_switching_enabled
dialect_or_region
business_vocabulary
known_locations
known_names
confidence_by_entity
```

Capabilities:

- Telugu-English code switching.
- Hindi-English code switching.
- Indian names and address normalization.
- Date/time interpretation in Asia/Kolkata.
- Indian number, currency and phone formats.
- Business-specific vocabulary biasing.
- Confidence-aware clarification.

Example:

```text
Input: "Anna repu morning Gannavaram airport ki Innova available undha?"

Intent: availability_check
Date: tomorrow
Period: morning
Destination: Gannavaram Airport
Vehicle: Innova
Language state: Telugu + English
```

If location confidence is low, the agent asks for confirmation instead of guessing.

### Layer 4 — Identity and conversation service

Unifies a customer across channels.

Responsibilities:

- Match phone numbers, WhatsApp IDs, email addresses and logged-in web identities.
- Maintain conversation lifecycle.
- Merge identity candidates with safe review rules.
- Store rolling conversation summaries.
- Link conversations to leads, bookings, orders and support cases.
- Preserve handoff context.

Identity resolution must never merge two customers solely because their names are similar.

### Layer 5 — MANI Agent Runtime

The runtime owns conversational reasoning and task planning.

Main components:

1. Session controller.
2. Intent classifier.
3. Entity extractor.
4. Context assembler.
5. Complexity and risk classifier.
6. Agent supervisor.
7. Specialist-agent router.
8. Tool-request planner.
9. Response composer.
10. Confidence evaluator.
11. Handoff controller.

Three reasoning levels:

#### Level 0 — Deterministic

For business hours, addresses, simple status checks and fixed FAQ responses. No LLM is needed when a validated template and data lookup can answer correctly.

#### Level 1 — Fast AI

For most conversational turns, intent extraction, short responses and standard tool workflows.

#### Level 2 — Deep AI

For complex itinerary planning, multi-constraint recommendations, negotiation support, ambiguous customer problems and manager analysis.

The router considers language, complexity, cost, latency budget, risk, context length, tenant plan and provider health.

### Layer 6 — AI Employee OS

Each AI employee is a versioned configuration, not a free-running model.

AI employee definition:

```text
employee_id
tenant_id
role
goal
allowed_channels
allowed_languages
business_scope
knowledge_scope
allowed_tools
approval_policy
voice_profile
prompt_version
workflow_version
model_route_policy
handoff_policy
operating_hours
evaluation_suite
status
```

Initial employees:

- Receptionist AI.
- Sales AI.
- Booking AI.
- Support AI.
- Follow-up AI.
- Collections AI.
- Manager AI.

The Supervisor coordinates specialists but cannot bypass tool permissions.

### Layer 7 — Knowledge OS

The Knowledge OS combines structured truth with document retrieval.

Ingestion pipeline:

```text
Website / PDF / spreadsheet / document / form / API
  -> source validation
  -> parsing and OCR
  -> normalization
  -> entity extraction
  -> structured fact candidates
  -> human verification where required
  -> document chunking
  -> embeddings
  -> indexing
  -> versioning and freshness policy
```

Knowledge classes:

- Structured operational data: prices, services, products, inventory, availability, branches.
- Verified knowledge: policies, approved FAQs, business rules.
- Documents: long-form policies, catalogues, manuals.
- Derived summaries: versioned and linked to sources.

Retrieval returns:

```text
source_id
source_version
fact_or_chunk
verification_status
valid_from / valid_until
confidence
tenant_scope
business_scope
```

Use PostgreSQL and pgvector first. Add a dedicated graph or vector database only if scale and retrieval quality justify it.

### Layer 8 — Memory OS

Memory is separated by purpose:

1. **Conversation memory** — current session, recent turns and rolling summary.
2. **Customer memory** — preferences, past interactions, consented personal context and relationship history.
3. **Business memory** — verified business facts, decisions and operating knowledge.
4. **Operational memory** — current assignments, failures, pending work and recent system state.
5. **Learning memory** — evaluated outcomes, lessons and approved improvements.

Memory rules:

- Every memory has tenant scope.
- Sensitive data has retention and access policies.
- Derived memory stores provenance.
- Low-confidence inferences are never treated as facts.
- Customers can be forgotten or anonymized according to policy and law.
- The prompt receives only relevant memory, not the full history.

### Layer 9 — Tool OS and deterministic control plane

This is the most important safety and reliability boundary.

Action lifecycle:

```text
Agent requests action
  -> schema validation
  -> tenant and identity validation
  -> permission check
  -> risk classification
  -> business-rule validation
  -> approval if required
  -> idempotency check
  -> execution
  -> result verification
  -> reconciliation
  -> audit event
  -> agent receives bounded result
```

Risk levels:

| Level | Examples | Behaviour |
|---|---|---|
| Green | Create lead, check availability, draft booking, send approved confirmation | Automatic after validation |
| Yellow | Modify booking, reschedule, apply limited discount, change customer record | Explicit confirmation or staff approval |
| Red | Refund, delete records, large discount, export sensitive data, financial commitment | Manager approval and stronger authentication |

Every action definition includes:

```text
name
version
input_schema
output_schema
required_permissions
risk_level
approval_policy
idempotency_policy
timeout
retry_policy
verification_handler
compensation_handler
audit_fields
```

### Layer 10 — Business OS

The Business OS is the source of truth.

Core domains:

- Tenants and subscriptions.
- Businesses and branches.
- Users, teams, roles and permissions.
- Customers and contacts.
- Leads and opportunities.
- Services and products.
- Pricing and quotations.
- Inventory and availability.
- Appointments and bookings.
- Orders and fulfilment.
- Invoices and payments.
- Employees and assignments.
- Conversations, calls and messages.
- Tasks, activities and follow-ups.
- Documents and knowledge.
- Agents, tools and workflows.
- Usage, cost and billing.
- Audit and approvals.

External CRMs are connectors. MBAs keeps a normalized internal source of truth and synchronization state.

### Layer 11 — Workflow OS

Workflows coordinate reliable long-running processes.

Example booking workflow:

```text
Lead captured
 -> requirements verified
 -> availability checked
 -> quote calculated
 -> customer confirms
 -> booking created
 -> payment link created
 -> WhatsApp confirmation sent
 -> staff/driver assignment requested
 -> reminder scheduled
 -> service completed
 -> invoice and feedback request sent
```

Workflow requirements:

- Versioned definitions.
- Durable state.
- Timeouts and retries.
- Idempotency.
- Human approval steps.
- Compensation/rollback where possible.
- Dead-letter queue.
- Full audit history.

Use a Postgres-backed job/workflow implementation during the MVP. Evaluate Temporal when workflow volume and complexity demand it.

### Layer 12 — Analytics, evaluation and learning

Analytics dimensions:

- Tenant and business.
- Channel and agent.
- Language.
- Provider and model.
- Call duration and turn latency.
- STT/TTS/LLM usage and cost.
- Tool success and failure.
- Lead conversion.
- Booking value.
- Escalation and abandonment.
- Customer satisfaction.

Evaluation pipeline:

```text
New prompt/model/workflow
 -> offline simulation
 -> regression suite
 -> safety tests
 -> multilingual tests
 -> latency/cost benchmark
 -> staff review
 -> canary release
 -> monitored comparison
 -> promote or rollback
```

Self-improvement is governed. The system may propose changes, but production changes require evaluation and approval.

---

## 6. End-to-end request flows

### 6.1 Simple deterministic question

Customer: “Are you open today?”

```text
Inbound message
 -> identity/session
 -> intent classifier
 -> business-hours lookup
 -> approved response template
 -> outbound message
 -> conversation/audit record
```

No large-model retrieval chain is required.

### 6.2 Car booking by phone

```text
Inbound SIP call
 -> LiveKit room
 -> VAD + streaming STT
 -> Telugu-English language state
 -> booking intent and entities
 -> customer match
 -> vehicle availability tool
 -> pricing tool
 -> short spoken quote
 -> customer confirmation
 -> guarded booking.create action
 -> payment link action
 -> WhatsApp confirmation
 -> follow-up workflow
 -> audit + usage metering
```

### 6.3 Sensitive refund

```text
Customer requests refund
 -> agent gathers booking and reason
 -> refund policy retrieval
 -> payment and booking verification
 -> payment.refund action request classified Red
 -> manager approval inbox
 -> manager authenticates and approves/rejects
 -> payment provider execution
 -> reconciliation
 -> customer notification
 -> immutable audit trail
```

### 6.4 Human handoff

```text
Low confidence / customer request / policy trigger
 -> agent summarizes conversation
 -> attaches verified entities and attempted actions
 -> selects staff queue
 -> transfers call or conversation
 -> staff receives full context
 -> AI remains silent or assists staff according to policy
```

---

## 7. First vertical: car travel and rental

### 7.1 Pilot goal

Create an AI receptionist and booking assistant for Sri Raghavendra Car Travels that handles Telugu, English and Hindi customer conversations, captures leads, checks availability, calculates quotes, creates bookings, sends WhatsApp confirmations and requests payment.

### 7.2 Domain model

- Vehicle category.
- Vehicle.
- Driver.
- Service type.
- Route.
- Pickup and destination.
- Schedule/availability.
- Quote.
- Booking.
- Booking passenger.
- Assignment.
- Payment.
- Expense later.
- Trip status.

### 7.3 Required workflows

1. Airport pickup/drop.
2. One-way trip.
3. Round trip.
4. Local hourly package.
5. Outstation multi-day trip.
6. Temple tour/custom itinerary.
7. Booking modification.
8. Cancellation and refund request.
9. Driver/vehicle assignment.
10. Pre-trip reminder and post-trip feedback.

### 7.4 Quote engine inputs

```text
service_type
pickup
destination
date_time
return_date_time
vehicle_category
passenger_count
luggage
distance
duration
tolls
parking
driver_allowance
night_charge
waiting_time
season/surge rule
approved discount
tax
```

The quote engine is deterministic. The agent explains the result but does not invent the price.

### 7.5 Pilot success metrics

- At least 95% of inbound leads captured with required contact details.
- At least 90% intent accuracy on the defined pilot intents.
- Zero unapproved refunds or destructive actions.
- At least 99% action audit coverage.
- Booking creation succeeds reliably under retry/idempotency tests.
- Median non-tool response initiation under the chosen practical latency target.
- Measured improvement in answered enquiries and lead-to-booking conversion.

---

## 8. Multi-tenant data architecture

### 8.1 Tenant hierarchy

```text
Tenant
  -> Business
      -> Branch
          -> Users / Agents / Customers / Records
```

Every business-domain record includes:

```text
tenant_id
business_id
branch_id where applicable
created_at
updated_at
version
created_by
```

### 8.2 Primary database

Use PostgreSQL 16+ with pgvector.

PostgreSQL owns:

- Transactional business truth.
- Workflow state.
- Identity and permissions.
- Audit metadata.
- Knowledge metadata.
- Vector embeddings during early stages.
- Usage and cost ledger.

Redis owns:

- Short-lived sessions.
- Rate limits.
- Distributed locks.
- Realtime presence.
- Caches.
- Lightweight queues during MVP.

Object storage owns:

- Call recordings when enabled.
- Uploaded documents.
- Generated exports.
- Large media.
- Backup artifacts.

### 8.3 Core tables

Identity and tenancy:

```text
tenants
subscriptions
businesses
branches
users
memberships
roles
permissions
api_keys
integration_credentials
```

CRM and operations:

```text
customers
customer_identities
contacts
leads
opportunities
services
products
price_rules
inventory_items
availability_slots
quotes
bookings
orders
invoices
payments
refund_requests
tasks
activities
```

Communications:

```text
conversations
conversation_participants
messages
calls
call_turns
handoffs
channel_connections
```

AI and knowledge:

```text
agents
agent_versions
prompts
model_routes
tools
tool_versions
workflows
workflow_runs
knowledge_sources
knowledge_documents
knowledge_chunks
memories
evaluation_suites
evaluation_runs
```

Governance:

```text
action_requests
approvals
audit_events
policy_versions
incidents
usage_events
cost_ledger
```

### 8.4 Tenant isolation

Controls:

- PostgreSQL Row-Level Security.
- Request-scoped tenant context.
- Tenant filters in repository interfaces.
- Per-tenant object-storage prefixes.
- Per-tenant encryption context for credentials.
- Cross-tenant access tests in CI.
- Super-admin access explicitly audited.

---

## 9. API architecture

### 9.1 API style

- REST/JSON for business and admin operations.
- WebSocket for realtime dashboard events and web chat.
- Webhooks for providers.
- Internal event contracts for asynchronous work.
- MCP adapters only where the tool ecosystem benefits; MCP does not replace internal authorization.

### 9.2 API groups

```text
/v1/auth
/v1/tenants
/v1/businesses
/v1/branches
/v1/customers
/v1/leads
/v1/services
/v1/quotes
/v1/bookings
/v1/invoices
/v1/payments
/v1/conversations
/v1/calls
/v1/agents
/v1/actions
/v1/approvals
/v1/workflows
/v1/knowledge
/v1/integrations
/v1/usage
/v1/analytics
/v1/admin
```

### 9.3 Request requirements

Every protected request carries resolved tenant identity, user/service identity, permissions, correlation ID and idempotency key where applicable.

### 9.4 Error contract

```json
{
  "error": {
    "code": "BOOKING_SLOT_UNAVAILABLE",
    "message": "The selected vehicle is no longer available.",
    "correlation_id": "...",
    "retryable": false,
    "details": {}
  }
}
```

Do not leak provider secrets, stack traces or cross-tenant identifiers.

---

## 10. Internal service structure

Start as a modular monorepo with a small number of deployable services:

1. **dashboard** — business owner/staff UI.
2. **admin** — platform operations UI.
3. **api** — identity, Business OS and public APIs.
4. **agent-runtime** — conversational reasoning and model routing.
5. **realtime/voice-agent** — LiveKit workers and streaming audio.
6. **worker** — workflows, integrations, knowledge jobs and scheduled work.

Keep modules inside these deployments until scaling data proves they must be separated.

Future separations:

- Dedicated realtime node.
- Dedicated knowledge workers.
- Dedicated integration workers.
- Dedicated analytics pipeline.
- Dedicated database node.
- Dedicated GPU inference service.

---

## 11. Repository structure

```text
MBAs/
├── README.md
├── MBAs_MASTER_BLUEPRINT.md
├── compose.yaml
├── .env.example
├── Makefile
│
├── apps/
│   ├── dashboard/
│   ├── admin/
│   └── customer-widget/
│
├── services/
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── auth/
│   │   │   ├── tenants/
│   │   │   ├── crm/
│   │   │   ├── bookings/
│   │   │   ├── billing/
│   │   │   ├── actions/
│   │   │   ├── approvals/
│   │   │   └── audit/
│   │   └── tests/
│   ├── agent-runtime/
│   ├── realtime/
│   ├── voice-agent/
│   ├── knowledge/
│   ├── integrations/
│   ├── workflow/
│   ├── analytics/
│   └── worker/
│
├── packages/
│   ├── business-core/
│   ├── agent-core/
│   ├── memory-core/
│   ├── knowledge-core/
│   ├── tool-core/
│   ├── voice-core/
│   ├── provider-router/
│   ├── permissions/
│   ├── contracts/
│   ├── schemas/
│   ├── observability/
│   └── sdk/
│
├── agents/
│   ├── receptionist/
│   ├── sales/
│   ├── booking/
│   ├── support/
│   ├── follow-up/
│   ├── collections/
│   └── manager/
│
├── industry/
│   ├── car-travel/
│   ├── clinic/
│   ├── salon/
│   ├── hotel/
│   ├── restaurant/
│   └── real-estate/
│
├── db/
│   ├── migrations/
│   ├── seeds/
│   └── policies/
│
├── infrastructure/
│   ├── docker/
│   ├── caddy/
│   ├── livekit/
│   ├── postgres/
│   ├── redis/
│   ├── monitoring/
│   ├── backups/
│   └── hostinger/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── e2e/
│   ├── security/
│   ├── tenant-isolation/
│   ├── agent-evals/
│   ├── voice-evals/
│   └── simulations/
│
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── operations/
│   ├── security/
│   ├── adr/
│   └── runbooks/
│
└── .github/
    ├── workflows/
    ├── ISSUE_TEMPLATE/
    └── pull_request_template.md
```

---

## 12. Technology stack

### Frontend

- Next.js + TypeScript.
- React.
- Accessible component primitives.
- Server-side data fetching where appropriate.
- WebSocket client for live events.
- PWA support after the core dashboard is stable.

### Backend

- Python 3.12.
- FastAPI.
- Pydantic.
- SQLAlchemy 2 or a clean asyncpg repository layer.
- Alembic migrations.
- Background worker with Redis/Postgres during MVP.

### Data

- PostgreSQL 16+.
- pgvector.
- Redis.
- S3-compatible object storage for production media and backups.

### Realtime and voice

- LiveKit.
- LiveKit SIP.
- TURN.
- Streaming STT/TTS adapters.
- WebRTC for web voice.

### AI

- Provider router with fast, standard and deep routes.
- External LLMs initially.
- Sarvam candidate for Indian speech.
- Small embedding/reranking models as needed.
- Future vLLM/Ollama/local inference on dedicated GPU infrastructure.

### Observability

- OpenTelemetry.
- Prometheus.
- Grafana.
- Loki.
- Structured JSON logs.
- Error tracking.

### Infrastructure

- Docker.
- Docker Compose.
- Caddy.
- GitHub Actions.
- Encrypted off-server backups.
- Infrastructure configuration versioned in Git.

---

## 13. Hostinger-first deployment

### 13.1 Initial topology

```text
Internet
   |
Caddy: HTTPS and routing
   |
   +-> Next.js dashboard
   +-> FastAPI API
   +-> WebSocket/realtime endpoints

Private Docker network
   +-> PostgreSQL + pgvector
   +-> Redis
   +-> worker
   +-> agent runtime
   +-> monitoring

External providers
   +-> LLM
   +-> STT/TTS
   +-> WhatsApp
   +-> SIP/telephony
   +-> payment/calendar/maps/email
```

Recommended starting class: KVM 8-class VPS where available, 8 vCPU, 32 GB RAM and NVMe storage. Revalidate exact Hostinger availability and pricing before purchase.

### 13.2 Public ports

- 80/TCP — HTTP redirect/ACME.
- 443/TCP — HTTPS.
- LiveKit/SIP/TURN ports only when the voice phase begins and only according to verified deployment documentation.

PostgreSQL, Redis, Grafana and internal service ports must not be publicly exposed.

### 13.3 Domain layout

```text
app.example.com       dashboard
api.example.com       API/webhooks
voice.example.com     LiveKit/realtime later
status.example.com    public status page later
```

### 13.4 Backup policy

- Daily encrypted PostgreSQL backup.
- Off-server object storage.
- Retain at least 30 daily restore points during the pilot.
- Back up uploaded documents and configuration.
- Test restoration regularly.
- Document recovery time and recovery point objectives.

### 13.5 Scaling stages

| Stage | Topology |
|---|---|
| Development | Local PC + Docker Compose |
| Internal pilot | Hostinger KVM 4/8-class node |
| Production MVP | KVM 8-class core node, external AI |
| Growth | Split realtime/voice from core |
| Further growth | Dedicated DB, workers and realtime nodes |
| High AI volume | Dedicated on-demand or owned GPU node |
| Large deployment | k3s/Kubernetes, multi-region and HA |

### 13.6 When to leave the single VPS

Scale after observing one or more of:

- Sustained CPU or memory pressure.
- Realtime voice affecting API/database latency.
- Backup or maintenance windows becoming unsafe.
- Worker backlog exceeding SLO.
- Need for high availability.
- Security requirement for isolated data services.

---

## 14. Security architecture

### 14.1 Authentication

- Secure business-user authentication.
- MFA for admins and sensitive approvals.
- Short-lived sessions/access tokens.
- Rotating refresh tokens where used.
- Service-to-service identities.
- Device/session management.

### 14.2 Authorization

- RBAC initially: owner, manager, agent, operator, analyst, viewer.
- Tenant and business scope on every permission.
- Attribute/policy rules for sensitive actions.
- Separate platform super-admin role.
- Approval separation for Red actions.

### 14.3 Secrets

- Never commit secrets.
- Encrypt integration credentials at rest.
- Do not include credentials in prompts or logs.
- Rotate provider keys.
- Use a proper secret manager as the deployment matures.

### 14.4 Data protection

- TLS in transit.
- Encrypted disks/backups.
- Field-level protection for selected sensitive data.
- Data minimization.
- Retention policies.
- Recording consent and access controls.
- Export/deletion workflows.

### 14.5 Application security

- Strict webhook signature verification.
- Rate limiting.
- Input/schema validation.
- Prompt-injection-aware tool boundary.
- File scanning and content-type validation.
- SSRF protections for website ingestion.
- Idempotency for write operations.
- Dependency and container scanning.
- Audit trail for privileged actions.

### 14.6 AI security

- Retrieved content is untrusted data, not system instruction.
- Tool permissions are independent of prompts.
- Structured tool arguments are validated.
- Model output cannot choose its own permission level.
- High-risk actions require deterministic policy and approval.
- Agent versions are immutable after release.
- Emergency agent/tool kill switch.

### 14.7 Compliance preparation

Before production in India, review applicable privacy, telecom, call recording, messaging consent, DND/DNC, payment and data-retention requirements with qualified legal/compliance professionals and selected providers.

---

## 15. Cost and margin architecture

Every interaction writes usage events:

```text
tenant_id
conversation_id
provider
model
STT seconds
TTS characters/audio seconds
LLM input/cached/output tokens
telephony minutes
messages delivered
tool calls
storage
estimated provider cost
allocated infrastructure cost
revenue allocation
gross contribution
```

Cost optimizations:

- Voice activity detection to avoid billing silence where provider billing allows.
- Streaming rather than generating long voice responses.
- Deterministic Level 0 paths.
- Prompt snapshots instead of full histories.
- Rolling conversation summaries.
- Relevant retrieval only.
- Cached business facts and model input where supported.
- Cheapest healthy provider that satisfies quality/SLO.
- Asynchronous processing for non-realtime tasks.
- Per-tenant quotas and budget alerts.

Pricing should combine a platform subscription with included usage and overage. Do not publish final prices until real pilot usage establishes cost per lead, call, booking and active tenant.

---

## 16. Observability and service objectives

### 16.1 Technical metrics

- API request rate, error rate and latency.
- Database connections, locks and slow queries.
- Redis health and queue depth.
- Webhook success and retry count.
- Provider latency, error rate and fallback.
- Realtime packet loss, jitter and disconnects.
- STT finalization time.
- Agent time-to-first-token.
- TTS time-to-first-audio.
- Tool execution time and verification failures.

### 16.2 Business metrics

- Enquiries answered.
- Leads created.
- Quotes generated.
- Bookings created.
- Revenue influenced.
- Follow-ups completed.
- Human handoffs.
- Customer abandonment.
- Cost per qualified lead/booking.

### 16.3 Initial objectives

- Core API availability target appropriate for an early pilot.
- No cross-tenant data leakage.
- No unapproved Red action.
- Near-complete audit coverage for write actions.
- Defined recovery procedure for provider failure.
- Clear operational alerts with owner and runbook.

---

## 17. Testing strategy

### 17.1 Conventional tests

- Unit tests for business rules.
- Database integration tests.
- API contract tests.
- Provider-adapter contract tests.
- End-to-end booking tests.
- Migration tests.
- Backup/restore tests.

### 17.2 Security tests

- Tenant isolation.
- Permission bypass attempts.
- Webhook forgery.
- Prompt injection.
- Tool argument tampering.
- Idempotency and replay.
- Secret leakage.
- File-ingestion abuse.

### 17.3 Agent evaluations

Test personas:

- Telugu speaker.
- Hindi speaker.
- English speaker.
- Hinglish/Telglish speaker.
- Noisy caller.
- Elderly or quiet caller.
- Angry customer.
- Confused customer.
- Price negotiator.
- Repeat customer.
- Spam/adversarial user.

Metrics:

- Intent accuracy.
- Entity accuracy.
- Knowledge groundedness.
- Booking correctness.
- Tool success.
- Hallucination rate.
- Clarification quality.
- Handoff quality.
- Latency.
- Cost.
- Conversion.

### 17.4 Release gates

A new model/prompt/workflow cannot enter production until it passes critical safety, regression and tenant-isolation tests. Release through a canary and preserve rollback.

---

## 18. Development workflow

### 18.1 Local development

Install:

- Git.
- Docker Engine and Docker Compose.
- Node.js 22.
- Python 3.12.
- Codex CLI.
- VS Code/Codex extension optionally.

Workflow:

```text
Create issue
 -> create branch
 -> write acceptance criteria
 -> implement smallest vertical slice
 -> tests and security checks
 -> review diff
 -> commit
 -> pull request
 -> CI
 -> staging
 -> approval
 -> production
```

### 18.2 Git strategy

- `main` remains deployable.
- Short-lived feature branches.
- Pull request for every meaningful change.
- Database migrations reviewed explicitly.
- Architecture decisions recorded under `docs/adr`.
- Tagged releases.
- Protected production secrets outside Git.

### 18.3 Definition of done

A feature is done only when:

- Acceptance criteria pass.
- Authorization and tenant scope are implemented.
- Audit events exist for state changes.
- Tests exist.
- Errors and retries are handled.
- Metrics/logs exist.
- Documentation is updated.
- Migration and rollback impact are understood.

---

## 19. Ninety-day implementation plan

### Phase 0 — Foundation (Days 1–7)

Deliverables:

- Confirm product boundaries and pilot scope.
- Repository standards and CI.
- Docker Compose local stack.
- PostgreSQL/Redis/Caddy.
- Environment and secret conventions.
- Core FastAPI and Next.js shells.
- Health checks, structured logs and correlation IDs.
- Architecture decision records.

Exit criteria:

- One command starts the local system.
- CI compiles/tests both backend and frontend.
- No production secret is committed.

### Phase 1 — Tenant, identity and Business OS core (Days 8–21)

Deliverables:

- Tenant/business/branch model.
- User authentication and RBAC.
- PostgreSQL RLS policies.
- Customer and lead modules.
- Service and pricing modules.
- Audit-event system.
- Basic dashboard navigation.

Exit criteria:

- Cross-tenant isolation tests pass.
- Staff can create and manage a customer/lead safely.

### Phase 2 — Car-travel operational slice (Days 22–38)

Deliverables:

- Vehicles, drivers and availability.
- Quote engine.
- Bookings.
- Booking modification/cancellation requests.
- Tasks and follow-up.
- Car-travel dashboard.

Exit criteria:

- Staff can complete lead-to-booking entirely inside MBAs.
- Quote is deterministic and reproducible.

### Phase 3 — Tool OS and workflows (Days 39–52)

Deliverables:

- Tool registry and versioned schemas.
- Green/Yellow/Red action policy.
- Approval inbox.
- Idempotent execution.
- Verification and compensation hooks.
- Booking and follow-up workflows.

Exit criteria:

- Agent-requested booking passes through the control plane.
- Red actions cannot execute without approval.

### Phase 4 — Web chat and agent runtime (Days 53–65)

Deliverables:

- Customer widget.
- Conversation and identity service.
- Model router.
- Receptionist and booking agents.
- Business context assembler.
- Confidence and clarification flow.
- Human handoff.

Exit criteria:

- A web-chat customer can obtain a verified quote and create a booking.
- Unsupported questions do not produce invented business facts.

### Phase 5 — WhatsApp and knowledge (Days 66–77)

Deliverables:

- WhatsApp webhook and outbound adapter.
- Approved templates.
- Website/document ingestion.
- Verified FAQ and policy retrieval.
- Shared customer timeline across web and WhatsApp.

Exit criteria:

- Conversation continues across channels for the same verified identity.
- Answers carry verified source/provenance internally.

### Phase 6 — Voice pilot (Days 78–86)

Deliverables:

- LiveKit deployment.
- SIP provider integration.
- Streaming STT/TTS.
- Telugu/English/Hindi language state.
- Barge-in and handoff.
- Voice latency/cost metrics.

Exit criteria:

- Controlled test calls complete the core booking flow.
- Recording/consent and telephony policies are approved.

### Phase 7 — Hardening and pilot launch (Days 87–90)

Deliverables:

- Security and tenant-isolation review.
- Backup/restore test.
- Failure drills and runbooks.
- Agent evaluation suite.
- Cost dashboard.
- Staff training.
- Limited production rollout.

Exit criteria:

- Pilot owner signs off.
- Rollback and kill switch are tested.
- Monitoring and incident ownership are active.

---

## 20. Post-90-day roadmap

### Stage A — Pilot optimization

- Improve conversion and handoff.
- Expand travel workflows.
- Tune Indian-language vocabulary.
- Build usage-based pricing from measured economics.
- Add calendar, maps, payments and accounting connectors.

### Stage B — Multi-tenant SaaS

- Self-service onboarding.
- Subscription billing.
- Usage quotas and overage.
- Tenant templates.
- Integration marketplace.
- White-label options.

### Stage C — Additional industries

- Clinic.
- Salon.
- Hotel.
- Restaurant.
- Real estate.

Each vertical pack contains schemas, workflows, tools, prompts, policies, tests, knowledge templates and dashboard views.

### Stage D — Enterprise/private MBAs

- Dedicated tenant deployments.
- Private networking.
- On-premise storage.
- Local STT/LLM/TTS.
- SSO and enterprise policy integration.
- Advanced audit and retention controls.

### Stage E — Advanced MANI autonomy

- Manager AI recommendations.
- Forecasting and staffing assistance.
- Automated workflow discovery proposals.
- Controlled experimentation.
- World-model/simulation components for operational planning.
- Governed self-improvement with evaluation and approval.

---

## 21. Build priorities and explicit non-goals

### Build first

1. Tenant isolation and permissions.
2. Structured Business OS.
3. Audit and guarded actions.
4. Car-travel booking workflow.
5. Web chat.
6. WhatsApp.
7. Knowledge.
8. Voice.
9. Cost/evaluation.
10. SaaS onboarding and vertical expansion.

### Do not build first

- Kubernetes.
- Permanent GPU cluster.
- Fully autonomous production changes.
- Dozens of verticals.
- Custom telephony infrastructure where a compliant provider is adequate.
- Separate vector, graph and analytics databases without evidence.
- Visual workflow builder before core workflows are reliable.
- Voice cloning before consent, security and business value are clear.

---

## 22. Key risks and mitigations

| Risk | Mitigation |
|---|---|
| Hallucinated prices or availability | Structured source priority and mandatory tools |
| Wrong customer identity merge | Verified identifiers and review rules |
| Cross-tenant data leakage | RLS, scoped repositories and isolation tests |
| Prompt injection triggers action | Independent tool permissions and validation |
| Duplicate bookings/payments | Idempotency keys and reconciliation |
| Voice latency | Streaming, Level 0 paths, provider routing and concise responses |
| Indian language errors | Persistent language state, vocabulary and clarification confidence |
| Provider outage | Health-aware routing, retries and human handoff |
| Costs exceed subscription | Per-event cost ledger, quotas and routing policies |
| AI change degrades quality | Evaluation gates, canary and rollback |
| Operational complexity | Modular monolith/limited services and measured scaling |
| Compliance failure | Provider/legal review, consent and retention policies before launch |

---

## 23. MVP acceptance checklist

### Platform

- [ ] Tenant onboarding works.
- [ ] Tenant isolation tests pass.
- [ ] Roles and permissions work.
- [ ] Audit events cover every state-changing action.
- [ ] Backups restore successfully.

### Car-travel Business OS

- [ ] Customers and leads.
- [ ] Vehicles and drivers.
- [ ] Services and pricing.
- [ ] Availability.
- [ ] Quotes.
- [ ] Bookings.
- [ ] Payments/payment links.
- [ ] Tasks and follow-up.

### AI and channels

- [ ] Receptionist agent.
- [ ] Booking agent.
- [ ] Web chat.
- [ ] WhatsApp.
- [ ] Knowledge retrieval.
- [ ] Telugu/English/Hindi evaluation.
- [ ] Phone pilot.
- [ ] Human handoff.

### Safety

- [ ] Green/Yellow/Red policies.
- [ ] Approval inbox.
- [ ] Idempotent actions.
- [ ] Result verification.
- [ ] Kill switch.
- [ ] Prompt-injection tests.

### Operations

- [ ] Metrics and alerts.
- [ ] Provider fallback.
- [ ] Usage/cost ledger.
- [ ] Incident runbooks.
- [ ] Staff training.
- [ ] Rollback tested.

---

## 24. Final architecture decision

MBAs will be built as a **Hostinger-first, provider-independent, multi-tenant Business AI Operating System**.

The product core is:

```text
MANI Business OS
  + AI Employee OS
  + Agent Runtime
  + Knowledge OS
  + Memory OS
  + Tool OS
  + Workflow OS
  + Communication OS
  + Voice Engine
  + Evaluation and Cost OS
  + Deterministic Safety Control Plane
```

The first release will prove one complete outcome for one business vertical: a multilingual AI receptionist/booking employee for car travel that converts customer enquiries into verified quotes and governed bookings across web, WhatsApp and phone.

Only after this vertical slice is reliable should MBAs expand into additional industries, dedicated realtime nodes, local GPU inference, enterprise deployments and advanced MANI autonomy.

---

## 25. Immediate next actions

1. Add this blueprint to the `rowdy9941/MBAs` repository as the single architectural source of truth.
2. Reconcile the existing scaffold with the target repository structure.
3. Create GitHub milestones matching the 90-day phases.
4. Implement authentication, tenant context and PostgreSQL RLS before more domain features.
5. Build the car-travel lead-to-booking vertical slice.
6. Add the guarded action gateway and approval inbox.
7. Add web chat, then WhatsApp, then voice.
8. Benchmark latency, accuracy, cost and conversion during the pilot.

This sequence converts MBAs from a scaffold into a safe, useful and commercially testable AI workforce platform.

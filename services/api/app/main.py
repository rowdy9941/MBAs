from contextlib import asynccontextmanager
from datetime import UTC, datetime
import json
import logging
import sys
import time
from typing import Literal
from uuid import UUID, uuid4

import asyncpg
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.auth import current_user, hash_password, issue_token, require_role, verify_password


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in ("correlation_id", "method", "path", "status_code", "duration_ms"):
            if hasattr(record, field):
                event[field] = getattr(record, field)
        if record.exc_info:
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(event, separators=(",", ":"))


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.mbas_log_level.upper())


configure_logging()
log = logging.getLogger("mbas.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=10)
    yield
    await app.state.pool.close()


app = FastAPI(title="MBAs API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID", "X-Correlation-ID"],
    expose_headers=["X-Correlation-ID"],
)


@asynccontextmanager
async def tenant_connection(user: dict):
    async with app.state.pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "SELECT set_config('app.tenant_id', $1, true), set_config('app.user_id', $2, true)",
                str(user["tenant_id"]), str(user["user_id"]),
            )
            yield conn


@app.middleware("http")
async def request_context(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("request.failed", extra={
            "correlation_id": correlation_id, "method": request.method, "path": request.url.path,
        })
        response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
    response.headers["X-Correlation-ID"] = correlation_id
    log.info("request.completed", extra={
        "correlation_id": correlation_id,
        "method": request.method,
        "path": request.url.path,
        "status_code": response.status_code,
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
    })
    return response


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(pattern=r"^[a-z0-9-]{2,63}$")


class ConversationCreate(BaseModel):
    business_id: UUID
    channel: Literal["phone", "whatsapp", "web", "telegram"]
    customer_id: UUID | None = None
    language: str | None = None


class ActionRequestCreate(BaseModel):
    business_id: UUID
    conversation_id: UUID | None = None
    action_name: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,100}$")
    payload: dict
    requested_by: str = "agent:mani"
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class ToolDefinitionCreate(BaseModel):
    name: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,100}$")
    risk_level: Literal["green", "yellow", "red"]
    input_schema: dict = Field(default_factory=dict)


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    note: str | None = Field(default=None, max_length=1000)


class SignupRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=120)
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(pattern=r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class BusinessCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    timezone: str = "Asia/Kolkata"


class CustomerCreate(BaseModel):
    business_id: UUID
    display_name: str | None = Field(default=None, max_length=120)
    phone_e164: str | None = Field(default=None, pattern=r"^\\+[1-9][0-9]{7,14}$")
    email: str | None = None


class LeadCreate(BaseModel):
    business_id: UUID
    customer_id: UUID | None = None
    source: str = Field(default="manual", max_length=40)
    notes: str | None = Field(default=None, max_length=2000)


class ServiceCreate(BaseModel):
    business_id: UUID
    name: str = Field(min_length=2, max_length=120)
    unit_price_paise: int = Field(ge=0)


class VehicleCreate(BaseModel):
    business_id: UUID
    registration_number: str = Field(min_length=4, max_length=32)
    vehicle_type: str = Field(min_length=2, max_length=80)
    seats: int = Field(gt=0, le=100)


class QuoteLineCreate(BaseModel):
    service_id: UUID
    quantity: int = Field(gt=0, le=1000)


class QuoteCreate(BaseModel):
    business_id: UUID
    customer_id: UUID | None = None
    lead_id: UUID | None = None
    lines: list[QuoteLineCreate] = Field(min_length=1, max_length=50)


class BookingCreate(BaseModel):
    business_id: UUID
    quote_id: UUID
    customer_id: UUID | None = None
    vehicle_id: UUID | None = None
    pickup_at: datetime
    pickup_location: str = Field(min_length=2, max_length=500)
    drop_location: str = Field(min_length=2, max_length=500)


RISK_LEVELS = {
    "lead.create": "green",
    "customer.create": "green",
    "booking.draft": "green",
    "message.send_confirmation": "green",
    "booking.modify": "yellow",
    "booking.cancel": "yellow",
    "payment.refund": "red",
    "customer.delete": "red",
}


def tenant_id(value: str | None) -> UUID:
    if not value:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")
    try:
        return UUID(value)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="X-Tenant-ID must be a UUID") from error


@app.get("/healthz", tags=["system"])
async def healthz():
    return {"status": "ok", "service": "mbas-api", "environment": settings.mbas_env}


@app.get("/readyz", tags=["system"])
async def readyz():
    async with app.state.pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok", "service": "mbas-api", "environment": settings.mbas_env}


@app.post("/v1/tenants", status_code=status.HTTP_201_CREATED, tags=["tenants"])
async def create_tenant(body: TenantCreate):
    async with app.state.pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                "INSERT INTO tenants(name, slug) VALUES($1, $2) RETURNING id, name, slug, created_at",
                body.name,
                body.slug,
            )
        except asyncpg.UniqueViolationError as error:
            raise HTTPException(status_code=409, detail="Tenant slug already exists") from error
    return dict(row)


@app.post("/v1/auth/signup", status_code=status.HTTP_201_CREATED, tags=["auth"])
async def signup(body: SignupRequest):
    async with app.state.pool.acquire() as conn:
        async with conn.transaction():
            try:
                tenant = await conn.fetchrow("INSERT INTO tenants(name, slug) VALUES($1, $2) RETURNING id", body.organization_name, body.organization_name.lower().replace(" ", "-")[:63])
                await conn.execute("SELECT set_config('app.tenant_id', $1, true)", str(tenant["id"]))
                org = await conn.fetchrow("INSERT INTO organizations(tenant_id, name) VALUES($1, $2) RETURNING id", tenant["id"], body.organization_name)
                user = await conn.fetchrow("INSERT INTO users(email, display_name, password_hash) VALUES($1, $2, $3) RETURNING id", body.email.lower(), body.name, hash_password(body.password))
                await conn.execute("INSERT INTO memberships(organization_id, user_id, role) VALUES($1, $2, 'owner')", org["id"], user["id"])
                await conn.execute("INSERT INTO audit_events(tenant_id, actor_type, actor_id, event_type, entity_type, entity_id) VALUES($1,'human',$2,'user.signup','user',$2)", tenant["id"], str(user["id"]))
            except asyncpg.UniqueViolationError as error:
                raise HTTPException(status_code=409, detail="Organization slug or email already exists") from error
    return {"access_token": issue_token(user["id"], tenant["id"], "owner"), "token_type": "bearer", "tenant_id": tenant["id"], "user_id": user["id"]}


@app.post("/v1/auth/login", tags=["auth"])
async def login(body: LoginRequest):
    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM authenticate_user($1)", body.email.lower())
    if not row or not row["password_hash"] or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": issue_token(row["user_id"], row["tenant_id"], row["role"]), "token_type": "bearer", "tenant_id": row["tenant_id"], "user_id": row["user_id"]}


@app.post("/v1/conversations", status_code=status.HTTP_201_CREATED, tags=["conversations"])
async def create_conversation(
    body: ConversationCreate,
    user: dict = Depends(current_user),
):
    current_tenant = user["tenant_id"]
    async with tenant_connection(user) as conn:
        row = await conn.fetchrow(
            """INSERT INTO conversations(tenant_id, business_id, customer_id, channel, language)
               VALUES($1, $2, $3, $4, $5)
               RETURNING id, business_id, channel, status, language, started_at""",
            current_tenant, body.business_id, body.customer_id, body.channel, body.language,
        )
    return dict(row)


@app.post("/v1/actions", status_code=status.HTTP_201_CREATED, tags=["actions"])
async def request_action(
    body: ActionRequestCreate,
    user: dict = Depends(require_role("owner", "admin", "manager", "staff")),
):
    current_tenant = user["tenant_id"]
    async with tenant_connection(user) as conn:
        if body.idempotency_key:
            existing = await conn.fetchrow("""SELECT id,action_name,risk_level,status,created_at FROM action_requests
                WHERE tenant_id=$1 AND idempotency_key=$2""", current_tenant, body.idempotency_key)
            if existing:
                return {**dict(existing), "requires_human_approval": existing["risk_level"] != "green", "idempotent_replay": True}
        tool = await conn.fetchrow("SELECT risk_level FROM tool_definitions WHERE name=$1 AND enabled ORDER BY version DESC LIMIT 1", body.action_name)
        risk_level = tool["risk_level"] if tool else RISK_LEVELS.get(body.action_name, "yellow")
        action_status = "approved" if risk_level == "green" else "pending"
        row = await conn.fetchrow(
            """INSERT INTO action_requests
            (tenant_id, business_id, conversation_id, action_name, risk_level, status, payload, requested_by, idempotency_key)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)
            RETURNING id, action_name, risk_level, status, created_at""",
            current_tenant, body.business_id, body.conversation_id, body.action_name,
            risk_level, action_status, body.payload, f"user:{user['user_id']}", body.idempotency_key,
        )
        await conn.execute(
            """INSERT INTO audit_events(tenant_id, actor_type, actor_id, event_type, entity_type, entity_id, payload)
            VALUES($1, 'agent', $2, 'action.requested', 'action_request', $3, $4)""",
            current_tenant,
            body.requested_by,
            str(row["id"]),
            json.dumps({"action": body.action_name, "risk": risk_level}),
        )
    return {**dict(row), "requires_human_approval": risk_level != "green"}


@app.post("/v1/tools", status_code=status.HTTP_201_CREATED, tags=["tools"])
async def create_tool(body: ToolDefinitionCreate, user: dict = Depends(require_role("owner", "admin"))):
    async with tenant_connection(user) as conn:
        row = await conn.fetchrow("""INSERT INTO tool_definitions(tenant_id,name,risk_level,input_schema)
            VALUES($1,$2,$3,$4) RETURNING id,name,version,risk_level,enabled,created_at""",
            user["tenant_id"], body.name, body.risk_level, json.dumps(body.input_schema))
    return dict(row)


@app.get("/v1/actions/pending", tags=["actions"])
async def pending_actions(user: dict = Depends(require_role("owner", "admin", "manager"))):
    async with tenant_connection(user) as conn:
        rows = await conn.fetch("""SELECT id,action_name,risk_level,status,payload,requested_by,created_at
            FROM action_requests WHERE status='pending' ORDER BY created_at""")
    return [dict(row) for row in rows]


@app.post("/v1/actions/{action_id}/approval", tags=["actions"])
async def decide_action(action_id: UUID, body: ApprovalDecision, user: dict = Depends(require_role("owner", "admin", "manager"))):
    async with tenant_connection(user) as conn:
        action = await conn.fetchrow("SELECT id,risk_level,status FROM action_requests WHERE id=$1", action_id)
        if not action or action["status"] != "pending":
            raise HTTPException(status_code=409, detail="Action is not awaiting approval")
        if action["risk_level"] == "red" and user["role"] not in ("owner", "admin"):
            raise HTTPException(status_code=403, detail="Red actions require owner or admin approval")
        await conn.execute("""INSERT INTO action_approvals(action_request_id,tenant_id,approver_id,decision,note)
            VALUES($1,$2,$3,$4,$5)""", action_id, user["tenant_id"], user["user_id"], body.decision, body.note)
        row = await conn.fetchrow("""UPDATE action_requests SET status=$2,approved_by=$3 WHERE id=$1
            RETURNING id,action_name,risk_level,status,approved_by""", action_id,
            "approved" if body.decision == "approved" else "rejected", str(user["user_id"]))
        await conn.execute("""INSERT INTO audit_events(tenant_id,actor_type,actor_id,event_type,entity_type,entity_id,payload)
            VALUES($1,'human',$2,$3,'action_request',$4,$5)""", user["tenant_id"], str(user["user_id"]),
            f"action.{body.decision}", str(action_id), json.dumps({"risk_level": action["risk_level"]}))
    return dict(row)


@app.post("/v1/businesses", status_code=status.HTTP_201_CREATED, tags=["businesses"])
async def create_business(body: BusinessCreate, user: dict = Depends(require_role("owner", "admin"))):
    async with tenant_connection(user) as conn:
        row = await conn.fetchrow("""INSERT INTO businesses(tenant_id,name,timezone) VALUES($1,$2,$3)
            RETURNING id,name,timezone,created_at""", user["tenant_id"], body.name, body.timezone)
    return dict(row)


@app.post("/v1/customers", status_code=status.HTTP_201_CREATED, tags=["customers"])
async def create_customer(body: CustomerCreate, user: dict = Depends(require_role("owner", "admin", "manager", "staff"))):
    async with tenant_connection(user) as conn:
        row = await conn.fetchrow("""INSERT INTO customers(tenant_id,business_id,display_name,phone_e164,email)
            VALUES($1,$2,$3,$4,$5) RETURNING id,business_id,display_name,phone_e164,email,created_at""",
            user["tenant_id"], body.business_id, body.display_name, body.phone_e164, body.email)
    return dict(row)


@app.post("/v1/leads", status_code=status.HTTP_201_CREATED, tags=["leads"])
async def create_lead(body: LeadCreate, user: dict = Depends(require_role("owner", "admin", "manager", "staff"))):
    async with tenant_connection(user) as conn:
        row = await conn.fetchrow("""INSERT INTO leads(tenant_id,business_id,customer_id,source,notes)
            VALUES($1,$2,$3,$4,$5) RETURNING id,business_id,customer_id,status,source,created_at""",
            user["tenant_id"], body.business_id, body.customer_id, body.source, body.notes)
    return dict(row)


@app.post("/v1/services", status_code=status.HTTP_201_CREATED, tags=["services"])
async def create_service(body: ServiceCreate, user: dict = Depends(require_role("owner", "admin", "manager"))):
    async with tenant_connection(user) as conn:
        row = await conn.fetchrow("""INSERT INTO services(tenant_id,business_id,name,unit_price_paise)
            VALUES($1,$2,$3,$4) RETURNING id,name,unit_price_paise,created_at""",
            user["tenant_id"], body.business_id, body.name, body.unit_price_paise)
    return dict(row)


@app.post("/v1/vehicles", status_code=status.HTTP_201_CREATED, tags=["vehicles"])
async def create_vehicle(body: VehicleCreate, user: dict = Depends(require_role("owner", "admin", "manager"))):
    async with tenant_connection(user) as conn:
        row = await conn.fetchrow("""INSERT INTO vehicles(tenant_id,business_id,registration_number,vehicle_type,seats)
            VALUES($1,$2,$3,$4,$5) RETURNING id,registration_number,vehicle_type,seats,status,created_at""",
            user["tenant_id"], body.business_id, body.registration_number.upper(), body.vehicle_type, body.seats)
    return dict(row)


@app.post("/v1/quotes", status_code=status.HTTP_201_CREATED, tags=["quotes"])
async def create_quote(body: QuoteCreate, user: dict = Depends(require_role("owner", "admin", "manager", "staff"))):
    async with tenant_connection(user) as conn:
        services = []
        for line in body.lines:
            service = await conn.fetchrow("SELECT id,name,unit_price_paise FROM services WHERE id=$1 AND business_id=$2 AND active", line.service_id, body.business_id)
            if not service:
                raise HTTPException(status_code=422, detail="Quote includes an unavailable service")
            services.append((service, line.quantity))
        total = sum(service["unit_price_paise"] * quantity for service, quantity in services)
        quote = await conn.fetchrow("""INSERT INTO quotes(tenant_id,business_id,customer_id,lead_id,total_paise)
            VALUES($1,$2,$3,$4,$5) RETURNING id,status,total_paise,currency,created_at""",
            user["tenant_id"], body.business_id, body.customer_id, body.lead_id, total)
        for service, quantity in services:
            await conn.execute("""INSERT INTO quote_lines(quote_id,service_id,description,quantity,unit_price_paise,line_total_paise)
                VALUES($1,$2,$3,$4,$5,$6)""", quote["id"], service["id"], service["name"], quantity, service["unit_price_paise"], service["unit_price_paise"] * quantity)
    return dict(quote)


@app.post("/v1/bookings", status_code=status.HTTP_201_CREATED, tags=["bookings"])
async def create_booking(body: BookingCreate, user: dict = Depends(require_role("owner", "admin", "manager", "staff"))):
    async with tenant_connection(user) as conn:
        quote = await conn.fetchrow("SELECT id,total_paise FROM quotes WHERE id=$1 AND business_id=$2 AND status IN ('draft','sent','accepted')", body.quote_id, body.business_id)
        if not quote:
            raise HTTPException(status_code=422, detail="Booking requires an active quote in this business")
        row = await conn.fetchrow("""INSERT INTO bookings(tenant_id,business_id,quote_id,customer_id,vehicle_id,pickup_at,pickup_location,drop_location,total_paise)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9) RETURNING id,status,total_paise,pickup_at,created_at""",
            user["tenant_id"], body.business_id, body.quote_id, body.customer_id, body.vehicle_id, body.pickup_at, body.pickup_location, body.drop_location, quote["total_paise"])
    return dict(row)


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response("mbas_api_up 1\\n", media_type="text/plain; version=0.0.4")

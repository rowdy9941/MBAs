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


class SignupRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=120)
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(pattern=r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


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
    return {"access_token": issue_token(row["id"], row["tenant_id"], row["role"]), "token_type": "bearer", "tenant_id": row["tenant_id"], "user_id": row["id"]}


@app.post("/v1/conversations", status_code=status.HTTP_201_CREATED, tags=["conversations"])
async def create_conversation(
    body: ConversationCreate,
    user: dict = Depends(current_user),
):
    current_tenant = user["tenant_id"]
    async with app.state.pool.acquire() as conn:
        await conn.execute("SELECT set_config('app.tenant_id', $1, true), set_config('app.user_id', $2, true)", str(current_tenant), str(user["user_id"]))
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
    risk_level = RISK_LEVELS.get(body.action_name, "yellow")
    action_status = "approved" if risk_level == "green" else "pending"
    async with app.state.pool.acquire() as conn:
        await conn.execute("SELECT set_config('app.tenant_id', $1, true), set_config('app.user_id', $2, true)", str(current_tenant), str(user["user_id"]))
        async with conn.transaction():
            row = await conn.fetchrow(
                """INSERT INTO action_requests
                (tenant_id, business_id, conversation_id, action_name, risk_level, status, payload, requested_by)
                VALUES($1,$2,$3,$4,$5,$6,$7,$8)
                RETURNING id, action_name, risk_level, status, created_at""",
                current_tenant, body.business_id, body.conversation_id, body.action_name,
                risk_level, action_status, body.payload, body.requested_by,
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


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response("mbas_api_up 1\\n", media_type="text/plain; version=0.0.4")

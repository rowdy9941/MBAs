from contextlib import asynccontextmanager
import json
from typing import Literal
from uuid import UUID

import asyncpg
from fastapi import FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=10)
    yield
    await app.state.pool.close()


app = FastAPI(title="MBAs API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[item.strip() for item in settings.mbas_cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
)


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


@app.post("/v1/conversations", status_code=status.HTTP_201_CREATED, tags=["conversations"])
async def create_conversation(
    body: ConversationCreate,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    current_tenant = tenant_id(x_tenant_id)
    async with app.state.pool.acquire() as conn:
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
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
):
    current_tenant = tenant_id(x_tenant_id)
    risk_level = RISK_LEVELS.get(body.action_name, "yellow")
    action_status = "approved" if risk_level == "green" else "pending"
    async with app.state.pool.acquire() as conn:
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

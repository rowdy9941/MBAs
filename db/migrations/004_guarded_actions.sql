CREATE TABLE tool_definitions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
  risk_level TEXT NOT NULL CHECK (risk_level IN ('green','yellow','red')),
  input_schema JSONB NOT NULL DEFAULT '{}'::jsonb, enabled BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE (tenant_id, name, version)
);
ALTER TABLE action_requests ADD COLUMN idempotency_key TEXT;
ALTER TABLE action_requests ADD COLUMN execution_error TEXT;
CREATE UNIQUE INDEX action_requests_tenant_idempotency_idx ON action_requests(tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE TABLE action_approvals (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), action_request_id UUID NOT NULL UNIQUE REFERENCES action_requests(id) ON DELETE CASCADE,
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, approver_id UUID NOT NULL REFERENCES users(id),
  decision TEXT NOT NULL CHECK (decision IN ('approved','rejected')), note TEXT, decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE tool_definitions ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_approvals ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_scope ON tool_definitions USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());
CREATE POLICY tenant_scope ON action_approvals USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());

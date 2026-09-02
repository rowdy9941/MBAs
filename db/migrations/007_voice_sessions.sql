CREATE TABLE voice_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
  provider TEXT NOT NULL, language TEXT NOT NULL DEFAULT 'en-IN', status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active','handoff','completed','failed')), latency_ms INTEGER, cost_paise BIGINT NOT NULL DEFAULT 0,
  recording_consent BOOLEAN NOT NULL DEFAULT false, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), ended_at TIMESTAMPTZ
);
ALTER TABLE voice_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_scope ON voice_sessions USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());

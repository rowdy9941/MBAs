CREATE TABLE knowledge_sources (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, title TEXT NOT NULL, source_type TEXT NOT NULL,
  verification_status TEXT NOT NULL DEFAULT 'pending' CHECK (verification_status IN ('pending','verified','rejected')),
  content TEXT NOT NULL, valid_until TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX knowledge_sources_retrieval_idx ON knowledge_sources(tenant_id,business_id,verification_status,created_at DESC);
CREATE TABLE channel_endpoints (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, provider TEXT NOT NULL,
  external_id TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(provider,external_id)
);
CREATE TABLE inbound_events (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, provider TEXT NOT NULL, provider_event_id TEXT NOT NULL,
  payload JSONB NOT NULL, received_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(provider,provider_event_id)
);
ALTER TABLE knowledge_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE channel_endpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE inbound_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_scope ON knowledge_sources USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());
CREATE POLICY tenant_scope ON channel_endpoints USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());
CREATE POLICY tenant_scope ON inbound_events USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());
CREATE OR REPLACE FUNCTION resolve_channel_endpoint(channel_provider TEXT, channel_external_id TEXT)
RETURNS TABLE(tenant_id UUID,business_id UUID) LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT tenant_id,business_id FROM channel_endpoints WHERE provider=channel_provider AND external_id=channel_external_id
$$;

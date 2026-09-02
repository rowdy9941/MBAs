CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  password_hash TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'invited', 'suspended')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE memberships (
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'manager', 'staff', 'viewer')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, user_id)
);

CREATE TABLE refresh_tokens (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL UNIQUE,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
-- Identity tables are accessed through authenticated service code and membership joins.

CREATE OR REPLACE FUNCTION app_current_tenant() RETURNS UUID
LANGUAGE sql STABLE AS $$ SELECT NULLIF(current_setting('app.tenant_id', true), '')::uuid $$;

DO $$
DECLARE table_name TEXT;
BEGIN
  FOREACH table_name IN ARRAY ARRAY['organizations','businesses','customers','conversations','action_requests','audit_events'] LOOP
    EXECUTE format('DROP POLICY IF EXISTS tenant_scope ON %I', table_name);
    EXECUTE format('CREATE POLICY tenant_scope ON %I USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant())', table_name);
  END LOOP;
END $$;

CREATE POLICY user_membership_scope ON users USING (
  id = current_setting('app.user_id', true)::uuid
  OR EXISTS (SELECT 1 FROM memberships m JOIN organizations o ON o.id = m.organization_id
            WHERE m.user_id = users.id AND o.tenant_id = app_current_tenant())
);
CREATE POLICY membership_scope ON memberships USING (
  organization_id IN (SELECT id FROM organizations WHERE tenant_id = app_current_tenant())
 ) WITH CHECK (
  organization_id IN (SELECT id FROM organizations WHERE tenant_id = app_current_tenant())
);
CREATE POLICY refresh_token_scope ON refresh_tokens USING (user_id = current_setting('app.user_id', true)::uuid);

-- Authentication must work before a request has a tenant context. This function exposes
-- only the minimum login fields and cannot be used to mutate identity data.
CREATE OR REPLACE FUNCTION authenticate_user(login_email TEXT)
RETURNS TABLE(user_id UUID, password_hash TEXT, tenant_id UUID, role TEXT)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT u.id, u.password_hash, o.tenant_id, m.role
  FROM users u JOIN memberships m ON m.user_id = u.id
  JOIN organizations o ON o.id = m.organization_id
  WHERE u.email = lower(login_email) AND u.status = 'active'
  ORDER BY m.created_at LIMIT 1
$$;

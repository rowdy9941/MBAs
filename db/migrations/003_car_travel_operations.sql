CREATE TABLE branches (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  address TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','contacted','qualified','won','lost')),
  source TEXT NOT NULL DEFAULT 'manual', notes TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE vehicles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, branch_id UUID REFERENCES branches(id) ON DELETE SET NULL,
  registration_number TEXT NOT NULL, vehicle_type TEXT NOT NULL, seats INTEGER NOT NULL CHECK (seats > 0),
  status TEXT NOT NULL DEFAULT 'available' CHECK (status IN ('available','assigned','maintenance','inactive')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE (business_id, registration_number)
);
CREATE TABLE services (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, name TEXT NOT NULL,
  unit_price_paise BIGINT NOT NULL CHECK (unit_price_paise >= 0), active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE quotes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
  customer_id UUID REFERENCES customers(id) ON DELETE SET NULL, currency CHAR(3) NOT NULL DEFAULT 'INR',
  total_paise BIGINT NOT NULL CHECK (total_paise >= 0), status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','sent','accepted','expired','cancelled')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE quote_lines (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), quote_id UUID NOT NULL REFERENCES quotes(id) ON DELETE CASCADE,
  service_id UUID NOT NULL REFERENCES services(id), description TEXT NOT NULL, quantity INTEGER NOT NULL CHECK (quantity > 0),
  unit_price_paise BIGINT NOT NULL CHECK (unit_price_paise >= 0), line_total_paise BIGINT NOT NULL CHECK (line_total_paise >= 0)
);
CREATE TABLE bookings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE, quote_id UUID REFERENCES quotes(id) ON DELETE SET NULL,
  customer_id UUID REFERENCES customers(id) ON DELETE SET NULL, vehicle_id UUID REFERENCES vehicles(id) ON DELETE SET NULL,
  pickup_at TIMESTAMPTZ NOT NULL, pickup_location TEXT NOT NULL, drop_location TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'confirmed' CHECK (status IN ('draft','confirmed','completed','cancelled')),
  total_paise BIGINT NOT NULL CHECK (total_paise >= 0), created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX leads_tenant_idx ON leads(tenant_id, created_at DESC);
CREATE INDEX bookings_tenant_idx ON bookings(tenant_id, pickup_at);

ALTER TABLE branches ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehicles ENABLE ROW LEVEL SECURITY;
ALTER TABLE services ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE quote_lines ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_scope ON branches USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());
CREATE POLICY tenant_scope ON leads USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());
CREATE POLICY tenant_scope ON vehicles USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());
CREATE POLICY tenant_scope ON services USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());
CREATE POLICY tenant_scope ON quotes USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());
CREATE POLICY tenant_scope ON bookings USING (tenant_id = app_current_tenant()) WITH CHECK (tenant_id = app_current_tenant());
CREATE POLICY quote_line_scope ON quote_lines USING (quote_id IN (SELECT id FROM quotes)) WITH CHECK (quote_id IN (SELECT id FROM quotes));

-- RUMBO commercial control-plane schema candidate V1
-- Non-production candidate. Review and adapt to the selected PostgreSQL/Supabase deployment.

create extension if not exists pgcrypto;

create table if not exists organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now()
);

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text,
  display_name text,
  created_at timestamptz not null default now(),
  unique (email)
);

create table if not exists identities (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  provider text not null check (provider in ('email','google','chatgpt')),
  provider_subject text not null,
  email_at_provider text,
  created_at timestamptz not null default now(),
  unique (provider, provider_subject)
);

create table if not exists organization_members (
  organization_id uuid not null references organizations(id) on delete cascade,
  user_id uuid not null references users(id) on delete cascade,
  role_key text not null,
  created_at timestamptz not null default now(),
  primary key (organization_id, user_id)
);

create table if not exists projects (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  name text not null,
  created_at timestamptz not null default now()
);
create index if not exists projects_org_idx on projects(organization_id);

create table if not exists pricing_versions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid references organizations(id) on delete cascade,
  code text not null,
  currency text not null default 'USD',
  active_from timestamptz not null,
  active_to timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists policy_decisions (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  project_id uuid not null references projects(id) on delete cascade,
  decision text not null check (decision in ('allow','deny','require_approval')),
  policy_version text not null,
  reason text,
  decided_at timestamptz not null default now()
);
create index if not exists policy_decisions_org_project_idx on policy_decisions(organization_id, project_id, decided_at);

create table if not exists execution_receipts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  project_id uuid not null references projects(id) on delete cascade,
  request_id text not null,
  trace_id text not null,
  result_hash text,
  effect_status text not null check (effect_status in ('not_checked','verified','failed','indeterminate')),
  receipt_hash text not null,
  created_at timestamptz not null default now(),
  unique (organization_id, request_id),
  unique (receipt_hash)
);
create index if not exists execution_receipts_org_project_idx on execution_receipts(organization_id, project_id, created_at);

create table if not exists usage_events (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  project_id uuid not null references projects(id) on delete cascade,
  idempotency_key text not null,
  request_id text not null,
  trace_id text not null,
  meter text not null,
  billable_units numeric(20,6) not null check (billable_units >= 0),
  price_version_id uuid references pricing_versions(id),
  unit_price numeric(20,8) not null check (unit_price >= 0),
  amount numeric(20,8) not null check (amount >= 0),
  currency text not null default 'USD',
  execution_receipt_id uuid references execution_receipts(id),
  occurred_at timestamptz not null default now(),
  unique (organization_id, idempotency_key)
);
create index if not exists usage_events_org_time_idx on usage_events(organization_id, occurred_at);

create table if not exists mcp_calls (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  project_id uuid not null references projects(id) on delete cascade,
  request_id text not null,
  trace_id text not null,
  server_name text not null,
  tool_name text not null,
  arguments_hash text not null,
  status text not null check (status in ('accepted','denied','error','protocol_success','effect_verified','effect_failed')),
  latency_ms bigint check (latency_ms >= 0),
  policy_decision_id uuid references policy_decisions(id),
  execution_receipt_id uuid references execution_receipts(id),
  started_at timestamptz not null,
  completed_at timestamptz,
  unique (organization_id, request_id)
);
create index if not exists mcp_calls_org_project_time_idx on mcp_calls(organization_id, project_id, started_at);

create table if not exists billing_accounts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null unique references organizations(id) on delete cascade,
  provider text not null,
  provider_customer_ref text,
  status text not null default 'active',
  created_at timestamptz not null default now()
);

create table if not exists support_tickets (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  opened_by uuid references users(id),
  category text not null,
  severity text not null default 'normal',
  status text not null default 'open',
  subject text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists support_tickets_org_status_idx on support_tickets(organization_id, status, created_at);

create table if not exists partner_records (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  partner_type text not null,
  internal_status text not null check (internal_status in ('APPLIED','UNDER_REVIEW','APPROVED','ACTIVE','SUSPENDED','REMOVED')),
  openai_partner_network_verified boolean not null default false,
  openai_marketplace_verified boolean not null default false,
  verification_evidence_ref text,
  verified_at timestamptz,
  created_at timestamptz not null default now()
);

-- RLS must be enabled only together with tested tenant policies in the selected runtime.
-- Do not ship an allow-all policy. Production admission requires explicit org-scoped policies
-- plus service-role boundaries, migration tests and security-advisor/readback evidence.

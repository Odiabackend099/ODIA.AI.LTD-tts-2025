create table if not exists api_keys (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  api_key text unique not null,
  label text,
  is_active boolean default true,
  created_at timestamptz default now()
);

create index if not exists idx_api_keys_key on api_keys(api_key);

create table if not exists usage_logs (
  id bigserial primary key,
  api_key text not null,
  chars_used int not null,
  duration_ms int not null,
  cache_hit boolean default false,
  created_at timestamptz default now()
);
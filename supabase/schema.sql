-- Job Radar — Supabase schema
-- Run this once in your Supabase project: SQL Editor -> New query -> paste -> Run

create extension if not exists "pgcrypto";

-- Companies table
create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  website text,
  careers_url text,
  category text default 'tech',
  tier text default 'good',                -- dream | high_priority | good | startup | backup | unclassified
  ats text default 'pending',              -- greenhouse | lever | ashby | workday | smartrecruiters | icims | successfactors | taleo | custom | unknown | pending
  ats_identifier text,                      -- e.g. board token, org slug, site id
  source_url text,
  status text default 'pending',            -- verified | needs_review | working | failed | unsupported | pending
  active boolean default true,
  last_checked_at timestamptz,
  last_success_at timestamptz,
  last_detect_attempt_at timestamptz,
  last_error text,
  jobs_found_count int default 0,
  notes text,
  created_at timestamptz default now()
);

-- Idempotent column additions for companies (if table already existed)
alter table companies add column if not exists website text;
alter table companies add column if not exists category text default 'tech';
alter table companies add column if not exists source_url text;
alter table companies add column if not exists status text default 'pending';
alter table companies add column if not exists last_success_at timestamptz;
alter table companies add column if not exists last_error text;

-- Jobs table
create table if not exists jobs (
  id uuid primary key default gen_random_uuid(),
  company_id uuid references companies(id) on delete set null,
  company_name text not null,
  external_job_id text,
  title text not null,
  description text,
  location text,
  location_priority int default 1,        -- 1: Bangalore/Remote India, 2: Major Indian Cities, 3: Other India, 0: Outside India
  employment_type text,
  experience_requirement text,
  application_url text not null,
  source text not null,                   -- greenhouse | lever | ashby | workday | smartrecruiters | custom | etc.
  source_url text,
  posted_at timestamptz,
  updated_at timestamptz,
  track text,                             -- ai_ml_ds | software | data_analyst | other
  fit_score int,                          -- 0-100 overall score
  role_relevance int,                     -- 0-100
  skill_match int,                        -- 0-100
  experience_fit int,                     -- 0-100
  location_fit int,                       -- 0-100
  career_value int,                       -- 0-100
  apply_recommendation boolean default true,
  fit_reason text,
  difficulty_tier text,                   -- reach | competitive | achievable
  status text default 'new',              -- new | applied | interviewing | rejected | offer | ignored
  applied_at timestamptz,
  followup_notes text,
  dedupe_key text unique,
  first_seen_at timestamptz default now(),
  last_seen_at timestamptz default now(),
  active boolean default true
);

-- Idempotent column additions for jobs (if table already existed)
alter table jobs add column if not exists location_priority int default 1;
alter table jobs add column if not exists employment_type text;
alter table jobs add column if not exists experience_requirement text;
alter table jobs add column if not exists source_url text;
alter table jobs add column if not exists updated_at timestamptz;
alter table jobs add column if not exists role_relevance int;
alter table jobs add column if not exists skill_match int;
alter table jobs add column if not exists experience_fit int;
alter table jobs add column if not exists location_fit int;
alter table jobs add column if not exists career_value int;
alter table jobs add column if not exists apply_recommendation boolean default true;
alter table jobs add column if not exists active boolean default true;

-- Collection Logs table
create table if not exists collection_logs (
  id uuid primary key default gen_random_uuid(),
  company_id uuid references companies(id) on delete cascade,
  company_name text,
  started_at timestamptz default now(),
  completed_at timestamptz,
  jobs_found int default 0,
  jobs_new int default 0,
  jobs_updated int default 0,
  jobs_skipped int default 0,
  error text,
  status text default 'success'           -- success | partial | failed | unsupported | manual_review
);

-- Indexes
create index if not exists idx_jobs_status on jobs(status);
create index if not exists idx_jobs_fit_score on jobs(fit_score desc);
create index if not exists idx_jobs_first_seen on jobs(first_seen_at desc);
create index if not exists idx_jobs_company_id on jobs(company_id);
create index if not exists idx_companies_active on companies(active);
create index if not exists idx_logs_company_id on collection_logs(company_id);

-- RLS policies
alter table companies enable row level security;
alter table jobs enable row level security;
alter table collection_logs enable row level security;

create policy "allow all - companies" on companies for all using (true) with check (true);
create policy "allow all - jobs" on jobs for all using (true) with check (true);
create policy "allow all - collection_logs" on collection_logs for all using (true) with check (true);

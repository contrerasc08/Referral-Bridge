-- Referral Bridge, Phase 1: companies, roles, and row-level security.
--
-- What this sets up:
--   * companies, memberships (role per company), platform_admins (the master account),
--     invites, record shares for guests, and an audit log
--   * one table per app collection, each row tagged with company_id
--   * row-level security on every table: a user only sees and changes records of
--     companies they belong to, as their role allows
--   * MFA: the platform owner and company admins must sign in with a second factor
--     (aal2) to reach any data; anyone else who has set up MFA must use it too
--
-- Nothing here creates a user or a password. The owner account is promoted afterwards
-- with supabase/bootstrap_owner.sql, run by hand in the Supabase SQL editor.
--
-- App collections keep their flexible shape in a jsonb "data" column, so the current app
-- moves over without rewriting every screen. Columns used for joins and security
-- (company_id, biz_id, coi_id, owner_id) are real columns.

create schema if not exists app;
revoke all on schema app from public;
grant usage on schema app to authenticated;

-- ---------- core tables ----------

create table public.companies (
  id          uuid primary key default gen_random_uuid(),
  name        text not null check (length(trim(name)) > 0),
  plan        text not null default 'internal',
  created_at  timestamptz not null default now(),
  created_by  uuid references auth.users(id) on delete set null
);

-- The master account(s). No policies allow writes, so rows can only be added from the
-- Supabase dashboard or SQL editor, never from the app.
create table public.platform_admins (
  user_id     uuid primary key references auth.users(id) on delete cascade,
  added_at    timestamptz not null default now()
);

create table public.memberships (
  company_id  uuid not null references public.companies(id) on delete cascade,
  user_id     uuid not null references auth.users(id) on delete cascade,
  role        text not null check (role in ('company_admin','employee','guest','bot')),
  -- employees see every company record ('all') or only records assigned to them
  scope       text not null default 'all' check (scope in ('all','assigned')),
  created_at  timestamptz not null default now(),
  created_by  uuid references auth.users(id) on delete set null,
  primary key (company_id, user_id)
);
create index memberships_user_idx on public.memberships(user_id);

create table public.invites (
  id          uuid primary key default gen_random_uuid(),
  company_id  uuid not null references public.companies(id) on delete cascade,
  email       text not null,
  role        text not null check (role in ('company_admin','employee','guest')),
  token_hash  text not null unique,           -- sha256 of the one-time code; the code itself is never stored
  expires_at  timestamptz not null default now() + interval '7 days',
  accepted_at timestamptz,
  accepted_by uuid references auth.users(id) on delete set null,
  invited_by  uuid references auth.users(id) on delete set null,
  created_at  timestamptz not null default now()
);

-- Records shared with a guest (a partner or specialist).
create table public.shares (
  company_id  uuid not null references public.companies(id) on delete cascade,
  table_name  text not null,
  record_id   text not null,
  user_id     uuid not null references auth.users(id) on delete cascade,
  can_edit    boolean not null default false,
  created_at  timestamptz not null default now(),
  primary key (table_name, record_id, user_id)
);

create table public.audit_log (
  id          bigint generated always as identity primary key,
  company_id  uuid,
  user_id     uuid,
  table_name  text not null,
  record_id   text,
  action      text not null,
  at          timestamptz not null default now(),
  changed     jsonb
);
create index audit_log_company_idx on public.audit_log(company_id, at desc);

-- ---------- helper functions (run with definer rights so policies can read memberships) ----------

create or replace function app.uid() returns uuid language sql stable as $$ select auth.uid() $$;

-- true when this session signed in with a second factor
create or replace function app.aal2() returns boolean language sql stable as $$
  select coalesce(auth.jwt()->>'aal','') = 'aal2'
$$;

-- users who have enrolled MFA must use it; users who haven't can still sign in
create or replace function app.mfa_ok() returns boolean
language sql stable security definer set search_path = '' as $$
  select app.aal2() or not exists (
    select 1 from auth.mfa_factors f where f.user_id = auth.uid() and f.status = 'verified')
$$;

create or replace function app.is_platform_admin() returns boolean
language sql stable security definer set search_path = '' as $$
  select app.aal2() and exists (select 1 from public.platform_admins p where p.user_id = auth.uid())
$$;

create or replace function app.role_in(c uuid) returns text
language sql stable security definer set search_path = '' as $$
  select m.role from public.memberships m where m.company_id = c and m.user_id = auth.uid()
$$;

create or replace function app.is_company_admin(c uuid) returns boolean
language sql stable as $$
  select app.is_platform_admin() or (app.aal2() and app.role_in(c) = 'company_admin')
$$;

-- can this user see a record of company c owned by owner?
create or replace function app.can_read(c uuid, owner uuid, tbl text, rid text) returns boolean
language sql stable security definer set search_path = '' as $$
  select app.is_platform_admin() or exists (
    select 1 from public.memberships m
    where m.company_id = c and m.user_id = auth.uid() and (
      (m.role = 'company_admin' and app.aal2())
      or m.role = 'bot'
      or (m.role = 'employee' and (m.scope = 'all' or owner = auth.uid()))
      or (m.role = 'guest' and exists (
            select 1 from public.shares s
            where s.table_name = tbl and s.record_id = rid and s.user_id = auth.uid() and s.company_id = c))
    ))
$$;

-- can this user add or change a record? Bots may only write the tables they work on.
create or replace function app.can_write(c uuid, owner uuid, tbl text, rid text) returns boolean
language sql stable security definer set search_path = '' as $$
  select app.is_platform_admin() or exists (
    select 1 from public.memberships m
    where m.company_id = c and m.user_id = auth.uid() and (
      (m.role = 'company_admin' and app.aal2())
      or (m.role = 'employee' and (m.scope = 'all' or owner = auth.uid()))
      or (m.role = 'bot' and tbl in ('businesses','cois','signals','news','drafts','botlog',
                                      'contact_requests','lead_requests','provider_usage'))
      or (m.role = 'guest' and exists (
            select 1 from public.shares s
            where s.table_name = tbl and s.record_id = rid and s.user_id = auth.uid()
              and s.company_id = c and s.can_edit))
    ))
$$;

-- deleting is for company admins and employees only; bots and guests never delete
create or replace function app.can_delete(c uuid, owner uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select app.is_platform_admin() or exists (
    select 1 from public.memberships m
    where m.company_id = c and m.user_id = auth.uid() and (
      (m.role = 'company_admin' and app.aal2())
      or (m.role = 'employee' and (m.scope = 'all' or owner = auth.uid()))))
$$;

-- ---------- app collection tables ----------
-- One table per collection in src/index.html (COL). Ids stay text so existing ids carry over.

create or replace function app.touch() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if tg_op = 'UPDATE' and new.company_id is distinct from old.company_id then
    raise exception 'A record cannot move to another company';
  end if;
  new.updated_at := now();
  new.updated_by := auth.uid();
  if tg_op = 'INSERT' then new.created_at := coalesce(new.created_at, now()); end if;
  return new;
end $$;

create or replace function app.audit() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  if tg_op = 'DELETE' then
    insert into public.audit_log(company_id, user_id, table_name, record_id, action)
    values (old.company_id, auth.uid(), tg_table_name, old.id, 'delete');
  else
    insert into public.audit_log(company_id, user_id, table_name, record_id, action, changed)
    values (new.company_id, auth.uid(), tg_table_name, new.id, lower(tg_op), new.data);
  end if;
  return null;
end $$;

do $$
declare
  t text;
  tables text[] := array['businesses','cois','matches','signals','news','outreach','drafts','botlog',
                         'settings','contact_requests','lead_requests','provider_usage','tasks'];
begin
  foreach t in array tables loop
    execute format($f$
      create table public.%1$I (
        id          text not null,
        company_id  uuid not null references public.companies(id) on delete cascade,
        owner_id    uuid references auth.users(id) on delete set null,
        biz_id      text,
        coi_id      text,
        data        jsonb not null default '{}'::jsonb,
        created_at  timestamptz not null default now(),
        updated_at  timestamptz not null default now(),
        updated_by  uuid,
        primary key (company_id, id)
      )$f$, t);
    execute format('create index %1$I on public.%2$I(company_id, updated_at desc)', t||'_recent_idx', t);
    execute format('create index %1$I on public.%2$I(company_id, biz_id) where biz_id is not null', t||'_biz_idx', t);
    execute format('create trigger touch before insert or update on public.%I for each row execute function app.touch()', t);
    execute format('create trigger audit after insert or update or delete on public.%I for each row execute function app.audit()', t);
    execute format('alter table public.%I enable row level security', t);
    execute format('alter table public.%I force row level security', t);

    execute format($p$create policy "members read" on public.%1$I for select to authenticated
      using (app.can_read(company_id, owner_id, %1$L, id))$p$, t);
    execute format($p$create policy "members add" on public.%1$I for insert to authenticated
      with check (app.can_write(company_id, owner_id, %1$L, id))$p$, t);
    execute format($p$create policy "members change" on public.%1$I for update to authenticated
      using (app.can_write(company_id, owner_id, %1$L, id))
      with check (app.can_write(company_id, owner_id, %1$L, id))$p$, t);
    execute format($p$create policy "members delete" on public.%1$I for delete to authenticated
      using (app.can_delete(company_id, owner_id))$p$, t);
    -- second factor required for anyone who has set one up
    execute format($p$create policy "mfa when enrolled" on public.%1$I as restrictive to authenticated
      using (app.mfa_ok()) with check (app.mfa_ok())$p$, t);

    execute format('revoke all on public.%I from anon, public', t);
    execute format('grant select, insert, update, delete on public.%I to authenticated', t);
  end loop;

  -- live updates for the app (replaces today's onSnapshot); only on Supabase
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime') then
    foreach t in array tables loop
      execute format('alter publication supabase_realtime add table public.%I', t);
    end loop;
  end if;
end $$;

-- ---------- policies on the core tables ----------

alter table public.companies       enable row level security;
alter table public.platform_admins enable row level security;
alter table public.memberships     enable row level security;
alter table public.invites         enable row level security;
alter table public.shares          enable row level security;
alter table public.audit_log       enable row level security;

-- companies: members see theirs; only the platform owner creates, renames or removes them
create policy "members see their company" on public.companies for select to authenticated
  using (app.is_platform_admin() or app.role_in(id) is not null);
create policy "owner manages companies" on public.companies for all to authenticated
  using (app.is_platform_admin()) with check (app.is_platform_admin());

-- platform_admins: you can check your own row; no one can write it from the app
create policy "see own admin row" on public.platform_admins for select to authenticated
  using (user_id = auth.uid());

-- memberships: see your own and, as an admin, your company's. Admins manage people,
-- but can't change their own row (no lockouts) and only the owner can add bots.
create policy "see memberships" on public.memberships for select to authenticated
  using (user_id = auth.uid() or app.is_company_admin(company_id));
create policy "admins add people" on public.memberships for insert to authenticated
  with check (app.is_company_admin(company_id) and user_id <> auth.uid()
              and (role <> 'bot' or app.is_platform_admin()));
create policy "admins change people" on public.memberships for update to authenticated
  using (app.is_company_admin(company_id) and user_id <> auth.uid())
  with check (app.is_company_admin(company_id) and user_id <> auth.uid()
              and (role <> 'bot' or app.is_platform_admin()));
create policy "admins remove people" on public.memberships for delete to authenticated
  using (app.is_company_admin(company_id) and user_id <> auth.uid());

create policy "admins manage invites" on public.invites for all to authenticated
  using (app.is_company_admin(company_id)) with check (app.is_company_admin(company_id));

create policy "see shares" on public.shares for select to authenticated
  using (user_id = auth.uid() or app.is_company_admin(company_id));
create policy "admins manage shares" on public.shares for all to authenticated
  using (app.is_company_admin(company_id)) with check (app.is_company_admin(company_id));

-- audit log: admins read it; rows are written only by the audit trigger
create policy "admins read audit" on public.audit_log for select to authenticated
  using (app.is_company_admin(company_id));

revoke all on public.companies, public.platform_admins, public.memberships, public.invites,
              public.shares, public.audit_log from anon, public;
grant select, insert, update, delete on public.companies, public.memberships, public.invites, public.shares to authenticated;
grant select on public.platform_admins, public.audit_log to authenticated;

-- ---------- accepting an invite ----------
-- The signed-in user passes the one-time code from their invite email. It must match their
-- email address and not be expired or used.
create or replace function public.accept_invite(code text) returns uuid
language plpgsql security definer set search_path = '' as $$
declare inv public.invites;
begin
  if auth.uid() is null then raise exception 'Sign in first'; end if;
  select * into inv from public.invites
   where token_hash = encode(extensions.digest(code, 'sha256'), 'hex')
     and accepted_at is null and expires_at > now()
   for update;
  if not found then raise exception 'This invite is invalid or expired'; end if;
  if lower(inv.email) <> lower(coalesce(auth.jwt()->>'email','')) then
    raise exception 'This invite was sent to a different email address';
  end if;
  insert into public.memberships(company_id, user_id, role, created_by)
  values (inv.company_id, auth.uid(), inv.role, inv.invited_by)
  on conflict (company_id, user_id) do nothing;
  update public.invites set accepted_at = now(), accepted_by = auth.uid() where id = inv.id;
  return inv.company_id;
end $$;
revoke all on function public.accept_invite(text) from public, anon;
grant execute on function public.accept_invite(text) to authenticated;

-- What the signed-in user may do, for the app to show or hide screens.
-- The database still checks every read and write; this is only for display.
create or replace function public.my_access() returns jsonb
language sql stable security definer set search_path = '' as $$
  select jsonb_build_object(
    'user_id', auth.uid(),
    'mfa', app.aal2(),
    'platform_owner', app.is_platform_admin(),
    'companies', coalesce((select jsonb_agg(jsonb_build_object(
        'company_id', m.company_id, 'name', c.name, 'role', m.role, 'scope', m.scope))
      from public.memberships m join public.companies c on c.id = m.company_id
      where m.user_id = auth.uid()), '[]'::jsonb))
$$;
revoke all on function public.my_access() from public, anon;
grant execute on function public.my_access() to authenticated;

revoke all on all functions in schema app from public, anon;
grant execute on all functions in schema app to authenticated;

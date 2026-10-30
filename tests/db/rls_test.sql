-- Security tests for supabase/migrations. Run with tests/db/run.sh.
-- Each check signs in as a test user (by setting the JWT claims Supabase would set),
-- tries to read or write, and fails loudly if the result is wrong.
\set ON_ERROR_STOP 1
set client_min_messages = warning;

-- ---------- test users and companies (as the database owner) ----------
insert into auth.users(id, email) values
 ('00000000-0000-0000-0000-00000000000a','owner@test'),
 ('00000000-0000-0000-0000-0000000000a1','alice@a.test'),
 ('00000000-0000-0000-0000-0000000000a2','bob@a.test'),
 ('00000000-0000-0000-0000-0000000000a3','cara@a.test'),
 ('00000000-0000-0000-0000-0000000000a4','gus@a.test'),
 ('00000000-0000-0000-0000-0000000000a5','bot@a.test'),
 ('00000000-0000-0000-0000-0000000000b1','dan@b.test'),
 ('00000000-0000-0000-0000-0000000000e1','eve@x.test'),
 ('00000000-0000-0000-0000-0000000000e2','newhire@a.test');
insert into auth.mfa_factors(user_id, status) values
 ('00000000-0000-0000-0000-00000000000a','verified'),
 ('00000000-0000-0000-0000-0000000000a1','verified'),
 ('00000000-0000-0000-0000-0000000000b1','verified');
insert into public.companies(id, name) values
 ('11111111-1111-1111-1111-111111111111','Company A'),
 ('22222222-2222-2222-2222-222222222222','Company B');
insert into public.platform_admins(user_id) values ('00000000-0000-0000-0000-00000000000a');
insert into public.memberships(company_id, user_id, role, scope) values
 ('11111111-1111-1111-1111-111111111111','00000000-0000-0000-0000-0000000000a1','company_admin','all'),
 ('11111111-1111-1111-1111-111111111111','00000000-0000-0000-0000-0000000000a2','employee','all'),
 ('11111111-1111-1111-1111-111111111111','00000000-0000-0000-0000-0000000000a3','employee','assigned'),
 ('11111111-1111-1111-1111-111111111111','00000000-0000-0000-0000-0000000000a4','guest','all'),
 ('11111111-1111-1111-1111-111111111111','00000000-0000-0000-0000-0000000000a5','bot','all'),
 ('22222222-2222-2222-2222-222222222222','00000000-0000-0000-0000-0000000000b1','company_admin','all');
insert into public.businesses(id, company_id, owner_id, data) values
 ('a1','11111111-1111-1111-1111-111111111111',null,'{"name":"A One"}'),
 ('a2','11111111-1111-1111-1111-111111111111','00000000-0000-0000-0000-0000000000a3','{"name":"A Two (Cara)"}'),
 ('a3','11111111-1111-1111-1111-111111111111',null,'{"name":"A Three"}'),
 ('b1','22222222-2222-2222-2222-222222222222',null,'{"name":"B One"}');
insert into public.outreach(id, company_id, biz_id, data) values
 ('o1','11111111-1111-1111-1111-111111111111','a1','{"channel":"call"}');
insert into public.shares(company_id, table_name, record_id, user_id) values
 ('11111111-1111-1111-1111-111111111111','businesses','a3','00000000-0000-0000-0000-0000000000a4');
insert into public.invites(company_id, email, role, token_hash) values
 ('11111111-1111-1111-1111-111111111111','newhire@a.test','employee', encode(extensions.digest('code-123','sha256'),'hex'));

-- ---------- helpers ----------
create or replace function pg_temp.as_user(u text, aal text default 'aal1') returns void language plpgsql as $$
begin
  perform set_config('request.jwt.claims', json_build_object('sub', u, 'aal', aal,
    'email', (select email from auth.users where id = u::uuid), 'role', 'authenticated')::text, false);
  execute 'set role authenticated';
end $$;
create or replace function pg_temp.check(name text, ok boolean) returns void language plpgsql as $$
begin
  if ok is distinct from true then raise exception 'FAIL: %', name; end if;
  raise warning 'PASS: %', name;
end $$;
-- runs a statement and reports whether the database refused it
create or replace function pg_temp.refused(stmt text) returns boolean language plpgsql as $$
declare n int;
begin
  execute stmt; get diagnostics n = row_count;
  return n = 0;            -- RLS hides rows from update/delete instead of erroring
exception when insufficient_privilege or check_violation or raise_exception then return true;
  when others then if sqlerrm like '%row-level security%' then return true; end if; raise;
end $$;
grant execute on function pg_temp.as_user(text,text), pg_temp.check(text,boolean), pg_temp.refused(text) to authenticated, anon;

-- ---------- not signed in ----------
set role anon;
select pg_temp.check('anon cannot read businesses', pg_temp.refused('select 1 from public.businesses'));
reset role;

-- ---------- platform owner ----------
select pg_temp.as_user('00000000-0000-0000-0000-00000000000a','aal1');
select pg_temp.check('owner without MFA code sees nothing', (select count(*) from public.businesses) = 0);
reset role;
select pg_temp.as_user('00000000-0000-0000-0000-00000000000a','aal2');
select pg_temp.check('owner with MFA sees every company', (select count(*) from public.businesses) = 4);
select pg_temp.check('owner can create a company', not pg_temp.refused($$insert into public.companies(name) values ('Company C')$$));
reset role;

-- ---------- company admin ----------
select pg_temp.as_user('00000000-0000-0000-0000-0000000000a1','aal1');
select pg_temp.check('admin without MFA code sees nothing', (select count(*) from public.businesses) = 0);
reset role;
select pg_temp.as_user('00000000-0000-0000-0000-0000000000a1','aal2');
select pg_temp.check('admin sees all of company A', (select count(*) from public.businesses) = 3);
select pg_temp.check('admin cannot see company B', not exists (select 1 from public.businesses where id = 'b1'));
select pg_temp.check('admin cannot write into company B', pg_temp.refused(
  $$insert into public.businesses(id, company_id, data) values ('x','22222222-2222-2222-2222-222222222222','{}')$$));
select pg_temp.check('admin cannot move a record to company B', pg_temp.refused(
  $$update public.businesses set company_id='22222222-2222-2222-2222-222222222222' where id='a1'$$));
select pg_temp.check('admin cannot create companies', pg_temp.refused($$insert into public.companies(name) values ('Mine')$$));
select pg_temp.check('admin cannot make themselves platform owner', pg_temp.refused(
  $$insert into public.platform_admins(user_id) values ('00000000-0000-0000-0000-0000000000a1')$$));
select pg_temp.check('admin cannot change their own role', pg_temp.refused(
  $$update public.memberships set role='employee' where user_id='00000000-0000-0000-0000-0000000000a1'$$));
select pg_temp.check('admin cannot add a bot', pg_temp.refused(
  $$insert into public.memberships(company_id,user_id,role) values ('11111111-1111-1111-1111-111111111111','00000000-0000-0000-0000-0000000000e1','bot')$$));
select pg_temp.check('admin can change an employee to assigned only', not pg_temp.refused(
  $$update public.memberships set scope='assigned' where user_id='00000000-0000-0000-0000-0000000000a2'$$));
select pg_temp.check('admin cannot add people to company B', pg_temp.refused(
  $$insert into public.memberships(company_id,user_id,role) values ('22222222-2222-2222-2222-222222222222','00000000-0000-0000-0000-0000000000e1','employee')$$));
select pg_temp.check('admin reads their audit log', (select count(*) from public.audit_log) > 0 and not exists (select 1 from public.audit_log where company_id='22222222-2222-2222-2222-222222222222'));
update public.memberships set scope='all' where user_id='00000000-0000-0000-0000-0000000000a2';
reset role;

-- ---------- employees ----------
select pg_temp.as_user('00000000-0000-0000-0000-0000000000a2');
select pg_temp.check('employee (all) sees company A', (select count(*) from public.businesses) = 3);
select pg_temp.check('employee can add a business', not pg_temp.refused(
  $$insert into public.businesses(id, company_id, data) values ('a9','11111111-1111-1111-1111-111111111111','{"name":"New"}')$$));
select pg_temp.check('the write is stamped with who made it', (select updated_by from public.businesses where id='a9') = '00000000-0000-0000-0000-0000000000a2');
select pg_temp.check('employee cannot see who else is a member', (select count(*) from public.memberships) = 1);
select pg_temp.check('employee cannot invite people', pg_temp.refused(
  $$insert into public.invites(company_id,email,role,token_hash) values ('11111111-1111-1111-1111-111111111111','x@x','employee','h')$$));
select pg_temp.check('employee cannot read the audit log', (select count(*) from public.audit_log) = 0);
reset role;
select pg_temp.as_user('00000000-0000-0000-0000-0000000000a3');
select pg_temp.check('employee (assigned) sees only their own business', (select string_agg(id, ',') from public.businesses) = 'a2');
select pg_temp.check('employee (assigned) cannot edit others''', pg_temp.refused($$update public.businesses set data='{}' where id='a1'$$));
reset role;

-- ---------- guest ----------
select pg_temp.as_user('00000000-0000-0000-0000-0000000000a4');
select pg_temp.check('guest sees only the shared business', (select string_agg(id, ',') from public.businesses) = 'a3');
select pg_temp.check('guest cannot edit a view-only share', pg_temp.refused($$update public.businesses set data='{}' where id='a3'$$));
select pg_temp.check('guest cannot delete', pg_temp.refused($$delete from public.businesses where id='a3'$$));
select pg_temp.check('guest sees no outreach', (select count(*) from public.outreach) = 0);
reset role;

-- ---------- bot ----------
select pg_temp.as_user('00000000-0000-0000-0000-0000000000a5');
select pg_temp.check('bot reads company A', (select count(*) from public.businesses) >= 3);
select pg_temp.check('bot can add a signal', not pg_temp.refused(
  $$insert into public.signals(id, company_id, biz_id, data) values ('s1','11111111-1111-1111-1111-111111111111','a1','{"type":"hiring"}')$$));
select pg_temp.check('bot cannot log outreach', pg_temp.refused(
  $$insert into public.outreach(id, company_id, data) values ('o9','11111111-1111-1111-1111-111111111111','{}')$$));
select pg_temp.check('bot cannot delete', pg_temp.refused($$delete from public.businesses where id='a1'$$));
select pg_temp.check('bot cannot change settings', pg_temp.refused(
  $$insert into public.settings(id, company_id, data) values ('targeting','11111111-1111-1111-1111-111111111111','{}')$$));
select pg_temp.check('bot cannot see company B', not exists (select 1 from public.businesses where id='b1'));
reset role;

-- ---------- someone with no company ----------
select pg_temp.as_user('00000000-0000-0000-0000-0000000000e1');
select pg_temp.check('a stranger sees nothing', (select count(*) from public.businesses) = 0 and (select count(*) from public.companies) = 0);
select pg_temp.check('a stranger cannot join by writing a membership', pg_temp.refused(
  $$insert into public.memberships(company_id,user_id,role) values ('11111111-1111-1111-1111-111111111111','00000000-0000-0000-0000-0000000000e1','company_admin')$$));
select pg_temp.check('a stranger cannot use someone else''s invite', pg_temp.refused($$select public.accept_invite('code-123')$$));
reset role;

-- ---------- invites ----------
select pg_temp.as_user('00000000-0000-0000-0000-0000000000e2');
select pg_temp.check('a wrong code is refused', pg_temp.refused($$select public.accept_invite('wrong')$$));
select pg_temp.check('the invited person can accept', public.accept_invite('code-123') = '11111111-1111-1111-1111-111111111111');
select pg_temp.check('they joined as an employee', (public.my_access()->'companies'->0->>'role') = 'employee');
select pg_temp.check('the code only works once', pg_temp.refused($$select public.accept_invite('code-123')$$));
reset role;

-- ---------- other company admin ----------
select pg_temp.as_user('00000000-0000-0000-0000-0000000000b1','aal2');
select pg_temp.check('company B admin sees only B', (select string_agg(id, ',') from public.businesses) = 'b1');
select pg_temp.check('company B admin cannot delete A records', pg_temp.refused($$delete from public.businesses where id='a1'$$));
reset role;

-- ---------- audit ----------
select pg_temp.check('every write was logged', (select count(*) from public.audit_log where table_name='businesses' and record_id='a9') = 1);
\echo 'ALL CHECKS PASSED'

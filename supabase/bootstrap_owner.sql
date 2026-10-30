-- Run ONCE by hand in the Supabase SQL editor, after you have:
--   1. signed up on the private preview with your own email and password, and
--   2. set up your authenticator app (MFA).
-- Replace the email below with yours. This makes you the platform owner and creates the
-- first company. No password or key is stored here or anywhere in the repo.
do $$
declare
  owner_email text := 'YOUR-EMAIL@example.com';
  u uuid;
  c uuid;
begin
  select id into u from auth.users where lower(email) = lower(owner_email);
  if u is null then raise exception 'No user with that email. Sign up on the preview first.'; end if;
  if not exists (select 1 from auth.mfa_factors where user_id = u and status = 'verified') then
    raise exception 'Set up your authenticator app first, then run this again.';
  end if;
  insert into public.platform_admins(user_id) values (u) on conflict do nothing;
  select id into c from public.companies where name = 'Referral Bridge';
  if c is null then
    insert into public.companies(name, created_by) values ('Referral Bridge', u) returning id into c;
  end if;
  insert into public.memberships(company_id, user_id, role, created_by)
  values (c, u, 'company_admin', u) on conflict (company_id, user_id) do update set role = 'company_admin';
  raise notice 'Done. % is the platform owner and an admin of company %', owner_email, c;
end $$;

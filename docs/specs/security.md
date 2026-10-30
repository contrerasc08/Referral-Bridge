# Security and permissions (Phase 1)

Referral Bridge is moving from a claude.ai artifact to Supabase: email and password sign-in, authenticator-app MFA, and Postgres with row-level security. The database itself decides who can see and change each record, so a bug in the page can't leak another company's data.

The rules are in [`supabase/migrations/`](../../supabase/migrations/). The tests that prove them are in [`tests/db/`](../../tests/db/).

## Roles

| Role | Who | Sees | Can do | MFA |
|---|---|---|---|---|
| Platform owner | The owner only (`platform_admins`) | Every company | Everything, including creating companies and adding bots | Required for any access |
| Company admin | A company's lead | Their company | Add, edit and delete records; invite, change and remove people (not themselves); read the audit log | Required for any access |
| Employee | Staff | Their company, or only records assigned to them (`scope = 'assigned'`) | Add, edit and delete records they can see | Required once they set it up |
| Guest | A partner or specialist | Only records in `shares` | View, or edit when the share allows | Required once they set it up |
| Bot | A scheduled bot's own login | Its company | Add and update businesses, specialists, signals, news, drafts, bot logs, research and lead requests, and usage. It can never delete records, log outreach, change settings or manage people | Not used |

## Rules that always hold

- Nobody who isn't signed in can read or write anything.
- No record can move to another company.
- `platform_admins` can't be written from the app, only from the Supabase dashboard.
- Invites are one-time codes, stored only as a hash. They expire after 7 days and only work for the invited email address.
- Every add, change and delete on app data is written to `audit_log` along with who made it.
- The browser only ever gets the publishable key. The service-role key is never put in the repo or the page.

## Data shape

Each app collection (`businesses`, `cois`, `matches`, `signals`, `news`, `outreach`, `drafts`, `botlog`, `settings`, `contact_requests`, `lead_requests`, `provider_usage`, `tasks`) is a table with `id`, `company_id`, `owner_id`, `biz_id`, `coi_id`, a `data` jsonb holding the record's fields, and timestamps. This lets today's app move over unchanged. Fields that need joins or reports can become real columns later.

## Setting up the owner account

Public sign-ups are off, so accounts are created in the Supabase dashboard.

1. In Supabase, go to **Authentication → Users → Add user → Send invitation** and enter your email.
2. Open the email link. The portal asks you to choose a password (12+ characters), then to set up your authenticator app.
3. In the Supabase SQL editor, open [`supabase/bootstrap_owner.sql`](../../supabase/bootstrap_owner.sql), put in your email and run it once. It refuses to run until your authenticator app is set up.

## Adding people

1. Create their account the same way (**Add user → Send invitation**). They choose a password and set up their authenticator app.
2. Give them an invite code for your company and role. They enter it on the portal's "Join your company" screen, or open `https://<portal>/?invite=<code>`. Until then they're signed in but can't see any records.

A screen for company admins to create invite codes comes with the storage-layer step.

## The portal ([`web/`](../../web/))

- Sign in with email and password. Everyone sets up an authenticator app before they get in, and the code is asked at every sign-in.
- Password reset by email. The reply is the same whether or not the account exists. Someone with MFA enters their code before choosing a new password.
- The page refuses to start if it's given a secret or `service_role` key.
- Strict security headers (`web/_headers`): scripts only from the portal itself, connections only to Supabase, no framing, no search indexing.
- The Supabase client is a pinned copy in `web/vendor/`, so no outside script can change.

## Supabase project settings

- Data API on. Automatically exposing new tables off. Automatic RLS on.
- Authentication: public sign-ups off (invite only), MFA (TOTP) on, minimum password length of 12 or more.
- Authentication → URL Configuration: Site URL and Redirect URLs set to the portal address (see [`docs/deploy.md`](../deploy.md)).

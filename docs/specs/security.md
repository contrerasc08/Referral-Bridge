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

1. Sign up on the private preview and set up your authenticator app.
2. In the Supabase SQL editor, open [`supabase/bootstrap_owner.sql`](../../supabase/bootstrap_owner.sql), put in your email and run it once.

## Supabase project settings

- Data API on. Automatically exposing new tables off. Automatic RLS on.
- Authentication: public sign-ups off (invite only), MFA (TOTP) on, minimum password length of 12 or more.

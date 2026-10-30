#!/usr/bin/env bash
# Tests the Supabase security rules on a local, throwaway Postgres database.
# Needs psql and a Postgres server you can create databases on (PGHOST/PGPORT/PGUSER).
# Usage: tests/db/run.sh
set -euo pipefail
cd "$(dirname "$0")/../.."
DB="rb_rls_test_$$"
createdb "$DB"
trap 'dropdb --if-exists "$DB"' EXIT
psql -q -v ON_ERROR_STOP=1 -d "$DB" -f tests/db/supabase_shim.sql
for f in supabase/migrations/*.sql; do psql -q -v ON_ERROR_STOP=1 -d "$DB" -f "$f"; done
psql -qAt -v ON_ERROR_STOP=1 -d "$DB" -f tests/db/rls_test.sql 2>&1 | grep -v '^$' | sed 's/^psql:[^ ]* WARNING:  //'

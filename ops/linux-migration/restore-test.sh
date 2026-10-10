#!/usr/bin/env bash
set -euo pipefail

# Restores into a separately identified disposable database. Never use production as target.
# Required:
#   SOURCE_DATABASE_URL=... (read-only identity check only; never printed)
#   MIGRATION_TARGET_DATABASE_URL=... (isolated disposable target)
#   MIGRATION_TARGET_DATABASE_NAME=... (expected target database name)
#   ALLOW_DISPOSABLE_RESTORE=YES
# Usage: bash restore-test.sh /secure/path/export.dump

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <custom-format-dump>" >&2
  exit 2
fi
dump=$1
[[ -f "$dump" && -s "$dump" ]] || { echo "FAIL: dump missing or empty" >&2; exit 1; }
command -v pg_restore >/dev/null 2>&1 || { echo "FAIL: pg_restore is required" >&2; exit 1; }
command -v psql >/dev/null 2>&1 || { echo "FAIL: psql is required" >&2; exit 1; }

[[ "${ALLOW_DISPOSABLE_RESTORE:-}" == "YES" ]] || {
  echo "STOP: set ALLOW_DISPOSABLE_RESTORE=YES only after independently confirming the target is disposable." >&2
  exit 3
}
: "${SOURCE_DATABASE_URL:?Set SOURCE_DATABASE_URL for a read-only source/target identity comparison}"
: "${MIGRATION_TARGET_DATABASE_URL:?Set MIGRATION_TARGET_DATABASE_URL to an isolated disposable database}"
: "${MIGRATION_TARGET_DATABASE_NAME:?Set MIGRATION_TARGET_DATABASE_NAME to the expected target database name}"

# Query identities only; never echo connection URLs or credentials.
source_identity=$(psql "$SOURCE_DATABASE_URL" -X -Atqc "select coalesce(inet_server_addr()::text,'local') || ':' || inet_server_port()::text || '/' || current_database()")
target_identity=$(psql "$MIGRATION_TARGET_DATABASE_URL" -X -Atqc "select coalesce(inet_server_addr()::text,'local') || ':' || inet_server_port()::text || '/' || current_database()")
target_db=$(psql "$MIGRATION_TARGET_DATABASE_URL" -X -Atqc 'select current_database()')
target_user=$(psql "$MIGRATION_TARGET_DATABASE_URL" -X -Atqc 'select current_user')

[[ "$source_identity" != "$target_identity" ]] || {
  echo "STOP: source and target resolve to the same server/database identity." >&2; exit 4;
}
[[ "$target_db" == "$MIGRATION_TARGET_DATABASE_NAME" ]] || {
  echo "STOP: connected database name does not match MIGRATION_TARGET_DATABASE_NAME." >&2; exit 4;
}
[[ -n "$target_user" && "$target_user" != "postgres" ]] || {
  echo "STOP: use a dedicated least-privilege restore role, not the postgres superuser." >&2; exit 4;
}

# Require a clearly disposable target name; this is an additional guard, not proof by itself.
case "$target_db" in
  *test*|*restore*|*disposable*|*migration*) ;;
  *) echo "STOP: target database name must visibly identify a test/restore/disposable/migration database." >&2; exit 4 ;;
esac

# Never use --clean/--if-exists; target should be newly created and empty.
table_count=$(psql "$MIGRATION_TARGET_DATABASE_URL" -X -Atqc "select count(*) from pg_catalog.pg_tables where schemaname not in ('pg_catalog','information_schema')")
[[ "$table_count" == "0" ]] || {
  echo "STOP: target is not empty (user table count=$table_count); create a fresh disposable database." >&2; exit 5;
}

echo "Restoring into verified isolated target (credentials redacted)..."
pg_restore --exit-on-error --no-owner --no-acl --dbname="$MIGRATION_TARGET_DATABASE_URL" "$dump"
psql "$MIGRATION_TARGET_DATABASE_URL" -X -v ON_ERROR_STOP=1 -Atqc "select 'restore-ok', current_database(), count(*) from pg_catalog.pg_tables where schemaname not in ('pg_catalog','information_schema')"
echo "PASS: restore completed. This is not authorization to cut over production."

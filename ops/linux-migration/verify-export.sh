#!/usr/bin/env bash
set -euo pipefail

# Verifies an existing PostgreSQL custom-format dump and SHA-256 sidecar only.
# Usage: bash verify-export.sh /secure/path/export.dump /secure/path/export.dump.sha256

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <custom-format-dump> <sha256-sidecar>" >&2
  exit 2
fi
dump=$1
sidecar=$2

[[ -f "$dump" && -s "$dump" ]] || { echo "FAIL: dump missing or empty" >&2; exit 1; }
[[ -f "$sidecar" && -s "$sidecar" ]] || { echo "FAIL: checksum sidecar missing or empty" >&2; exit 1; }
command -v sha256sum >/dev/null 2>&1 || { echo "FAIL: sha256sum is required" >&2; exit 1; }
command -v pg_restore >/dev/null 2>&1 || { echo "FAIL: pg_restore is required" >&2; exit 1; }

# Sidecar must contain the expected hash for this dump filename; run from its directory.
dump_dir=$(cd "$(dirname "$dump")" && pwd)
dump_name=$(basename "$dump")
sidecar_dir=$(cd "$(dirname "$sidecar")" && pwd)
sidecar_name=$(basename "$sidecar")
[[ "$dump_dir" == "$sidecar_dir" ]] || { echo "FAIL: dump and checksum sidecar must be in the same directory" >&2; exit 1; }

(
  cd "$dump_dir"
  sha256sum --check "$sidecar_name"
)
pg_restore --list "$dump" >/dev/null
printf 'PASS: SHA-256 matches and pg_restore can read the archive directory.\n'
printf 'NOTE: This does not prove the dump can be restored; run restore-test.sh against an isolated disposable database.\n'
printf 'Dump bytes: %s\n' "$(wc -c < "$dump" | tr -d ' ')"

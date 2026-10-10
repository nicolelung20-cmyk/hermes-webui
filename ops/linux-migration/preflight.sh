#!/usr/bin/env bash
set -euo pipefail

# Read-only host/tool preflight. Does not connect to production or display secret values.
printf '== Linux migration preflight (read-only) ==\n'
printf 'OS: '; uname -srm
if [[ -r /etc/os-release ]]; then
  . /etc/os-release
  printf 'Distribution: %s %s\n' "${ID:-unknown}" "${VERSION_ID:-unknown}"
fi
printf 'User: %s\n' "$(id -un)"
printf 'UID: %s\n' "$(id -u)"
printf 'Working directory: %s\n' "$PWD"
printf '\nTool availability:\n'
for cmd in git bash ssh scp rsync tar sha256sum shasum curl jq node npm python3 pip3 psql pg_dump pg_restore; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf '  PASS  %s\n' "$cmd"
  else
    printf '  MISS  %s\n' "$cmd"
  fi
done
printf '\nEnvironment variable names only (values are never printed):\n'
for name in SOURCE_DATABASE_URL MIGRATION_TARGET_DATABASE_URL ALLOW_DISPOSABLE_RESTORE; do
  if [[ -n "${!name-}" ]]; then printf '  SET   %s\n' "$name"; else printf '  UNSET %s\n' "$name"; fi
done
printf '\nSafety defaults:\n'
printf '  No production connection attempted.\n'
printf '  No files changed. No services restarted. No deployment performed.\n'
printf '  Trading and real-money movement must remain disabled.\n'

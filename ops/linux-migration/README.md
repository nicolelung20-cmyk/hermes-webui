# Linux migration toolkit for Elevat / Hermes

This toolkit is designed for a **direct Linux host** (self-managed hardware or a VM you control), without introducing another application hosting platform.

## Safety invariants

- Existing production remains unchanged while discovery, backup, export verification, restore testing, and parity checks run.
- Never place credentials, database URLs, API keys, SSH private keys, or dumps in Git.
- Keep trading execution and all real-money movement disabled.
- Do not cut over until a database backup is confirmed, an independent export passes checksum/format checks, that export is restored into an isolated disposable database, persistent volumes are separately backed up, and the destination passes security checks.
- A Git branch or successful script run is not proof that a backup exists or that a restore works.

## Contents

- `preflight.sh`: read-only tool/host checks; does not connect to production.
- `verify-export.sh`: checks an existing PostgreSQL custom-format dump and its SHA-256 sidecar.
- `restore-test.sh`: restores an export only to a separately named, explicitly approved disposable target database.
- `SKILL.md`: operator workflow and stop conditions.

## Use on Linux

1. Copy/clone this repository on the Linux host using a private working directory.
2. Review the scripts before running them.
3. Run `bash ops/linux-migration/preflight.sh`.
4. Create a database export using your approved backup procedure; write it outside the repository with restrictive permissions. Keep credentials in the shell environment or a secrets manager, never in command history or files committed to Git.
5. Run `bash ops/linux-migration/verify-export.sh /secure/path/export.dump /secure/path/export.dump.sha256`.
6. Run the isolated restore test only after verifying that the target is disposable and distinct from production.
7. Back up each persistent volume independently; a database dump does not include application files, auth state, uploaded files, or other mounted volume contents.

## Not automated by design

This kit does not provision servers, read production secrets, change DNS, deploy, stop services, alter databases, enable trading, or cut over traffic. Those actions require evidence and explicit review after all gates pass.

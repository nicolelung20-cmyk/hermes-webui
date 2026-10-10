---
name: linux-server-migration
description: Safely migrate Elevat/Hermes projects to a directly controlled Linux server while preserving production until backups, independent exports, isolated restore tests, and security checks are verified.
---

# Linux Server Migration Skill

## Objective
Move repositories, services, scheduled jobs, database state, persistent files, and runtime configuration to a Linux host the operator controls. Avoid adding an intermediary application-hosting platform. Git hosting is only source control; it is not the destination runtime.

## Non-negotiable controls
1. Production stays online and unchanged during preparation.
2. Live trading, order execution, payment capture, and real-money transfers stay disabled.
3. Never read secrets into chat, print them, commit them, or put them in logs.
4. Do not copy workloads or cut over before all required gates pass.
5. Do not infer a backup from a dashboard status or successful command. Record timestamp, object identity, size, checksum, and restore evidence.
6. Back up mounted volumes separately from database exports.
7. Stop on ambiguous source/target identity, missing permissions, failed checksum, failed restore, or unexpected service behavior.

## Phases

### A. Inventory (read-only)
- Enumerate repositories, branches, build/start commands, service ports, domains, scheduled jobs, webhooks, storage volumes, and data dependencies.
- Identify secrets by variable *name only*; do not print values.
- Identify production vs staging/test by explicit environment IDs and connection metadata.
- Document rollback path and DNS/routing state.

### B. Backup gate
- Confirm a provider-managed database backup with timestamp and project identity.
- Produce a separate logical database export to secure storage outside Git.
- Verify its checksum and expected PostgreSQL dump format.
- Restore it into an isolated disposable database and run sanity checks.
- Back up every persistent volume independently and verify file counts/checksums.
- If any item is missing, stop. Do not copy production workloads or cut over.

### C. Linux destination security
- Use a dedicated non-root service account per workload where practical.
- SSH keys only; disable password SSH and root login where supported.
- Firewall inbound access to the minimum required ports; keep admin endpoints private or VPN-only.
- Use restrictive permissions for secret files and backups; prefer a secrets manager or root-owned environment files outside the repo.
- Pin runtime versions, patch the OS, enable unattended security updates where appropriate, and configure logs/rotation.
- Test restore and recovery procedures before moving traffic.

### D. Stage and verify
- Deploy from a reviewed commit to a non-production Linux instance.
- Import only verified copies of data and volume state.
- Verify service health, authentication, permissions, scheduled jobs, observability, and backup restore.
- Keep trading/order/payment actions disabled and stub external side effects in tests.
- Compare key database counts, schema/migration versions, file checksums, and service behavior.

### E. Cutover gate
Cutover is forbidden until all are documented as PASS:
- provider backup confirmed;
- independent export checksum and format verified;
- isolated restore test successful;
- persistent volume backups verified;
- Linux security checklist passed;
- smoke tests and rollback rehearsed;
- explicit operator approval for traffic/DNS change.

If any gate fails, leave production unchanged and report the exact blocker. Never auto-merge or auto-deploy this migration toolkit.

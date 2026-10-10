# Skills Index

> **Maintenance contract:** Individual skill files are authoritative. Update and validate skill content first, then refresh this index and related derived metadata last. Keep this index synchronized in the same change; do not leave it stale.

## Skill maintenance
- Skill creation and edits must invoke the repository's metadata/index generator when one exists.
- If no generator exists, update this index manually after the skill content and version metadata are final.
- Validate paths, frontmatter, versions, and references before considering an update complete.
- Automation must be idempotent and must not auto-deploy or expand permissions.
- Follow [references/versioning.md](references/versioning.md).

## Core skills
- [skill-creator](skills/skill-creator/SKILL.md) — create, maintain, validate, version, and index skills with content-first freshness handling.

## Index policy
This file is an inventory/metadata layer, not the source of truth for skill behavior. Do not edit skill behavior only here; make changes in the corresponding skill file first and then refresh this index.

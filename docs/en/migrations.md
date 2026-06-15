# Data migrations

<p align="right">
  <a href="../ko/migrations.md">한국어</a> ·
  <strong>English</strong>
</p>

## Normalized-email backfill

New and updated users store `email_normalized`. Lookups remain compatible with legacy documents.

### Dry run (default)

```bash
flask --app app:create_app backfill-emails
```

Reports planned changes and conflicts **without writing**.

### Apply

```bash
flask --app app:create_app backfill-emails --apply
```

Idempotent; does not delete or merge accounts.

### Indexes

Add a unique `email_normalized` index only after a dry run shows no conflicts. Startup indexes and the backfill command live in `services/migrations.py`.

## General principles

- Use **non-destructive** migrations on production databases.
- Do not force schema changes without backups.

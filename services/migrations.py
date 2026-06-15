"""Non-destructive data migrations exposed as Flask CLI commands."""
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

import click

from extensions.db import mongo
from models.user import normalize_email_field

if TYPE_CHECKING:  # pragma: no cover - typing only
    from flask import Flask


def register_migration_commands(app: Flask) -> None:
    """Register the email normalization backfill command on ``app``."""

    @app.cli.command('backfill-emails')
    @click.option('--apply', 'apply_changes', is_flag=True, default=False,
                  help='Persist changes. Without this flag the command is a dry run.')
    def backfill_emails(apply_changes: bool) -> None:
        """Backfill ``email_normalized`` and report normalized-email conflicts.

        This never deletes, merges, or modifies account ownership. It only fills
        the missing ``email_normalized`` field and surfaces collisions so they
        can be resolved by hand before any unique index is added.
        """
        buckets: dict[str, list[str]] = defaultdict(list)
        to_update: list[tuple[object, str]] = []

        for user in mongo.db.users.find({}, {'email': 1, 'email_normalized': 1}):
            normalized = normalize_email_field(user.get('email'))
            if not normalized:
                continue
            buckets[normalized].append(str(user['_id']))
            if user.get('email_normalized') != normalized:
                to_update.append((user['_id'], normalized))

        conflicts = {key: ids for key, ids in buckets.items() if len(ids) > 1}

        click.echo(f'Scanned users with email: {sum(len(v) for v in buckets.values())}')
        click.echo(f'Records needing email_normalized: {len(to_update)}')
        click.echo(f'Conflicting normalized emails: {len(conflicts)}')
        for key, ids in conflicts.items():
            click.echo(f'  CONFLICT {key}: {", ".join(ids)}')

        if not apply_changes:
            click.echo('Dry run only. Re-run with --apply to write email_normalized values.')
            return

        for user_id, normalized in to_update:
            mongo.db.users.update_one(
                {'_id': user_id}, {'$set': {'email_normalized': normalized}}
            )
        click.echo(f'Updated {len(to_update)} record(s).')
        if conflicts:
            click.echo('Unique normalized-email index NOT created: resolve conflicts first.')
        else:
            click.echo('No conflicts: a unique partial index on email_normalized is safe to add.')

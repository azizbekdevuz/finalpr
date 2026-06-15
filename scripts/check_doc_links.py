#!/usr/bin/env python3
"""Verify relative Markdown links in docs/ and README language switchers."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
SWITCHER_RE = re.compile(r'<a href="([^"]+)">')

SKIP_PREFIXES = ('http://', 'https://', 'mailto:', '#')


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding='utf-8')
    for match in LINK_RE.finditer(text):
        target = match.group(1).strip()
        if target.startswith(SKIP_PREFIXES):
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.is_file():
            errors.append(f'{path.relative_to(ROOT)}: broken link -> {target}')
    for match in SWITCHER_RE.finditer(text):
        target = match.group(1).strip()
        if target.startswith(SKIP_PREFIXES):
            continue
        resolved = (path.parent / target).resolve()
        if not resolved.is_file():
            errors.append(f'{path.relative_to(ROOT)}: broken switcher -> {target}')
    return errors


def main() -> int:
    files = [ROOT / 'README.md', ROOT / 'README.en.md']
    files.extend((ROOT / 'docs').rglob('*.md'))
    all_errors: list[str] = []
    for path in sorted(files):
        all_errors.extend(check_file(path))
    if all_errors:
        print('Documentation link errors:')
        for err in all_errors:
            print(f'  - {err}')
        return 1
    print(f'OK: checked {len(files)} markdown files')
    return 0


if __name__ == '__main__':
    sys.exit(main())

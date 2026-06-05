"""Single source of truth for validating user-supplied redirect targets.

Prevents open-redirect vulnerabilities by only accepting same-host relative
paths and rejecting absolute or scheme-relative URLs.
"""
from __future__ import annotations

from urllib.parse import urljoin, urlparse

from flask import request, url_for


def is_safe_local_path(target: str | None) -> bool:
    """Return ``True`` when ``target`` is a safe same-host relative path."""
    if not target:
        return False
    # Reject scheme-relative URLs like "//evil.example/path".
    if target.startswith('//'):
        return False
    # Resolve against the current host and confirm it stays on this origin.
    host_url = request.host_url
    resolved = urljoin(host_url, target)
    parsed_host = urlparse(host_url)
    parsed_target = urlparse(resolved)
    return (
        parsed_target.scheme in {'http', 'https'}
        and parsed_target.netloc == parsed_host.netloc
    )


def safe_redirect_target(target: str | None, fallback_endpoint: str = 'main.index') -> str:
    """Return ``target`` when it is a safe local path, else a safe fallback."""
    if is_safe_local_path(target):
        return target  # type: ignore[return-value]
    return url_for(fallback_endpoint)

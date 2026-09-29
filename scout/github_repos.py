"""GitHub repository scout via Search API."""
from __future__ import annotations

import os
from typing import Any

import requests

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
DEFAULT_TIMEOUT = 20


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "scout-hub",
    }
    token = (os.environ.get("GITHUB_TOKEN") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_status() -> dict[str, Any]:
    """Lightweight probe of GitHub Search API availability."""
    try:
        r = requests.get(
            GITHUB_SEARCH_URL,
            headers=_headers(),
            params={"q": "stars:>10000", "per_page": 1},
            timeout=10,
        )
        ok = r.status_code == 200
        return {
            "ok": ok,
            "authenticated": bool((os.environ.get("GITHUB_TOKEN") or "").strip()),
            "status_code": r.status_code,
            "message": None if ok else (r.text[:200] if r.text else f"HTTP {r.status_code}"),
        }
    except Exception as e:
        return {"ok": False, "authenticated": False, "status_code": None, "message": str(e)}


def search_repos(
    *,
    q: str = "",
    language: str = "",
    min_stars: int = 0,
    sort: str = "stars",
    per_page: int = 20,
) -> list[dict[str, Any]]:
    """
    Search GitHub repositories.

    sort: 'stars' | 'forks' (also accepted as GitHub sort values)
    Returns normalized list of repo dicts.
    """
    sort = (sort or "stars").strip().lower()
    if sort not in ("stars", "forks", "updated"):
        sort = "stars"

    per_page = max(1, min(int(per_page or 20), 50))
    min_stars = max(0, int(min_stars or 0))

    parts: list[str] = []
    query = (q or "").strip()
    if query:
        parts.append(query)
    else:
        parts.append("stars:>100")

    lang = (language or "").strip()
    if lang:
        parts.append(f"language:{lang}")
    if min_stars > 0:
        parts.append(f"stars:>={min_stars}")

    params = {
        "q": " ".join(parts),
        "sort": sort,
        "order": "desc",
        "per_page": per_page,
    }

    r = requests.get(
        GITHUB_SEARCH_URL,
        headers=_headers(),
        params=params,
        timeout=DEFAULT_TIMEOUT,
    )
    if r.status_code != 200:
        raise RuntimeError(f"GitHub Search API error {r.status_code}: {r.text[:300]}")

    items = (r.json() or {}).get("items") or []
    out: list[dict[str, Any]] = []
    for item in items:
        out.append(
            {
                "full_name": item.get("full_name") or "",
                "html_url": item.get("html_url") or "",
                "description": item.get("description") or "",
                "stars": item.get("stargazers_count") or 0,
                "forks": item.get("forks_count") or 0,
                "language": item.get("language") or "",
                "updated_at": item.get("updated_at") or "",
            }
        )
    return out

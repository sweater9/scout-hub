"""AI news scout: HN Algolia + RSS feeds."""
from __future__ import annotations

import email.utils
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

import requests

HN_URL = "http://hn.algolia.com/api/v1/search_by_date"
RSS_FEEDS = [
    {
        "source": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "source": "Google News AI",
        "url": "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
    },
]
DEFAULT_TIMEOUT = 15
UA = {"User-Agent": "scout-hub/1.0"}


def _parse_date(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip()
    # ISO-ish
    try:
        if value.endswith("Z"):
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).isoformat()
        if "T" in value:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    # RFC 2822 (RSS)
    try:
        dt = email.utils.parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo.timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return value


def _fetch_hn(query: str, limit: int) -> list[dict[str, Any]]:
    params = {
        "query": query or "AI",
        "tags": "story",
        "hitsPerPage": min(limit, 50),
    }
    r = requests.get(HN_URL, params=params, headers=UA, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    hits = (r.json() or {}).get("hits") or []
    out: list[dict[str, Any]] = []
    for h in hits:
        title = h.get("title") or h.get("story_title") or ""
        url = h.get("url") or (
            f"https://news.ycombinator.com/item?id={h.get('objectID')}" if h.get("objectID") else ""
        )
        if not title or not url:
            continue
        out.append(
            {
                "title": title,
                "url": url,
                "source": "Hacker News",
                "published": _parse_date(h.get("created_at")),
            }
        )
    return out


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _fetch_rss(feed: dict[str, str], limit: int) -> list[dict[str, Any]]:
    r = requests.get(feed["url"], headers=UA, timeout=DEFAULT_TIMEOUT)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    items: list[dict[str, Any]] = []
    # RSS 2.0
    for item in root.iter():
        if _local(item.tag) != "item":
            continue
        title = ""
        link = ""
        pub = ""
        for child in item:
            name = _local(child.tag)
            text = (child.text or "").strip()
            if name == "title":
                title = text
            elif name == "link":
                link = text
            elif name in ("pubDate", "published", "updated", "date"):
                pub = text
        if title and link:
            items.append(
                {
                    "title": title,
                    "url": link,
                    "source": feed["source"],
                    "published": _parse_date(pub),
                }
            )
        if len(items) >= limit:
            break
    # Atom fallback
    if not items:
        for entry in root.iter():
            if _local(entry.tag) != "entry":
                continue
            title = ""
            link = ""
            pub = ""
            for child in entry:
                name = _local(child.tag)
                if name == "title":
                    title = (child.text or "").strip()
                elif name == "link":
                    link = child.attrib.get("href") or (child.text or "").strip()
                elif name in ("published", "updated"):
                    pub = (child.text or "").strip()
            if title and link:
                items.append(
                    {
                        "title": title,
                        "url": link,
                        "source": feed["source"],
                        "published": _parse_date(pub),
                    }
                )
            if len(items) >= limit:
                break
    return items


def fetch_ai_news(*, q: str = "AI", limit: int = 20) -> list[dict[str, Any]]:
    """Fetch and merge recent AI news from HN + RSS. Soft-fails individual sources."""
    limit = max(1, min(int(limit or 20), 50))
    query = (q or "AI").strip() or "AI"
    collected: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        collected.extend(_fetch_hn(query, limit))
    except Exception as e:
        errors.append(f"HN: {e}")

    per_feed = max(5, limit // 2)
    for feed in RSS_FEEDS:
        try:
            collected.extend(_fetch_rss(feed, per_feed))
        except Exception as e:
            errors.append(f"{feed['source']}: {e}")

    # Deduplicate by URL
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in collected:
        url = item.get("url") or ""
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(item)

    def sort_key(it: dict[str, Any]) -> str:
        return it.get("published") or ""

    unique.sort(key=sort_key, reverse=True)
    result = unique[:limit]
    if not result and errors:
        raise RuntimeError("; ".join(errors))
    return result


def news_status() -> dict[str, Any]:
    backends: dict[str, Any] = {}
    try:
        r = requests.get(
            HN_URL,
            params={"query": "AI", "tags": "story", "hitsPerPage": 1},
            headers=UA,
            timeout=8,
        )
        backends["hacker_news"] = {"ok": r.status_code == 200, "status_code": r.status_code}
    except Exception as e:
        backends["hacker_news"] = {"ok": False, "message": str(e)}

    for feed in RSS_FEEDS:
        key = feed["source"].lower().replace(" ", "_")
        try:
            r = requests.head(feed["url"], headers=UA, timeout=8, allow_redirects=True)
            # some feeds reject HEAD
            ok = r.status_code < 400
            if not ok:
                r = requests.get(feed["url"], headers=UA, timeout=8)
                ok = r.status_code == 200
            backends[key] = {"ok": ok, "status_code": r.status_code}
        except Exception as e:
            backends[key] = {"ok": False, "message": str(e)}

    any_ok = any(v.get("ok") for v in backends.values())
    return {"ok": any_ok, "backends": backends}

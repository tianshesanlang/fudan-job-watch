#!/usr/bin/env python3
"""Scrape Fudan official notice/job list pages (Newcapec CMS). Stdlib only."""
from __future__ import annotations

import json
import re
import ssl
import urllib.request
from datetime import datetime, timezone, timedelta
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TZ = timezone(timedelta(hours=8))
CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (compatible; FudanJobWatch/1.1; +https://github.com/tianshesanlang/fudan-job-watch)"

ITEM_RE = re.compile(
    r'<li[^>]*>\s*<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>(.*?)</li>',
    re.I | re.S,
)
FALLBACK_RE = re.compile(
    r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
    re.I | re.S,
)
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")
TAG_RE = re.compile(r"<[^>]+>")
TRAIL_DATE_RE = re.compile(r"\s*20\d{2}-\d{2}-\d{2}\s*$")


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, context=CTX, timeout=25) as resp:
        raw = resp.read()
    for enc in ("utf-8", "gb18030", "gbk"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def abs_url(base: str, href: str) -> str:
    href = unescape(href.strip())
    if href.startswith("http"):
        return href
    origin = "/".join(base.split("/")[:3])
    if href.startswith("/"):
        return origin + href
    return base.rsplit("/", 1)[0] + "/" + href


def clean(text: str) -> str:
    text = TAG_RE.sub("", unescape(text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return TRAIL_DATE_RE.sub("", text).strip()


def parse_list(html: str, page_url: str) -> list[dict]:
    items = []
    seen = set()

    def add(href: str, inner: str, extra: str = "") -> None:
        if "page.htm" not in href and "page.psp" not in href:
            return
        title = clean(inner)
        if len(title) < 6:
            return
        url = abs_url(page_url, href)
        if url in seen:
            return
        seen.add(url)
        blob = f"{inner} {extra}"
        dm = DATE_RE.search(blob) or DATE_RE.search(title)
        items.append({"title": title, "url": url, "publishedAt": dm.group(1) if dm else None})

    for m in ITEM_RE.finditer(html):
        add(m.group(1), m.group(2), m.group(3))
    if len(items) < 3:
        for m in FALLBACK_RE.finditer(html):
            add(m.group(1), m.group(2), html[m.end() : m.end() + 240])
    return items


def hit(title: str, words: list[str]) -> bool:
    return any(w in title for w in words)


def priority_of(title: str, source: dict, cfg: dict) -> str:
    if source.get("priorityDefault") == "high" and hit(title, cfg["keywordsRecruitment"]):
        return "high"
    if hit(title, cfg["keywordsHigh"]):
        return "high"
    if hit(title, cfg["keywordsMid"]):
        return "mid"
    return source.get("priorityDefault", "low")


def job_id(url: str) -> str:
    m = re.search(r"(c\d+a\d+)", url)
    return m.group(1) if m else re.sub(r"\W+", "-", url)[-40:]


def main() -> None:
    cfg = load_json(ROOT / "sources.json", {})
    prev = load_json(ROOT / "data" / "jobs.json", {"jobs": []})
    old = {j["id"]: j for j in prev.get("jobs", [])}
    merged = {k: {**v, "isNew": False} for k, v in old.items()}
    new_high = []
    pages_ok = 0

    for source in cfg.get("sources", []):
        if source.get("loginRequired"):
            continue
        urls = [source["home"]]
        home = source["home"]
        if home.endswith("list.htm"):
            urls.append(home.replace("list.htm", "list2.htm"))
        collected = []
        for u in urls:
            try:
                html = fetch(u)
                collected.extend(parse_list(html, u))
                pages_ok += 1
            except Exception as exc:
                print(f"WARN {u}: {exc}")
        for it in collected:
            title = it["title"]
            is_rec = source["kind"] == "jobs" or hit(title, cfg["keywordsRecruitment"])
            if source["kind"] == "notice" and not is_rec:
                continue
            jid = f"{source['id']}-{job_id(it['url'])}"
            old_row = old.get(jid, {})
            pri = priority_of(title, source, cfg)
            is_new = jid not in old
            row = {
                **old_row,
                "id": jid,
                "title": title,
                "source": source["id"],
                "sourceLabel": source["label"],
                "url": it["url"],
                "publishedAt": it["publishedAt"] or old_row.get("publishedAt"),
                "priority": pri,
                "isRecruitment": True,
                "isNew": is_new,
            }
            merged[jid] = row
            if is_new and pri == "high":
                new_high.append(row)

    jobs = sorted(
        merged.values(),
        key=lambda j: (j.get("publishedAt") or "", j["id"]),
        reverse=True,
    )[:300]
    out = {
        "updatedAt": datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "pagesFetched": pages_ok,
        "newHighCount": len(new_high),
        "jobs": jobs,
    }
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "jobs.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    alert = ROOT / "data" / "alerts.md"
    if new_high:
        lines = ["# 新的高优先级招聘\n"]
        for j in new_high:
            lines.append(
                f"- **{j['title']}** · {j['sourceLabel']} · {j.get('publishedAt') or ''} · {j['url']}"
            )
        alert.write_text("\n".join(lines) + "\n", encoding="utf-8")
    elif alert.exists():
        alert.unlink()
    print(f"jobs={len(jobs)} new_high={len(new_high)} pages={pages_ok}")


if __name__ == "__main__":
    main()

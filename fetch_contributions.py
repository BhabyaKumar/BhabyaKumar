from __future__ import annotations

import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent
USERNAME = os.environ.get("GITHUB_USER", "BhabyaKumar")
OUTPUT = ROOT / "data" / "contributions.json"
URL = f"https://github.com/users/{USERNAME}/contributions"


def contribution_count(node) -> int:
    for attr in ("data-count", "data-contribution-count"):
        value = node.get(attr)
        if value and value.isdigit():
            return int(value)

    text = " ".join(
        part
        for part in (
            node.get("aria-label", ""),
            node.get("title", ""),
            node.get_text(" ", strip=True),
        )
        if part
    )
    match = re.search(r"(\d[\d,]*)\s+contributions?", text, re.IGNORECASE)
    return int(match.group(1).replace(",", "")) if match else 0


def main() -> None:
    response = requests.get(
        URL,
        headers={"User-Agent": f"{USERNAME}-profile-readme", "Accept": "text/html"},
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    days = []
    seen = set()
    for node in soup.select("[data-date][data-level]"):
        day = node.get("data-date", "")
        if not day or day in seen:
            continue
        seen.add(day)
        try:
            level = max(0, min(4, int(node.get("data-level", "0"))))
        except ValueError:
            level = 0
        days.append({"date": day, "count": contribution_count(node), "level": level})

    if not days:
        raise RuntimeError(
            "GitHub returned no contribution cells. The page format may have changed."
        )

    days.sort(key=lambda item: item["date"])
    payload = {
        "username": USERNAME,
        "total_contributions": sum(item["count"] for item in days),
        "days": days,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(days)} days and {payload['total_contributions']} contributions.")


if __name__ == "__main__":
    main()

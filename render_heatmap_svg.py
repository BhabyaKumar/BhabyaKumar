from __future__ import annotations

import json
from datetime import date, timedelta
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "contrib-heatmap.svg"
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
CELL = 11
GAP = 3
STEP = CELL + GAP
GRID_X = 58
GRID_Y = 39
WIDTH = 860
HEIGHT = 157


def sunday_on_or_before(value: date) -> date:
    return value - timedelta(days=(value.weekday() + 1) % 7)


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    days = payload.get("days", [])
    by_date = {date.fromisoformat(item["date"]): item for item in days}

    today = max(by_date, default=date.today())
    first = sunday_on_or_before(today - timedelta(days=370))
    weeks = 53
    month_labels = []
    last_month = None
    cells = []

    for week in range(weeks):
        for weekday in range(7):
            current = first + timedelta(days=week * 7 + weekday)
            item = by_date.get(current, {})
            try:
                level = max(0, min(4, int(item.get("level", 0))))
            except (TypeError, ValueError):
                level = 0
            try:
                count = max(0, int(item.get("count", 0)))
            except (TypeError, ValueError):
                count = 0
            if current.day <= 7 and current.month != last_month:
                month_labels.append(
                    f'<text class="month" x="{GRID_X + week * STEP}" y="25">{current.strftime("%b")}</text>'
                )
                last_month = current.month
            delay = (week * 0.006) + (weekday * 0.026)
            label = (
                f"{count} contribution{'s' if count != 1 else ''} on "
                f"{current.strftime('%B')} {current.day}, {current.year}"
            )
            cells.append(
                f'<rect class="cell" x="{GRID_X + week * STEP}" y="{GRID_Y + weekday * STEP}" '
                f'width="{CELL}" height="{CELL}" rx="3" fill="{PALETTE[level]}" '
                f'style="animation-delay:{delay:.3f}s"><title>{escape(label)}</title></rect>'
            )

    total = payload.get("total_contributions")
    footer = (
        f"{total:,} contributions in the last year"
        if isinstance(total, int)
        else "Live contribution data refreshes daily"
    )
    legend_x = 615
    legend = []
    for level, color in enumerate(PALETTE):
        legend.append(
            f'<rect x="{legend_x + level * STEP}" y="137" width="{CELL}" height="{CELL}" rx="3" fill="{color}"/>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Animated contribution heatmap</title>
  <desc id="desc">{escape(footer)} for {escape(payload.get("username", "this profile"))}.</desc>
  <style>
    .month, .day, .footer {{ fill: #8b949e; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .month {{ font-size: 10px; }}
    .day {{ font-size: 9px; }}
    .footer {{ font-size: 11px; }}
    .cell {{ opacity: 0; transform: translateY(-4px); animation: reveal .45s ease-out forwards; }}
    @keyframes reveal {{ to {{ opacity: 1; transform: translateY(0); }} }}
    @media (prefers-reduced-motion: reduce) {{ .cell {{ animation: none; opacity: 1; transform: none; }} }}
  </style>
  {''.join(month_labels)}
  <text class="day" x="12" y="{GRID_Y + STEP * 2 + 8}">Mon</text>
  <text class="day" x="12" y="{GRID_Y + STEP * 4 + 8}">Wed</text>
  <text class="day" x="12" y="{GRID_Y + STEP * 6 + 8}">Fri</text>
  {''.join(cells)}
  <text class="footer" x="58" y="147">{escape(footer)}</text>
  <text class="footer" x="{legend_x - 38}" y="147">Less</text>
  {''.join(legend)}
  <text class="footer" x="{legend_x + 5 * STEP + 1}" y="147">More</text>
</svg>
'''
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Rendered {OUTPUT.name}.")


if __name__ == "__main__":
    main()

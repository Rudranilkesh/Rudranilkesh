"""Render the SVG profile cards, optionally refreshing GitHub's public calendar."""

import argparse
import base64
import calendar
from collections import Counter
from datetime import date, timedelta
from html import escape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data" / "contributions.json"
STATIC = os.environ.get("STATIC") == "1"
DAY = timedelta(days=1)
WIDTH = 840
PAPER = "#fffdf6"
INK = "#141a32"
MUTED = "#47516d"
BLUE = "#233db6"
LEVELS = ("#e9ecfa", "#c3cef9", "#8da0f0", "#526de0", BLUE)


class ContributionCalendar(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}
        self.tooltips = {}
        self.tooltip_id = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and {"id", "data-date", "data-level"} <= attrs.keys():
            self.days[attrs["id"]] = (attrs["data-date"], int(attrs["data-level"]))
        if tag == "tool-tip" and "for" in attrs:
            self.tooltip_id = attrs["for"]
            self.tooltips[self.tooltip_id] = ""

    def handle_data(self, value):
        if self.tooltip_id is not None:
            self.tooltips[self.tooltip_id] += value

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.tooltip_id = None

    def counts(self):
        counts = {}
        for cell_id, (day, level) in self.days.items():
            match = re.match(r"\s*(No|[\d,]+) contributions?\b", self.tooltips.get(cell_id, ""))
            if not match:
                raise ValueError(f"Missing contribution count for {day}")
            value = match[1]
            counts[day] = (0 if value == "No" else int(value.replace(",", "")), level)
        return counts


def read_calendar(html):
    parser = ContributionCalendar()
    parser.feed(html)
    counts = parser.counts()
    if len(counts) < 365:
        raise ValueError(f"Expected at least 365 days, got {len(counts)}")
    end = date.fromisoformat(max(counts))
    dates = [end - i * DAY for i in range(364, -1, -1)]
    return {"days": [{"date": day.isoformat(), "count": counts[day.isoformat()][0],
                      "level": counts[day.isoformat()][1]} for day in dates]}


def refresh_calendar(username):
    url = f"https://github.com/users/{quote(username, safe='')}/contributions"
    request = Request(url, headers={"Accept-Language": "en-US", "User-Agent": "profile-card-renderer"})
    with urlopen(request, timeout=30) as response:
        return read_calendar(response.read().decode("utf-8"))


def text(x, y, value, size=20, color=INK, bold=False, anchor="start"):
    weight = ' font-weight="700"' if bold else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}"{weight}>{escape(str(value))}</text>')


def rect(x, y, w, h, color, radius=0, extra=""):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
            f'fill="{color}" {extra}/>')


def arrow(x, y, color=BLUE):
    return (f'<path d="M{x} {y + 17}l17 -17m-12 0h12v12" fill="none" '
            f'stroke="{color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')


def embed(file):
    return base64.b64encode(file.read_bytes()).decode("ascii")


def fonts(body):
    nodes = ElementTree.fromstring(f'<g xmlns:xlink="http://www.w3.org/1999/xlink">{body}</g>')
    css = []
    with TemporaryDirectory() as temp:
        for weight, name in ((400, "Regular"), (700, "Bold")):
            chars = {ch for node in nodes.iter("text")
                     if node.get("font-weight", "400") == str(weight) for ch in node.text or ""}
            if not chars:
                continue
            target = Path(temp) / f"{name}.woff"
            unicodes = ",".join(f"U+{ord(ch):04X}" for ch in sorted(chars))
            # This is the module entry point for pyftsubset on every platform.
            subprocess.run([sys.executable, "-m", "fontTools.subset", str(ASSETS / f"Tinos-{name}.ttf"),
                            f"--unicodes={unicodes}", "--drop-tables+=Debg", "--flavor=woff",
                            f"--output-file={target}"], check=True)
            css.append(f'@font-face{{font-family:Card;src:url(data:font/woff;base64,{embed(target)}) '
                       f'format("woff");font-weight:{weight};font-display:swap}}')
    return "\n".join(css)


def card(title, body, height, delay, width=WIDTH):
    motion = ""
    flash = ""
    if not STATIC:
        motion = f"""
          .panel-content {{ animation: entrance .55s cubic-bezier(.18,.75,.25,1) {delay:.2f}s both; }}
          .bars {{ transform-box:fill-box; transform-origin:center bottom;
                   animation: rise .66s ease-out {delay + .16:.2f}s both; }}
          @keyframes entrance {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
          @keyframes rise {{ from {{ transform:scaleY(.03); }} to {{ transform:scaleY(1); }} }}
          @media (prefers-reduced-motion: reduce) {{
            .panel-content,.bars {{ animation:none; }}
            .flash {{ display:none; }}
          }}"""
        flash = (f'<g class="flash" opacity="0"><path d="M18 10H{width - 22}" stroke="#738bff" stroke-width="3"/>'
                 f'<animate attributeName="opacity" values="0;.8;0" begin="{delay:.2f}s" dur=".62s" fill="remove"/></g>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
  <title>{escape(title)}</title>
  <style>
    {fonts(body)}
    text {{ font-family:Card,"Times New Roman",serif; }}{motion}
  </style>
  <defs>
    <pattern id="dots" width="8" height="8" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.15" fill="{BLUE}"/></pattern>
  </defs>
  {rect(5, 5, width - 7, height - 7, INK, 15)}
  {rect(2, 2, width - 8, height - 8, PAPER, 14, f'stroke="{INK}" stroke-width="2"')}
  <g class="panel-content">{body}</g>
  {flash}
</svg>
'''


def hero(portrait):
    art = (f'<path d="M608 233 687 8h139v225Z" fill="{BLUE}"/>'
           '<path d="M596 224 668 19m-54 205 72-205m-42 205 69-205" stroke="#536be0" stroke-width="2"/>'
           '<path d="M675 35h139v156H626Z" fill="url(#dots)" opacity=".45"/>')
    if portrait.is_file():
        art += (f'<defs><clipPath id="portrait"><circle cx="719" cy="122" r="75"/></clipPath></defs>'
                f'<circle cx="719" cy="122" r="82" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>'
                f'<image x="644" y="47" width="150" height="150" clip-path="url(#portrait)" '
                f'xlink:href="data:image/jpeg;base64,{embed(portrait)}"/>')
    else:
        art += text(725, 150, "RK", 80, PAPER, True, "middle")
    art += ('<path d="M630 42l4 10 10 4-10 4-4 10-4-10-10-4 10-4Z" fill="#233db6"/>'
            '<path d="M787 174l5 13 13 5-13 5-5 13-5-13-13-5 13-5Z" fill="#fffdf6"/>')
    body = art + text(37, 63, "@Rudranilkesh", 22, BLUE, True)
    body += text(34, 135, "RudraniL Kesh", 72, INK, True)
    body += text(39, 173, "BCA student building full-stack apps, APIs and backend systems.", 21, MUTED)
    body += '<path d="M39 195h104l13 7h82" fill="none" stroke="#233db6" stroke-width="3"/>'
    return card("RudraniL Kesh", body, 246, .03)


def tile(title, detail, symbol, delay):
    body = rect(15, 20, 46, 48, BLUE, 8)
    body += text(38, 51, symbol, 22, PAPER, True, "middle")
    body += text(73, 41, title, 24, INK, True) + text(73, 64, detail, 16, MUTED)
    body += arrow(224, 33)
    return card(title, body, 92, delay, 273)


def repo(title, description, tools, delay):
    body = rect(22, 21, 66, 77, "#e9ecfa", 10)
    body += '<path d="M44 43h20v30H44zm5 7h10m-10 6h10m-10 6h6" fill="none" stroke="#233db6" stroke-width="2"/>'
    body += text(107, 44, title, 27, INK, True)
    body += text(108, 70, description, 19, MUTED) + text(108, 94, tools, 16, BLUE, True)
    body += arrow(782, 33)
    return card(title, body, 122, delay)


def monthly(days):
    months = Counter()
    for day, count, _ in days:
        months[(day.year, day.month)] += count
    active = sum(count > 0 for _, count, _ in days)
    busiest, peak, _ = max(days, key=lambda row: row[1])
    streak = 0
    # A zero-count day still in progress does not break yesterday's streak.
    trailing = days if days[-1][1] else days[:-1]
    for _, count, _ in reversed(trailing):
        if not count:
            break
        streak += 1

    body = text(28, 44, "Monthly contributions", 33, INK, True)
    body += text(810, 43, "LAST 365 DAYS", 15, BLUE, True, "end")
    peak_label = f"{busiest:%b} {busiest.day} · {peak}" if peak else "—"
    streak_label = f"{streak} {'day' if streak == 1 else 'days'}"
    for x, value, label in ((28, streak_label, "Current streak"), (293, active, "Active days"),
                            (558, peak_label, "Busiest day")):
        body += rect(x, 61, 253, 58, "#edf0fd", 8)
        body += text(x + 13, 88, value, 24, BLUE, True) + text(x + 13, 107, label, 15, MUTED)
    baseline = 263
    body += f'<path d="M28 {baseline}h783" stroke="#adb8df"/>'
    step = 783 / len(months)
    maximum = max(1, *months.values())
    bars = labels = ""
    for i, ((_, month), count) in enumerate(months.items()):
        x = round(28 + step * (i + .5), 1)
        h = max(2, round(109 * count / maximum))
        bars += rect(x - 15, baseline - h, 30, h, BLUE if count == maximum else "#a4b2f5", 4)
        labels += text(x, baseline - h - 7, count, 15, INK, True, "middle")
        labels += text(x, 285, calendar.month_abbr[month], 14, MUTED, False, "middle")
    return card("Monthly GitHub contributions, streak, active days and busiest day",
                body + f'<g class="bars">{bars}</g>' + labels, 308, .62)


def heatmap(days):
    first = days[0][0]
    start = first - ((first.weekday() + 1) % 7) * DAY
    end = days[-1][0]
    body = text(27, 43, "Contribution calendar", 33, INK, True)
    body += text(810, 42, f"{sum(count for _, count, _ in days):,} CONTRIBUTIONS", 16, BLUE, True, "end")
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        body += text(28, 91 + row * 14, label, 13, MUTED)
    last_month_column = -4
    for day, _, level in days:
        column, row = divmod((day - start).days, 7)
        x = 66 + column * 14
        body += rect(x, 80 + row * 14, 11, 11, LEVELS[level], 2)
        if (day.day == 1 or (day == first and day.day <= 7)) and column - last_month_column >= 3 and column <= 51:
            body += text(x, 71, day.strftime("%b"), 14, MUTED)
            last_month_column = column
    body += text(28, 204, f"{first:%d %b %Y} – {end:%d %b %Y}", 15, MUTED)
    body += text(680, 204, "Less", 14, MUTED) + text(813, 204, "More", 14, MUTED, False, "end")
    for i, color in enumerate(LEVELS):
        body += rect(712 + i * 14, 193, 11, 11, color, 2)
    return card("GitHub contribution calendar for the last 365 days", body, 226, 1.42)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument("--refresh", metavar="USERNAME", help="Download the public GitHub calendar")
    sources.add_argument("--calendar-html", type=Path, help="Import a saved public GitHub calendar")
    parser.add_argument("--output", type=Path, default=ROOT / "cards")
    parser.add_argument("--portrait", type=Path, default=ASSETS / "portrait.jpg")
    args = parser.parse_args()

    if args.refresh:
        snapshot = refresh_calendar(args.refresh)
    elif args.calendar_html:
        snapshot = read_calendar(args.calendar_html.read_text(encoding="utf-8"))
    else:
        snapshot = json.loads(DATA.read_text(encoding="utf-8"))
    days = [(date.fromisoformat(item["date"]), item["count"], item["level"]) for item in snapshot["days"]]
    if len(days) != 365 or any((day - days[0][0]).days != i or count < 0 or not 0 <= level <= 4
                               for i, (day, count, level) in enumerate(days)):
        raise ValueError("Expected 365 consecutive dates with valid contribution counts and levels")

    cards = {
        "hero": hero(args.portrait),
        "repos": tile("GitHub", "Browse repositories", "<>", .24),
        "linkedin": tile("LinkedIn", "Connect with me", "in", .34),
        "leetcode": tile("LeetCode", "See my practice", "{ }", .44),
        "monthly": monthly(days),
        "url_shortner": repo("URL Shortener", "Create custom short links and track clicks from a dashboard.",
                             "React · Node.js · Express · MongoDB", .87),
        "html-portfolio": repo("HTML Portfolio", "An early collection of web projects and personal pages.",
                               "HTML · GitHub Pages", 1.04),
        "html-resume": repo("HTML Résumé", "A web-based résumé built with HTML.", "HTML", 1.21),
        "contributions": heatmap(days),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    for name, svg in cards.items():
        (args.output / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
    if args.refresh or args.calendar_html:
        DATA.parent.mkdir(exist_ok=True)
        rows = ",\n".join(f"    {json.dumps(row)}" for row in snapshot["days"])
        DATA.write_text(f'{{\n  "days": [\n{rows}\n  ]\n}}\n', encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

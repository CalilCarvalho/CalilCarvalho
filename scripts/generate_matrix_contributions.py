#!/usr/bin/env python3
"""
Matrix Contributions — Profile README generator

V3 (simple/public mode)
- Reads the public GitHub contributions calendar HTML.
- Generates an animated GIF with Matrix rain + the real contribution grid.
- No Personal Access Token required.

Usage:
    python scripts/generate_matrix_contributions.py USERNAME
    python scripts/generate_matrix_contributions.py --demo
"""

from __future__ import annotations

import argparse
import random
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1000
HEIGHT = 340
FRAMES = 99
FRAME_DURATION_MS = 110

PHRASE = "WAKE UP, DEVelop a new world_"
CHARS = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ<>/[]{}#$%&*+-=;:"

MATRIX_FONT_SIZE = 17
TITLE_FONT_SIZE = 25
SMALL_FONT_SIZE = 14

CELL_SIZE = 11
CELL_GAP = 4
GRID_TOP = 88

OUTPUT = Path("assets/matrix-contributions.gif")

BG = (0, 0, 0)
LEVEL_COLORS = {
    0: (5, 20, 10),
    1: (0, 72, 34),
    2: (0, 116, 50),
    3: (0, 178, 72),
    4: (88, 255, 145),
}


def load_font(size: int):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
        "DejaVuSansMono.ttf",
        "DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()


def sunday_index(d: date) -> int:
    # Python: Monday=0 ... Sunday=6. Desired: Sunday=0 ... Saturday=6.
    return (d.weekday() + 1) % 7


def build_grid(days: list[dict]) -> list[dict]:
    if not days:
        raise RuntimeError("Nenhum dia de contribuição encontrado.")

    normalized = []
    for item in days:
        d = datetime.strptime(item["date"], "%Y-%m-%d").date()
        normalized.append({"date_obj": d, "date": item["date"], "level": int(item["level"])})

    normalized.sort(key=lambda x: x["date_obj"])
    first = normalized[0]["date_obj"]
    anchor = first - timedelta(days=sunday_index(first))

    cells = []
    for item in normalized:
        d = item["date_obj"]
        delta = (d - anchor).days
        cells.append(
            {
                "date": item["date"],
                "level": max(0, min(4, item["level"])),
                "row": sunday_index(d),
                "col": delta // 7,
            }
        )

    # Keep the newest 53 columns to fit a classic GitHub-style yearly graph.
    max_col = max(c["col"] for c in cells)
    min_col = max(0, max_col - 52)
    cropped = [c for c in cells if c["col"] >= min_col]
    for c in cropped:
        c["col"] -= min_col
    return cropped


def fetch_contributions(username: str) -> list[dict]:
    url = f"https://github.com/users/{username}/contributions"
    headers = {
        "User-Agent": "github-matrix-profile/1.0",
        "Referer": f"https://github.com/{username}",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "text/html,application/xhtml+xml",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    selectors = [
        ".js-calendar-graph-table .ContributionCalendar-day[data-date][data-level]",
        ".ContributionCalendar-day[data-date][data-level]",
        "[data-date][data-level]",
    ]

    nodes = []
    for selector in selectors:
        nodes = soup.select(selector)
        if nodes:
            break

    if not nodes:
        raise RuntimeError(
            "Não consegui localizar os dias do calendário público do GitHub. "
            "A estrutura do HTML pode ter mudado."
        )

    by_date = {}
    for node in nodes:
        day = node.get("data-date")
        level = node.get("data-level")
        if not day or level is None:
            continue
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            continue
        try:
            level_int = int(level)
        except ValueError:
            continue
        by_date[day] = {"date": day, "level": level_int}

    if not by_date:
        raise RuntimeError("O calendário foi localizado, mas os dados não puderam ser lidos.")

    return [by_date[k] for k in sorted(by_date)]


def demo_contributions() -> list[dict]:
    """Synthetic demo used only for the GIF shipped in the package."""
    end = date.today()
    start = end - timedelta(days=370)
    rng = random.Random(1337)
    days = []
    d = start
    while d <= end:
        # Sparse-ish developer activity, with occasional bursts.
        roll = rng.random()
        if roll < 0.46:
            level = 0
        elif roll < 0.70:
            level = 1
        elif roll < 0.84:
            level = 2
        elif roll < 0.94:
            level = 3
        else:
            level = 4
        days.append({"date": d.isoformat(), "level": level})
        d += timedelta(days=1)
    return days


def brighten(color: tuple[int, int, int], amount: int):
    return tuple(min(255, c + amount) for c in color)


def draw_rain(draw, drops, speeds, font, frame_idx):
    for i in range(len(drops)):
        x = i * MATRIX_FONT_SIZE
        drops[i] += speeds[i]
        head_y = int(drops[i] * MATRIX_FONT_SIZE)

        for trail in range(13):
            y = head_y - trail * MATRIX_FONT_SIZE
            if not (0 <= y < HEIGHT):
                continue

            ch = random.choice(CHARS)
            if trail == 0:
                fill = (205, 255, 215)
            elif trail <= 2:
                fill = (80, 255, 125)
            elif trail <= 5:
                fill = (0, 165, 70)
            else:
                fade = max(25, 105 - trail * 8)
                fill = (0, fade, max(15, fade // 2))

            draw.text((x, y), ch, font=font, fill=fill)

        if head_y > HEIGHT + random.randint(50, 240):
            drops[i] = random.uniform(-24, -2)
            speeds[i] = random.choice([0.55, 0.7, 0.85, 1.0, 1.15, 1.3])


def draw_grid(draw, cells, origin_x, origin_y, frame_idx):
    for cell in cells:
        x1 = origin_x + cell["col"] * (CELL_SIZE + CELL_GAP)
        y1 = origin_y + cell["row"] * (CELL_SIZE + CELL_GAP)
        x2 = x1 + CELL_SIZE
        y2 = y1 + CELL_SIZE

        level = cell["level"]
        base = LEVEL_COLORS[level]

        # Scanner wave travels through the contribution calendar.
        scanner_col = frame_idx % 53
        glow = 0
        if level > 0 and abs(cell["col"] - scanner_col) <= 1:
            glow = 45
        elif level > 0 and (frame_idx + cell["col"] * 2 + cell["row"]) % 19 == 0:
            glow = 20

        fill = brighten(base, glow)
        outline = (0, 50, 25) if level == 0 else (0, 105, 48)

        draw.rounded_rectangle(
            [x1, y1, x2, y2],
            radius=2,
            fill=fill,
            outline=outline,
            width=1,
        )


def text_center(draw, text, y, font, fill):
    box = draw.textbbox((0, 0), text, font=font)
    w = box[2] - box[0]
    draw.text(((WIDTH - w) // 2, y), text, font=font, fill=fill)


def generate(username: str, display_name: str, cells: list[dict], output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)

    matrix_font = load_font(MATRIX_FONT_SIZE)
    title_font = load_font(TITLE_FONT_SIZE)
    small_font = load_font(SMALL_FONT_SIZE)

    cols = max(c["col"] for c in cells) + 1
    grid_width = cols * CELL_SIZE + max(0, cols - 1) * CELL_GAP
    grid_height = 7 * CELL_SIZE + 6 * CELL_GAP

    origin_x = (WIDTH - grid_width) // 2
    origin_y = GRID_TOP

    rng = random.Random(2026)
    matrix_columns = WIDTH // MATRIX_FONT_SIZE + 2
    drops = [rng.uniform(-24, 5) for _ in range(matrix_columns)]
    speeds = [rng.choice([0.55, 0.7, 0.85, 1.0, 1.15, 1.3]) for _ in range(matrix_columns)]

    frames = []

    for frame_idx in range(FRAMES):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)

        draw_rain(draw, drops, speeds, matrix_font, frame_idx)

        # Dark glass panel makes the real graph readable over the rain.
        pad_x = 20
        pad_y = 18
        panel = [
            origin_x - pad_x,
            origin_y - pad_y,
            origin_x + grid_width + pad_x,
            origin_y + grid_height + pad_y,
        ]
        draw.rounded_rectangle(
            panel,
            radius=12,
            fill=(0, 4, 1),
            outline=(0, 70, 30),
            width=1,
        )

        draw_grid(draw, cells, origin_x, origin_y, frame_idx)

        # Header
        header = display_name
        text_center(draw, header, 28, small_font, (75, 235, 110))

        # Phrase: steady glow with a subtle terminal cursor pulse.
        cursor = "█" if (frame_idx // 4) % 2 == 0 else " "
        phrase = PHRASE + cursor
        glow = 15 + int(15 * (1 + math_sin(frame_idx / 5.0)))
        phrase_color = (min(255, 105 + glow), 255, min(255, 145 + glow))
        text_center(draw, phrase, HEIGHT - 56, title_font, phrase_color)

        frames.append(img)

    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=2,
        optimize=True,
    )


def math_sin(x: float) -> float:
    # Local import keeps the top of the script simple.
    import math
    return math.sin(x)


def main():
    parser = argparse.ArgumentParser(description="Generate Matrix-style GitHub contribution GIF.")
    parser.add_argument("username", nargs="?", help="GitHub username")
    parser.add_argument("--demo", action="store_true", help="Generate a synthetic demo without network access")
    parser.add_argument("--display-name", default="@CalilCarvalho", help="Text shown above the contribution grid")
    parser.add_argument("--output", default=str(OUTPUT), help="Output GIF path")
    args = parser.parse_args()

    if args.demo:
        username = "demo"
        days = demo_contributions()
    else:
        if not args.username:
            parser.error("Informe o username do GitHub ou use --demo.")
        username = args.username.strip()
        days = fetch_contributions(username)

    cells = build_grid(days)
    generate(username, args.display_name, cells, Path(args.output))
    print(f"OK: {args.output}")


if __name__ == "__main__":
    main()

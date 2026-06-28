#!/usr/bin/env python3
"""Generate dashboard bitmap icons and the docs asset gallery.

The runtime icon loader expects black shapes on a white background. It inverts
icons before drawing them as 1-bit bitmaps on the e-paper canvas.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "icons"
DOCS_DIR = ROOT / "docs"
FONT_DIR = ROOT / "fnt"
SCALE = 4
ICON_SIZE = 40
CANVAS = ICON_SIZE * SCALE
BLACK = 0
WHITE = 255


def s(value: float) -> int:
    return int(round(value * SCALE))


def draw_scaled(draw_fn: Callable[[ImageDraw.ImageDraw], None]) -> Image.Image:
    image = Image.new("L", (CANVAS, CANVAS), WHITE)
    draw = ImageDraw.Draw(image)
    draw_fn(draw)
    return image.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS).convert("RGB")


def line(draw: ImageDraw.ImageDraw, points, width=2, fill=BLACK):
    draw.line([(s(x), s(y)) for x, y in points], fill=fill, width=s(width), joint="curve")


def rect(draw: ImageDraw.ImageDraw, box, outline=BLACK, fill=None, width=2):
    draw.rectangle(tuple(s(v) for v in box), outline=outline, fill=fill, width=s(width))


def rounded_rect(draw: ImageDraw.ImageDraw, box, radius=4, outline=BLACK, fill=None, width=2):
    draw.rounded_rectangle(tuple(s(v) for v in box), radius=s(radius), outline=outline, fill=fill, width=s(width))


def ellipse(draw: ImageDraw.ImageDraw, box, outline=BLACK, fill=None, width=2):
    draw.ellipse(tuple(s(v) for v in box), outline=outline, fill=fill, width=s(width))


def polygon(draw: ImageDraw.ImageDraw, points, fill=BLACK, outline=None):
    draw.polygon([(s(x), s(y)) for x, y in points], fill=fill, outline=outline)


def arc(draw: ImageDraw.ImageDraw, box, start, end, width=2):
    draw.arc(tuple(s(v) for v in box), start=start, end=end, fill=BLACK, width=s(width))


def icon_alert(draw):
    line(draw, [(20, 5), (36, 34), (4, 34), (20, 5)], width=2)
    line(draw, [(20, 14), (20, 24)], width=3)
    ellipse(draw, (18.5, 28, 21.5, 31), fill=BLACK, width=1)


def icon_calendar(draw):
    rounded_rect(draw, (6, 8, 34, 34), radius=3, outline=BLACK, width=2)
    line(draw, [(6, 15), (34, 15)], width=2)
    line(draw, [(13, 5), (13, 11)], width=3)
    line(draw, [(27, 5), (27, 11)], width=3)
    for x in (12, 20, 28):
        for y in (21, 28):
            rect(draw, (x - 1, y - 1, x + 1, y + 1), fill=BLACK, width=1)


def icon_package(draw):
    line(draw, [(7, 13), (20, 6), (33, 13), (20, 20), (7, 13)], width=2)
    line(draw, [(7, 13), (20, 20), (20, 35), (7, 27), (7, 13)], width=2)
    line(draw, [(33, 13), (20, 20), (20, 35), (33, 27), (33, 13)], width=2)
    line(draw, [(14, 9.5), (27, 16.5)], width=2)


def icon_battery(draw):
    rounded_rect(draw, (5, 13, 32, 28), radius=2, outline=BLACK, width=2)
    rect(draw, (33, 17, 36, 24), fill=BLACK, width=1)
    rect(draw, (9, 17, 15, 24), fill=BLACK, width=1)
    rect(draw, (17, 17, 23, 24), fill=BLACK, width=1)
    line(draw, [(26, 17), (26, 24)], width=2)


def icon_server(draw):
    rounded_rect(draw, (7, 7, 33, 17), radius=2, outline=BLACK, width=2)
    rounded_rect(draw, (7, 22, 33, 32), radius=2, outline=BLACK, width=2)
    ellipse(draw, (11, 10, 14, 13), fill=BLACK, width=1)
    ellipse(draw, (11, 25, 14, 28), fill=BLACK, width=1)
    line(draw, [(18, 12), (29, 12)], width=2)
    line(draw, [(18, 27), (29, 27)], width=2)


def icon_database(draw):
    ellipse(draw, (8, 5, 32, 15), outline=BLACK, width=2)
    line(draw, [(8, 10), (8, 29)], width=2)
    line(draw, [(32, 10), (32, 29)], width=2)
    arc(draw, (8, 20, 32, 34), 0, 180, width=2)
    arc(draw, (8, 13, 32, 27), 0, 180, width=2)


def icon_shield(draw):
    line(draw, [(20, 4), (34, 10), (31, 25), (20, 36), (9, 25), (6, 10), (20, 4)], width=2)
    line(draw, [(20, 10), (20, 29)], width=2)
    line(draw, [(14, 20), (19, 25), (27, 15)], width=2)


def icon_deploy(draw):
    rounded_rect(draw, (7, 24, 33, 33), radius=2, outline=BLACK, width=2)
    line(draw, [(20, 7), (20, 23)], width=3)
    polygon(draw, [(20, 5), (12, 14), (17, 14), (17, 23), (23, 23), (23, 14), (28, 14)], fill=BLACK)
    ellipse(draw, (10, 27, 13, 30), fill=BLACK, width=1)
    line(draw, [(17, 29), (29, 29)], width=2)


def icon_backup(draw):
    arc(draw, (7, 8, 33, 34), 35, 335, width=3)
    polygon(draw, [(8, 20), (5, 31), (16, 28)], fill=BLACK)
    line(draw, [(20, 13), (20, 21), (26, 24)], width=2)


def icon_checklist(draw):
    rounded_rect(draw, (8, 5, 34, 35), radius=3, outline=BLACK, width=2)
    line(draw, [(14, 14), (16, 16), (20, 11)], width=2)
    line(draw, [(23, 14), (30, 14)], width=2)
    line(draw, [(14, 24), (16, 26), (20, 21)], width=2)
    line(draw, [(23, 24), (30, 24)], width=2)
    line(draw, [(15, 5), (15, 2), (27, 2), (27, 5)], width=2)


def icon_home(draw):
    line(draw, [(5, 20), (20, 7), (35, 20)], width=2)
    rounded_rect(draw, (10, 18, 30, 34), radius=2, outline=BLACK, width=2)
    rect(draw, (17, 24, 23, 34), outline=BLACK, width=2)


def icon_timer(draw):
    ellipse(draw, (8, 9, 32, 35), outline=BLACK, width=2)
    line(draw, [(17, 5), (23, 5)], width=3)
    line(draw, [(20, 5), (20, 9)], width=2)
    line(draw, [(20, 22), (20, 14)], width=2)
    line(draw, [(20, 22), (26, 26)], width=2)
    line(draw, [(29, 9), (32, 6)], width=2)


def icon_lightning(draw):
    polygon(draw, [(23, 3), (10, 23), (18, 23), (15, 37), (30, 17), (21, 17)], fill=BLACK)


NEW_ICONS = {
    "icon_alert": icon_alert,
    "icon_calendar": icon_calendar,
    "icon_package": icon_package,
    "icon_battery": icon_battery,
    "icon_server": icon_server,
    "icon_database": icon_database,
    "icon_shield": icon_shield,
    "icon_deploy": icon_deploy,
    "icon_backup": icon_backup,
    "icon_checklist": icon_checklist,
    "icon_home": icon_home,
    "icon_timer": icon_timer,
    "icon_lightning": icon_lightning,
}

NEW_PURPOSES = {
    "icon_alert": "incidents / alerts",
    "icon_calendar": "calendar / schedule",
    "icon_package": "deliveries / inventory",
    "icon_battery": "battery / power",
    "icon_server": "server / homelab",
    "icon_database": "database / storage",
    "icon_shield": "security / status",
    "icon_deploy": "deploy / release",
    "icon_backup": "backup / sync",
    "icon_checklist": "tasks / chores",
    "icon_home": "home overview",
    "icon_timer": "focus / timer",
    "icon_lightning": "storm weather fallback",
}


def write_icons() -> None:
    ICON_DIR.mkdir(exist_ok=True)
    for name, fn in NEW_ICONS.items():
        draw_scaled(fn).save(ICON_DIR / f"{name}.bmp")


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(FONT_DIR / name), size)
    except OSError:
        return ImageFont.load_default()


def render_gallery() -> None:
    DOCS_DIR.mkdir(exist_ok=True)
    icon_paths = sorted(ICON_DIR.glob("icon_*.bmp"))
    cols = 6
    cell_w = 176
    cell_h = 92
    margin = 32
    title_h = 92
    font_h = 250
    rows = (len(icon_paths) + cols - 1) // cols
    width = margin * 2 + cols * cell_w
    height = margin * 2 + title_h + rows * cell_h + font_h

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    title_font = load_font("Aldrich-Regular.ttc", 34)
    label_font = load_font("Aldrich-Regular.ttc", 15)
    small_font = load_font("Aldrich-Regular.ttc", 13)
    body_font = load_font("Aldrich-Regular.ttc", 22)
    led_font = load_font("advanced_led_board-7.ttc", 54)
    fallback_font = load_font("Font.ttc", 28)

    draw.text((margin, margin), "Icon And Font Gallery", font=title_font, fill=BLACK)
    draw.text((margin, margin + 44), "40px monochrome source icons, rendered for high-contrast e-paper use", font=body_font, fill=BLACK)
    draw.line((margin, margin + title_h - 18, width - margin, margin + title_h - 18), fill=BLACK, width=2)

    y0 = margin + title_h
    for idx, path in enumerate(icon_paths):
        col = idx % cols
        row = idx // cols
        x = margin + col * cell_w
        y = y0 + row * cell_h
        is_new = path.stem in NEW_ICONS
        draw.rounded_rectangle((x, y, x + cell_w - 14, y + cell_h - 12), radius=6, outline=BLACK, width=2 if is_new else 1)
        if is_new:
            draw.rectangle((x + cell_w - 54, y, x + cell_w - 14, y + 18), fill=BLACK)
            draw.text((x + cell_w - 48, y + 2), "NEW", font=small_font, fill=WHITE)
        icon = Image.open(path).convert("L").resize((40, 40), Image.Resampling.LANCZOS)
        image.paste(icon.convert("RGB"), (x + 12, y + 12))
        label = path.stem.replace("icon_", "")
        if len(label) > 18:
            label = label[:17] + "..."
        draw.text((x + 62, y + 14), label, font=label_font, fill=BLACK)
        purpose = NEW_PURPOSES.get(path.stem, "")
        if purpose:
            draw.text((x + 62, y + 38), purpose[:20], font=small_font, fill=BLACK)

    font_y = y0 + rows * cell_h + 28
    draw.line((margin, font_y - 16, width - margin, font_y - 16), fill=BLACK, width=2)
    draw.text((margin, font_y), "Font Samples", font=title_font, fill=BLACK)
    draw.text((margin, font_y + 52), "Aldrich Regular 20/28/40: DASHBOARD STATUS 42%", font=load_font("Aldrich-Regular.ttc", 28), fill=BLACK)
    draw.text((margin, font_y + 92), "Aldrich 60: 128 ms", font=load_font("Aldrich-Regular.ttc", 60), fill=BLACK)
    draw.text((margin, font_y + 160), "LED clock: 14:32", font=led_font, fill=BLACK)
    draw.text((margin + 520, font_y + 160), "Fallback: 123 ABC xyz", font=fallback_font, fill=BLACK)

    image.save(DOCS_DIR / "icon-font-gallery.png")


def main() -> None:
    write_icons()
    render_gallery()
    print(f"Wrote {len(NEW_ICONS)} icons and docs/icon-font-gallery.png")


if __name__ == "__main__":
    main()
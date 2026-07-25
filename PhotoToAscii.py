"""
photo_to_ascii.py
------------------
Converts a photo into a grid of colors (portrait.txt) that generate_profile.py
uses to draw a pixel-art style portrait inside the terminal SVG.

Usage:
    python photo_to_ascii.py <input_image> [--cols 40] [--rows 46]

Output:
    portrait.txt - one line per row, hex colors comma-separated per column
"""

import sys
import argparse
from PIL import Image, ImageEnhance


def image_to_grid(path: str, cols: int, rows: int, glitch_tint: bool = True):
    img = Image.open(path).convert("RGB")

    # Crop to a portrait-ish aspect ratio (matches the terminal panel shape)
    target_ratio = cols / rows
    w, h = img.size
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    img = img.resize((cols, rows), Image.LANCZOS)

    # Slight contrast/color boost so the pixel art reads well at small size
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Color(img).enhance(1.2)

    rows_out = []
    for y in range(rows):
        row_colors = []
        for x in range(cols):
            r, g, b = img.getpixel((x, y))
            if glitch_tint:
                # Push toward blue/purple/magenta like a CRT/terminal glitch photo
                r = min(255, int(r * 0.85))
                b = min(255, int(b * 1.15 + 20))
            row_colors.append("#%02x%02x%02x" % (r, g, b))
        rows_out.append(",".join(row_colors))
    return rows_out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="Path to source photo (jpg/png)")
    parser.add_argument("--cols", type=int, default=40)
    parser.add_argument("--rows", type=int, default=46)
    parser.add_argument("--out", default="portrait.txt")
    parser.add_argument("--no-tint", action="store_true")
    args = parser.parse_args()

    grid = image_to_grid(args.input, args.cols, args.rows, glitch_tint=not args.no_tint)

    with open(args.out, "w") as f:
        f.write("\n".join(grid))

    print(f"Wrote {args.cols}x{args.rows} pixel grid to {args.out}")


if __name__ == "__main__":
    main()
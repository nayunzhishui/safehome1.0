"""Create labeled contact sheets for visual QA of rendered document pages."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--rows", type=int, default=3)
    args = parser.parse_args()

    pages = sorted(args.input_dir.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
    if not pages:
        raise SystemExit("no page PNGs found")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    per_sheet = args.columns * args.rows
    font = ImageFont.load_default()
    thumb_w, thumb_h = 408, 528
    label_h = 22
    for sheet_index in range(math.ceil(len(pages) / per_sheet)):
        batch = pages[sheet_index * per_sheet : (sheet_index + 1) * per_sheet]
        canvas = Image.new("RGB", (args.columns * thumb_w, args.rows * (thumb_h + label_h)), "#d9dce1")
        draw = ImageDraw.Draw(canvas)
        for index, page_path in enumerate(batch):
            page_number = int(page_path.stem.split("-")[-1])
            with Image.open(page_path) as image:
                image = image.convert("RGB")
                image.thumbnail((thumb_w - 8, thumb_h - 8))
                col, row = index % args.columns, index // args.columns
                x = col * thumb_w + (thumb_w - image.width) // 2
                y = row * (thumb_h + label_h) + label_h
                canvas.paste(image, (x, y))
                draw.text((col * thumb_w + 6, row * (thumb_h + label_h) + 4), f"Page {page_number}", fill="black", font=font)
        output = args.output_dir / f"contact-{sheet_index + 1:02d}.png"
        canvas.save(output, optimize=True)
    print(f"pages={len(pages)} sheets={math.ceil(len(pages) / per_sheet)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Generate resources/icon.ico (run once, needs Pillow).

    python ocr_app/resources/make_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [16, 16, size - 16, size - 16], radius=48, fill=(0, 122, 204, 255)
    )
    try:
        font = ImageFont.truetype("arialbd.ttf", 96)
    except OSError:
        font = ImageFont.load_default()
    draw.text(
        (size / 2, size / 2),
        "OCR",
        font=font,
        fill="white",
        anchor="mm",
    )
    out = Path(__file__).parent / "icon.ico"
    img.save(out, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)])
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

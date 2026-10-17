"""Draw a Receipt to a clean grayscale image, the way a thermal printer would print it."""

from functools import lru_cache
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

from .layout import Align, Receipt, Size

# Thermal printers lay down 8 dots per mm. 80 mm paper has a 72 mm printable width (576 dots);
# 58 mm paper has 48 mm (384 dots). Both print in a fixed-pitch font.
PAPER = {80: {"columns": 42, "print_px": 576}, 58: {"columns": 32, "print_px": 384}}
MARGIN_PX = 24
LINE_GAP = 1.25  # line height as a multiple of the font size

FONT_CANDIDATES = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
    ("/usr/share/fonts/truetype/msttcorefonts/cour.ttf", "/usr/share/fonts/truetype/msttcorefonts/courbd.ttf"),
    ("/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSansMono-Bold.ttf"),
]


def _font_paths(preferred: str | None = None) -> tuple[str, str]:
    for regular, bold in FONT_CANDIDATES:
        if preferred and preferred not in regular:
            continue
        if Path(regular).exists():
            return regular, bold if Path(bold).exists() else regular
    raise FileNotFoundError("no monospace TTF found; install fonts-dejavu or pass --font")


@lru_cache(maxsize=None)
def _font_for_columns(path: str, columns: int, print_px: int) -> ImageFont.FreeTypeFont:
    """Largest size at which `columns` glyphs fit the printable width."""
    size = 8
    while True:
        candidate = ImageFont.truetype(path, size + 1)
        if candidate.getlength("M" * columns) > print_px:
            return ImageFont.truetype(path, size)
        size += 1


def render(receipt: Receipt, paper_mm: int = 80, font_family: str | None = None) -> Image.Image:
    spec = PAPER[paper_mm]
    assert receipt.columns == spec["columns"], "receipt was laid out for a different paper width"
    regular_path, bold_path = _font_paths(font_family)
    fonts = {
        (False, Size.NORMAL): _font_for_columns(regular_path, spec["columns"], spec["print_px"]),
        (True, Size.NORMAL): _font_for_columns(bold_path, spec["columns"], spec["print_px"]),
        (False, Size.DOUBLE): _font_for_columns(regular_path, spec["columns"] // 2, spec["print_px"]),
        (True, Size.DOUBLE): _font_for_columns(bold_path, spec["columns"] // 2, spec["print_px"]),
    }
    base_height = int(fonts[(False, Size.NORMAL)].size * LINE_GAP)
    qr_side = spec["print_px"] // 2

    # First pass: total height.
    height = MARGIN_PX
    for line in receipt.lines:
        height += qr_side + base_height if line.qr_payload is not None else base_height * line.size.value
    height += MARGIN_PX * 2

    width = spec["print_px"] + MARGIN_PX * 2
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)
    y = MARGIN_PX
    for line in receipt.lines:
        if line.qr_payload is not None:
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2)
            qr.add_data(line.qr_payload)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert("L")
            qr_img = qr_img.resize((qr_side, qr_side), Image.NEAREST)
            image.paste(qr_img, ((width - qr_side) // 2, y + base_height // 2))
            y += qr_side + base_height
            continue
        font = fonts[(line.bold, line.size)]
        text_width = font.getlength(line.text)
        if line.align is Align.CENTER:
            x = (width - text_width) / 2
        elif line.align is Align.RIGHT:
            x = width - MARGIN_PX - text_width
        else:
            x = MARGIN_PX
        draw.text((x, y), line.text, font=font, fill=0)
        y += base_height * line.size.value
    return image

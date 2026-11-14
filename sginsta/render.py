"""Draws 1080x1350 (4:5) JPEG cards in the site's look, and crops meetup photos to the same size."""
from PIL import Image, ImageDraw, ImageFont, ImageOps

from . import config as C

try:  # iPhone photos
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

W, H, M = 1080, 1350, 84  # size and side margin


def _font(name, size):
    return ImageFont.truetype(str(C.FONTS / name), size)


def serif(s): return _font("InstrumentSerif-Regular.ttf", s)
def sans(s): return _font("Inter-Regular.otf", s)
def bold(s): return _font("Inter-Bold.otf", s)


def _wrap(d, text, font, width):
    lines = []
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            trial = f"{line} {word}".strip()
            if d.textlength(trial, font=font) <= width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def _fit(d, text, make, sizes, width, max_lines):
    """Largest font size at which text fits in max_lines."""
    for s in sizes:
        f = make(s)
        lines = _wrap(d, text, f, width)
        if len(lines) <= max_lines:
            return f, lines
    return f, lines[:max_lines]


def _spaced(d, xy, text, font, fill, spacing=4):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + spacing


def card(out, *, kicker, headline, body="", top="", bg=C.PAPER, accent=C.TOMATO, footer="", sun=True):
    """kicker: small caps line; top: accent line above the headline (date, tip number)."""
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    if sun:
        d.ellipse((W - 430, -260, W + 230, 400), fill=C.SUN if bg != C.SUN else C.PAPER)
    logo = Image.open(C.LOGO).convert("RGBA").resize((92, 92))
    im.paste(logo, (M, M), logo)
    _spaced(d, (M + 116, M + 30), kicker.upper(), bold(26), C.INK)

    y = 330
    if top:
        _spaced(d, (M, y), top.upper(), bold(36), accent, 3)
        y += 76
    f, lines = _fit(d, headline, serif, range(150, 70, -6), W - 2 * M, 4)
    lh = int(f.size * 0.98)
    for ln in lines:
        d.text((M, y), ln, font=f, fill=C.INK)
        y += lh
    y += int(f.size * 0.3)  # clear the descenders
    if body:
        d.line((M, y, M + 160, y), fill=C.INK, width=3)
        y += 44
        bf, blines = _fit(d, body, sans, range(42, 26, -2), W - 2 * M, max(2, (H - 210 - y) // 56))
        for ln in blines:
            d.text((M, y), ln, font=bf, fill=C.INK)
            y += int(bf.size * 1.42)

    d.rectangle((0, H - 150, W, H), fill=C.INK)
    d.text((M, H - 98), footer or "", font=bold(32), fill=C.PAPER)
    link = C.NEXT_LINK
    lf = sans(30)
    d.text((W - M - d.textlength(link, font=lf), H - 96), link, font=lf, fill=C.SUN)
    im.save(out, "JPEG", quality=92)
    return out


def photo(src, out):
    """Crop a meetup photo to 4:5 around its centre and save it as JPEG."""
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    ImageOps.fit(im, (W, H), Image.LANCZOS).save(out, "JPEG", quality=90)
    return out

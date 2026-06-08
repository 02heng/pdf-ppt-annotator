#!/usr/bin/env python3
"""从品牌设计生成应用图标（高分辨率主稿 + 小尺寸简化，任务栏更清晰）"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / "assets" / "branding"
WEB = ROOT / "src" / "web"
ELECTRON = ROOT / "electron" / "assets"

# 与 src/ui/theme.py 一致
PURPLE_LIGHT = (167, 139, 250)
PURPLE_MID = (124, 58, 237)
PURPLE_DARK = (91, 33, 182)
WHITE = (255, 255, 255)
MARKER_FILL = (237, 233, 254)
MARKER_BORDER = (124, 58, 237)
PEN = (251, 191, 36)
INK = (30, 22, 51)
LINE = (220, 210, 255)
SHADOW = (46, 16, 101, 90)

MASTER_SIZE = 1024
ICO_SIZES = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _gradient_bg(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    for y in range(size):
        for x in range(size):
            t = min(1.0, x / size * 0.35 + y / size * 0.65)
            r = _lerp(PURPLE_LIGHT[0], PURPLE_DARK[0], t)
            g = _lerp(PURPLE_LIGHT[1], PURPLE_DARK[1], t)
            b = _lerp(PURPLE_LIGHT[2], PURPLE_DARK[2], t)
            px[x, y] = (r, g, b, 255)
    return img


def _scale(size: int, v: float) -> int:
    return max(1, int(round(v * size / 512)))


def _fonts(size: int) -> tuple:
    s = _scale(size, 1)
    try:
        return (
            ImageFont.truetype("segoeui.ttf", _scale(size, 26)),
            ImageFont.truetype("segoeuib.ttf", _scale(size, 52)),
            ImageFont.truetype("segoeuib.ttf", _scale(size, 34)),
        )
    except OSError:
        f = ImageFont.load_default()
        return f, f, f


def _rounded_mask(size: int, margin_ratio: float, radius_ratio: float) -> Image.Image:
    m = int(size * margin_ratio)
    rad = int(size * radius_ratio)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [m, m, size - m, size - m], radius=rad, fill=255
    )
    return mask


def draw_logo(size: int = MASTER_SIZE, *, compact: bool = False) -> Image.Image:
    """
    TO PDF 批注图标：主体占画布约 78%，小尺寸用 compact 加粗简化。
    """
    img = _gradient_bg(size)
    margin = 0.028 if compact else 0.04
    radius = 0.19 if compact else 0.2
    img.putalpha(_rounded_mask(size, margin, radius))
    draw = ImageDraw.Draw(img)
    s = lambda v: _scale(size, v)
    font_pdf, font_num, font_note = _fonts(size)

    # 文档阴影
    doc = [s(96), s(88), s(416), s(424)]
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [doc[0] + s(8), doc[1] + s(10), doc[2] + s(8), doc[3] + s(10)],
        radius=s(28),
        fill=SHADOW,
    )
    img = Image.alpha_composite(img, shadow)
    draw = ImageDraw.Draw(img)

    doc_r = s(22) if compact else s(26)
    draw.rounded_rectangle(doc, radius=doc_r, fill=WHITE)

    line_h = s(16) if compact else s(14)
    line_r = s(8) if compact else s(7)
    lines = (
        (s(132), s(148), s(252), line_h),
        (s(132), s(188), s(320), line_h),
        (s(132), s(228), s(288), line_h),
    )
    if not compact:
        lines = (*lines, (s(132), s(268), s(304), line_h))
    for x1, y1, x2, h in lines:
        draw.rounded_rectangle([x1, y1, x2, y1 + h], radius=line_r, fill=LINE)

    # PDF 角标（加大）
    badge = [s(300), s(92), s(416), s(148)]
    draw.rounded_rectangle(badge, radius=s(14), fill=PURPLE_MID)
    draw.text((s(358), s(118)), "PDF", fill=WHITE, font=font_pdf, anchor="mm")

    if compact:
        # 小图标：粗批注块 + 粗笔触，去掉细笔帽
        draw.rounded_rectangle(
            [s(318), s(268), s(400), s(352)],
            radius=s(16),
            fill=MARKER_FILL,
            outline=MARKER_BORDER,
            width=max(2, s(8)),
        )
        draw.text((s(359), s(308)), "注", fill=PURPLE_DARK, font=font_note, anchor="mm")
        draw.rounded_rectangle(
            [s(268), s(338), s(420), s(372)],
            radius=s(14),
            fill=PEN,
        )
    else:
        draw.rounded_rectangle(
            [s(308), s(258), s(396), s(346)],
            radius=s(18),
            fill=MARKER_FILL,
            outline=MARKER_BORDER,
            width=s(7),
        )
        draw.text((s(352), s(300)), "注", fill=PURPLE_DARK, font=font_note, anchor="mm")
        draw.rounded_rectangle(
            [s(262), s(328), s(430), s(358)],
            radius=s(15),
            fill=PEN,
        )
        draw.rounded_rectangle(
            [s(430), s(334), s(462), s(352)], radius=s(6), fill=INK
        )
        # 高光
        draw.ellipse([s(118), s(102), s(168), s(152)], fill=(255, 255, 255, 48))

    return img


def _resize_logo(src: Image.Image, target: int, *, compact: bool) -> Image.Image:
    if target <= 48:
        frame = draw_logo(target, compact=True)
    else:
        frame = src.resize((target, target), Image.Resampling.LANCZOS)
        if target <= 64:
            frame = frame.filter(ImageFilter.UnsharpMask(radius=0.6, percent=120, threshold=2))
    return frame.convert("RGBA")


def write_ico(master: Image.Image, path: Path) -> None:
    base = master.resize((256, 256), Image.Resampling.LANCZOS)
    base.save(
        path,
        format="ICO",
        sizes=[(n, n) for n in ICO_SIZES],
    )


def write_svg(path: Path) -> None:
    path.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="Bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#a78bfa"/>
      <stop offset="55%" stop-color="#7c3aed"/>
      <stop offset="100%" stop-color="#5b21b6"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#2e1065" flood-opacity="0.35"/>
    </filter>
  </defs>
  <rect width="512" height="512" rx="98" ry="98" fill="url(#Bg)"/>
  <g filter="url(#shadow)">
    <rect x="96" y="88" width="320" height="336" rx="26" fill="#ffffff"/>
    <rect x="132" y="148" width="120" height="14" rx="7" fill="#dcd4ff"/>
    <rect x="132" y="188" width="188" height="14" rx="7" fill="#dcd4ff"/>
    <rect x="132" y="228" width="156" height="14" rx="7" fill="#dcd4ff"/>
    <rect x="132" y="268" width="172" height="14" rx="7" fill="#dcd4ff"/>
    <rect x="300" y="92" width="116" height="56" rx="14" fill="#7c3aed"/>
    <text x="358" y="128" text-anchor="middle" font-family="Segoe UI, Microsoft YaHei, sans-serif" font-size="26" font-weight="700" fill="#ffffff">PDF</text>
    <rect x="308" y="258" width="88" height="88" rx="18" fill="#ede9fe" stroke="#7c3aed" stroke-width="7"/>
    <text x="352" y="308" text-anchor="middle" font-family="Segoe UI, Microsoft YaHei, sans-serif" font-size="34" font-weight="700" fill="#5b21b6">注</text>
    <rect x="262" y="328" width="168" height="30" rx="15" fill="#fbbf24"/>
    <rect x="430" y="334" width="32" height="18" rx="6" fill="#1e1633"/>
  </g>
  <ellipse cx="143" cy="127" rx="25" ry="25" fill="#ffffff" opacity="0.2"/>
</svg>
""",
        encoding="utf-8",
    )


def main() -> int:
    BRAND.mkdir(parents=True, exist_ok=True)
    WEB.mkdir(parents=True, exist_ok=True)

    write_svg(BRAND / "logo.svg")

    logo = draw_logo(MASTER_SIZE, compact=False)
    icon_png = BRAND / "icon.png"
    logo.save(icon_png, "PNG", optimize=True)
    print(f"[icons] OK -> {icon_png} ({MASTER_SIZE}px)")

    icon_ico = BRAND / "icon.ico"
    write_ico(logo, icon_ico)
    print(f"[icons] OK -> {icon_ico} (sizes: {ICO_SIZES})")

    fav = WEB / "favicon.png"
    _resize_logo(logo, 64, compact=True).save(fav, "PNG")
    print(f"[icons] OK -> {fav}")

    toolbar = BRAND / "toolbar-logo.png"
    _resize_logo(logo, 72, compact=False).save(toolbar, "PNG")
    print(f"[icons] OK -> {toolbar}")

    brand = WEB / "brand-logo.png"
    brand.write_bytes(toolbar.read_bytes())
    print(f"[icons] OK -> {brand}")

    fav_ico = WEB / "favicon.ico"
    fav_ico.write_bytes(icon_ico.read_bytes())
    print(f"[icons] OK -> {fav_ico}")

    ELECTRON.mkdir(parents=True, exist_ok=True)
    for src, name in (
        (icon_png, "icon.png"),
        (icon_ico, "icon.ico"),
        (toolbar, "toolbar-logo.png"),
    ):
        dest = ELECTRON / name
        if src.resolve() != dest.resolve():
            dest.write_bytes(src.read_bytes())
        print(f"[icons] OK -> {dest}")

    app_icon = ELECTRON / "app-icon.png"
    logo.resize((512, 512), Image.Resampling.LANCZOS).save(app_icon, "PNG")
    print(f"[icons] OK -> {app_icon}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

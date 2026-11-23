"""
SiteGlow NG Visual Renderer
Generates glassmorphic dark-luxury visuals (1080x1350 Carousel Slides + 1080x1920 Reel Scenes
with Edge-TTS voiceover, motion graphics, portfolio pop-ups, and word-level dynamic captions).
Works identically on Windows and Linux (GitHub Actions Ubuntu runners).
"""
import asyncio
import math
import os
import subprocess
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
LOGO_PATH = ASSETS / "logo.jpg"


def _find_font(bold: bool = True) -> str:
    candidates = (
        [
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
        if bold
        else [
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
    )
    for c in candidates:
        if os.path.exists(c):
            return c
    raise FileNotFoundError("No TrueType font found on system.")


FONT_BOLD_PATH = _find_font(bold=True)
FONT_REG_PATH = _find_font(bold=False)


def fnt(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD_PATH if bold else FONT_REG_PATH, size)


def load_logo_transparent() -> Image.Image:
    src = Image.open(LOGO_PATH).convert("RGBA")
    arr = np.array(src).astype(np.float32)
    lum = np.maximum(np.maximum(arr[:, :, 0], arr[:, :, 1]), arr[:, :, 2])
    alpha = np.clip((lum - 18.0) / 55.0, 0.0, 1.0) ** 0.85
    out = np.zeros_like(arr, dtype=np.uint8)
    out[:, :, :3] = np.clip(arr[:, :, :3] * 1.04, 0, 255).astype(np.uint8)
    out[:, :, 3] = (alpha * 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def make_dark_mesh_bg(w: int, h: int, glow_rgb=(235, 35, 50), glow2_rgb=(0, 175, 255)) -> Image.Image:
    """Rich dark obsidian gradient with soft neon ambient orbs and subtle tech grid."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = xx / w, yy / h

    # Base obsidian gradient
    r = 8 + 10 * (1 - ny)
    g = 10 + 12 * (1 - ny)
    b = 18 + 20 * (1 - ny)

    # Top-right crimson/accent orb
    d1 = np.exp(-((nx - 0.82) ** 2 / 0.22 + (ny - 0.16) ** 2 / 0.14))
    # Bottom-left cyan/emerald orb
    d2 = np.exp(-((nx - 0.18) ** 2 / 0.26 + (ny - 0.84) ** 2 / 0.18))

    r = np.clip(r + d1 * glow_rgb[0] * 0.42 + d2 * glow2_rgb[0] * 0.24, 0, 255)
    g = np.clip(g + d1 * glow_rgb[1] * 0.42 + d2 * glow2_rgb[1] * 0.24, 0, 255)
    b = np.clip(b + d1 * glow_rgb[2] * 0.42 + d2 * glow2_rgb[2] * 0.24, 0, 255)

    rgb = np.stack([r, g, b], axis=2).astype(np.uint8)
    img = Image.fromarray(rgb, "RGB").convert("RGBA")

    # Subtle architectural dot/line grid
    grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    step = 72
    for x in range(0, w, step):
        gd.line([(x, 0), (x, h)], fill=(255, 255, 255, 9), width=1)
    for y in range(0, h, step):
        gd.line([(0, y), (w, y)], fill=(255, 255, 255, 9), width=1)
    img.alpha_composite(grid)
    return img


def draw_glass_box(canvas: Image.Image, box: tuple[int, int, int, int], radius=36,
                   fill=(18, 22, 36, 200), border=(255, 255, 255, 95),
                   glow=(235, 35, 45, 90)):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0

    # Soft glow & shadow
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([x0 - 4, y0 + 8, x1 + 4, y1 + 16], radius=radius + 4, fill=(0, 0, 0, 150))
    if glow:
        sd.rounded_rectangle([x0 - 5, y0 - 5, x1 + 5, y1 + 5], radius=radius + 5, outline=glow, width=6)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    canvas.alpha_composite(sh)

    # Frosted glass body + diagonal specular sheen
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    grad = np.clip(1.0 - (xx / (w * 0.9) + yy / (h * 0.7)), 0, 1)
    sh_arr = np.zeros((h, w, 4), dtype=np.uint8)
    sh_arr[:, :, :3] = 255
    sh_arr[:, :, 3] = (grad * 42).astype(np.uint8)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
    layer.paste(Image.fromarray(sh_arr, "RGBA"), (x0, y0), mask)

    ld.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=border, width=2)
    ld.line([(x0 + radius, y0 + 1), (x1 - radius, y0 + 1)], fill=(255, 255, 255, 165), width=2)
    canvas.alpha_composite(layer)


def draw_brand_header(canvas: Image.Image, logo_trans: Image.Image, right_pill: str = "@SITEGLOWNG"):
    w = canvas.width
    # Top-left glass brand pill
    draw_glass_box(canvas, (52, 48, 430, 134), radius=43, fill=(14, 17, 28, 210),
                   border=(255, 255, 255, 100), glow=(235, 35, 45, 75))
    s_icon = logo_trans.crop((190, 95, 890, 585)).resize((78, 56), Image.LANCZOS)
    canvas.alpha_composite(s_icon, (68, 63))
    d = ImageDraw.Draw(canvas)
    d.text((156, 63), "SITEGLOW", font=fnt(26, True), fill=(255, 255, 255, 255))
    d.text((314, 63), "NG", font=fnt(26, True), fill=(245, 45, 55, 255))
    d.text((158, 96), "WEBSITES THAT SHINE", font=fnt(14, True), fill=(195, 210, 235, 220))

    # Top-right tag pill
    draw_glass_box(canvas, (w - 295, 58, w - 52, 122), radius=32, fill=(24, 30, 46, 200),
                   border=(255, 255, 255, 80), glow=None)
    d = ImageDraw.Draw(canvas)
    d.text((w - 266, 77), right_pill, font=fnt(20, True), fill=(230, 240, 255, 245))


def draw_growth_graph_inside(canvas: Image.Image, x0: int, y0: int, x1: int, y1: int):
    d = ImageDraw.Draw(canvas)
    # Google search bar header
    d.rounded_rectangle([x0 + 24, y0 + 22, x1 - 24, y0 + 84], radius=31, fill=(26, 34, 52, 240),
                        outline=(110, 175, 255, 165), width=2)
    d.text((x0 + 48, y0 + 34), "G", font=fnt(34, True), fill=(66, 133, 244, 255))
    d.text((x0 + 96, y0 + 39), "best local business near me...", font=fnt(24, True), fill=(235, 245, 255, 250))
    d.rounded_rectangle([x1 - 175, y0 + 32, x1 - 36, y0 + 74], radius=21, fill=(235, 38, 48, 250))
    d.text((x1 - 152, y0 + 41), "SEARCH", font=fnt(20, True), fill=(255, 255, 255, 255))

    gx0, gy0, gx1, gy1 = x0 + 74, y0 + 135, x1 - 38, y1 - 52
    for i in range(4):
        yy = int(gy0 + i * (gy1 - gy0) / 3)
        d.line([(gx0, yy), (gx1, yy)], fill=(255, 255, 255, 35), width=1)
        lbl = ["100%", "65%", "30%", "0%"][i]
        d.text((x0 + 18, yy - 11), lbl, font=fnt(16, True), fill=(160, 175, 200, 195))

    # Flat red line (no website)
    low_pts = [(gx0 + int(i * (gx1 - gx0) / 6), gy1 - 16 - (i % 2) * 5) for i in range(7)]
    d.line(low_pts, fill=(255, 85, 85, 200), width=5)
    d.text((gx1 - 275, gy1 - 46), "NO WEBSITE (NOT FOUND)", font=fnt(18, True), fill=(255, 115, 115, 245))

    # Rising emerald curve (SiteGlow NG)
    hs = [0.08, 0.19, 0.34, 0.52, 0.70, 0.86, 0.96]
    hi_pts = [(gx0 + int(i * (gx1 - gx0) / 6), int(gy1 - h * (gy1 - gy0))) for i, h in enumerate(hs)]
    fill_l = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(fill_l).polygon([(gx0, gy1)] + hi_pts + [(gx1, gy1)], fill=(0, 235, 165, 52))
    canvas.alpha_composite(fill_l)
    d = ImageDraw.Draw(canvas)
    d.line(hi_pts, fill=(0, 245, 175, 255), width=7)
    for (px, py) in hi_pts:
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=(255, 255, 255, 255), outline=(0, 230, 160, 255), width=3)
    d.text((hi_pts[2][0] - 20, hi_pts[4][1] - 36), "WITH SITEGLOW NG (+340%)", font=fnt(20, True), fill=(70, 255, 185, 255))


def draw_portfolio_inside(canvas: Image.Image, portfolio_name: str, x0: int, y0: int, x1: int, y1: int, badge: str):
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([x0 + 18, y0 + 16, x1 - 18, y0 + 64], radius=16, fill=(26, 32, 48, 240))
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([x0 + 36 + i * 24, y0 + 33, x0 + 50 + i * 24, y0 + 47], fill=col)
    d.text((x0 + 125, y0 + 29), badge, font=fnt(19, True), fill=(240, 245, 255, 245))

    p_path = ASSETS / "portfolio" / portfolio_name
    if not p_path.exists():
        p_path = ASSETS / "portfolio" / "metro_cars.png"
    shot = Image.open(p_path).convert("RGBA")
    vw, vh = (x1 - x0) - 36, (y1 - y0) - 96
    shot_r = shot.resize((vw, vh), Image.LANCZOS)
    mask = Image.new("L", (vw, vh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, vw, vh], radius=22, fill=255)
    canvas.paste(shot_r, (x0 + 18, y0 + 76), mask)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([x0 + 18, y0 + 76, x0 + 18 + vw, y0 + 76 + vh], radius=22, outline=(255, 255, 255, 85), width=2)


def _draw_wrapped(draw: ImageDraw.ImageDraw, text: str, x: int, y: int, max_chars: int,
                  font: ImageFont.FreeTypeFont, fill, line_h: int) -> int:
    cur_y = y
    for line in textwrap.wrap(text, width=max_chars):
        draw.text((x, cur_y), line, font=font, fill=fill)
        cur_y += line_h
    return cur_y


# ==============================================================================
# 1. CAROUSEL RENDERER (5 x 1080x1350 PNG/JPG slides)
# ==============================================================================
def render_carousel(content: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    logo_trans = load_logo_transparent()
    logo_raw = Image.open(LOGO_PATH).convert("RGBA")
    paths = []

    slides = content["slides"]
    total = len(slides)
    for idx, s in enumerate(slides, start=1):
        style = s.get("style", "problem")
        glow1 = (235, 35, 50) if style in ("cover", "problem", "cta") else (0, 210, 150)
        canvas = make_dark_mesh_bg(1080, 1350, glow_rgb=glow1, glow2_rgb=(0, 165, 255))
        draw_brand_header(canvas, logo_trans, right_pill=f"SLIDE 0{idx} / 0{total}")

        # Main glass card
        draw_glass_box(canvas, (52, 175, 1028, 1210), radius=42, fill=(14, 18, 30, 215),
                       border=(255, 255, 255, 105), glow=(glow1[0], glow1[1], glow1[2], 95))
        d = ImageDraw.Draw(canvas)

        # Tag pill
        tag_fill = (235, 35, 48, 245) if style in ("cover", "problem", "cta") else (20, 165, 115, 245)
        d.rounded_rectangle([96, 218, 490, 272], radius=27, fill=tag_fill)
        d.text((122, 232), s["tag"][:26], font=fnt(22, True), fill=(255, 255, 255, 255))

        # Headline
        next_y = _draw_wrapped(d, s["headline"], 96, 305, 18, fnt(58, True), (255, 255, 255, 255), 72)

        # Body text
        next_y = _draw_wrapped(d, s["body"], 96, next_y + 24, 38, fnt(32, False), (210, 222, 242, 245), 46)

        # Visual showcase area in bottom half of the card
        vis_y0 = max(next_y + 38, 665)
        vis_y1 = 1155
        if style == "graph":
            draw_glass_box(canvas, (92, vis_y0, 988, vis_y1), radius=28, fill=(10, 14, 24, 235),
                           border=(70, 235, 165, 140), glow=None)
            draw_growth_graph_inside(canvas, 92, vis_y0, 988, vis_y1)
        elif style in ("portfolio", "cover"):
            draw_glass_box(canvas, (92, vis_y0, 988, vis_y1), radius=28, fill=(10, 14, 24, 235),
                           border=(255, 255, 255, 100), glow=None)
            draw_portfolio_inside(canvas, content["portfolio"], 92, vis_y0, 988, vis_y1, "3D INTERACTIVE SHOWCASE")
        elif style == "cta":
            # Crisp Logo + Big CTA Button
            l_box = logo_raw.resize((270, 270), Image.LANCZOS)
            mask = Image.new("L", (270, 270), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, 270, 270], radius=28, fill=255)
            canvas.paste(l_box, (405, vis_y0 + 15), mask)
            d = ImageDraw.Draw(canvas)
            d.rounded_rectangle([140, vis_y0 + 310, 940, vis_y0 + 405], radius=47, fill=(235, 35, 48, 255),
                                outline=(255, 215, 215, 220), width=3)
            d.text((238, vis_y0 + 335), "DM 'GLOW' TO START TODAY", font=fnt(38, True), fill=(255, 255, 255, 255))
            d.text((260, vis_y0 + 425), "PACKAGES STARTING FROM ₦150,000", font=fnt(28, True), fill=(255, 210, 90, 255))
        else:
            # Problem / checklist contrast box
            draw_glass_box(canvas, (92, vis_y0 + 20, 988, vis_y1 - 20), radius=28, fill=(52, 16, 24, 230),
                           border=(255, 75, 85, 200), glow=None)
            d = ImageDraw.Draw(canvas)
            d.text((134, vis_y0 + 68), "WITHOUT A WEBSITE:", font=fnt(28, True), fill=(255, 120, 125, 255))
            d.text((134, vis_y0 + 118), "X  Invisible on Google Search", font=fnt(30, True), fill=(255, 235, 235, 245))
            d.text((134, vis_y0 + 168), "X  Serious buyers question brand trust", font=fnt(30, True), fill=(255, 235, 235, 245))
            d.text((134, vis_y0 + 218), "X  Hours wasted replying 'DM for price'", font=fnt(30, True), fill=(255, 235, 235, 245))
            d.rounded_rectangle([134, vis_y0 + 290, 946, vis_y0 + 365], radius=22, fill=(20, 95, 65, 235),
                                outline=(60, 240, 160, 210), width=2)
            d.text((178, vis_y0 + 312), "FIX IT WITH SITEGLOW NG  |  FROM ₦150,000", font=fnt(28, True), fill=(110, 255, 185, 255))

        # Bottom swipe indicator
        d = ImageDraw.Draw(canvas)
        foot = "SWIPE LEFT  >>>" if idx < total else "SAVE & DM 'GLOW' NOW"
        d.text((52, 1252), "SITEGLOW NG  |  3D WEBSITES & GOOGLE SEO", font=fnt(22, True), fill=(175, 190, 215, 210))
        d.text((760, 1252), foot, font=fnt(24, True), fill=(255, 215, 95, 255))

        out_jpg = out_dir / f"slide_{idx:02d}.jpg"
        canvas.convert("RGB").save(out_jpg, quality=95)
        paths.append(out_jpg)
    return paths


# ==============================================================================
# 2. AUTONOMOUS REEL RENDERER (1080x1920 MP4 + Edge-TTS + Word-Level Captions)
# ==============================================================================
async def _tts_beat(text: str, voice: str, out_mp3: Path) -> list[dict]:
    import edge_tts

    comm = edge_tts.Communicate(text, voice, rate="+8%", boundary="WordBoundary")
    words = []
    with open(out_mp3, "wb") as fh:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                fh.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                st = chunk["offset"] / 10_000_000.0
                dur = chunk["duration"] / 10_000_000.0
                words.append({"w": chunk["text"], "s": st, "e": st + dur})
    return words


def _probe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True,
    ).strip()
    return float(out)


def _ass_time(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - int(sec)) * 100))
    if cs == 100:
        s += 1
        cs = 0
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _render_reel_scene_png(beat: dict, portfolio: str, beat_idx: int, logo_trans: Image.Image,
                           logo_raw: Image.Image, out_png: Path):
    accent = beat.get("accent", "red")
    glow_map = {"red": (235, 35, 50), "graph": (0, 215, 155), "portfolio": (0, 165, 255), "cta": (240, 40, 55)}
    g1 = glow_map.get(accent, (235, 35, 50))
    canvas = make_dark_mesh_bg(1080, 1920, glow_rgb=g1, glow2_rgb=(0, 175, 255))
    draw_brand_header(canvas, logo_trans, right_pill=beat.get("badge", "SITEGLOW NG")[:16].upper())

    d = ImageDraw.Draw(canvas)
    # Huge top kinetic headline (the on-screen hook)
    _draw_wrapped(d, beat["on_screen"].upper(), 60, 215, 14, fnt(78, True), (255, 255, 255, 255), 92)

    # Central Glassmorphic Showcase Card (y=470..1310)
    draw_glass_box(canvas, (52, 470, 1028, 1310), radius=44, fill=(14, 18, 30, 220),
                   border=(255, 255, 255, 115), glow=(g1[0], g1[1], g1[2], 125))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([92, 512, 460, 566], radius=27, fill=(g1[0], g1[1], g1[2], 245))
    d.text((116, 526), beat.get("badge", "SITEGLOW NG")[:20].upper(), font=fnt(22, True), fill=(255, 255, 255, 255))
    d.text((92, 590), beat.get("card_title", "SITEGLOW NG")[:30].upper(), font=fnt(40, True), fill=(255, 255, 255, 255))
    _draw_wrapped(d, beat.get("card_sub", ""), 92, 650, 40, fnt(28, False), (205, 220, 240, 240), 38)

    if accent == "graph":
        draw_glass_box(canvas, (88, 755, 992, 1265), radius=28, fill=(10, 14, 24, 235),
                       border=(65, 240, 170, 150), glow=None)
        draw_growth_graph_inside(canvas, 88, 755, 992, 1265)
    elif accent == "portfolio":
        draw_glass_box(canvas, (88, 755, 992, 1265), radius=28, fill=(10, 14, 24, 235),
                       border=(255, 255, 255, 110), glow=None)
        draw_portfolio_inside(canvas, portfolio, 88, 755, 992, 1265, "LIVE 3D WEBSITE PREVIEW")
    elif accent == "cta":
        l_box = logo_raw.resize((300, 300), Image.LANCZOS)
        mask = Image.new("L", (300, 300), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, 300, 300], radius=32, fill=255)
        canvas.paste(l_box, (390, 760), mask)
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle([126, 1090, 954, 1188], radius=49, fill=(235, 35, 48, 255),
                            outline=(255, 215, 215, 230), width=3)
        d.text((225, 1117), "SEND A DM: 'GLOW' NOW!", font=fnt(40, True), fill=(255, 255, 255, 255))
        d.text((255, 1214), "PACKAGES START FROM ₦150,000", font=fnt(28, True), fill=(255, 215, 95, 255))
    else:
        # High-impact alert showcase
        draw_glass_box(canvas, (88, 765, 992, 1255), radius=30, fill=(56, 14, 24, 235),
                       border=(255, 75, 85, 220), glow=None)
        d = ImageDraw.Draw(canvas)
        d.ellipse([475, 800, 605, 930], fill=(240, 38, 48, 255))
        d.text((521, 818), "!", font=fnt(82, True), fill=(255, 255, 255, 255))
        d.text((195, 965), "CLIENTS ARE SEARCHING GOOGLE", font=fnt(36, True), fill=(255, 235, 235, 255))
        d.text((220, 1025), "DON'T LET COMPETITORS WIN THEM", font=fnt(30, True), fill=(255, 175, 180, 245))
        d.rounded_rectangle([165, 1115, 915, 1200], radius=24, fill=(20, 95, 65, 240),
                            outline=(60, 245, 165, 215), width=2)
        d.text((215, 1142), "SITEGLOW NG  |  STARTS AT ₦150,000", font=fnt(30, True), fill=(110, 255, 185, 255))

    canvas.convert("RGB").save(out_png)


def render_reel(content: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    voice = os.getenv("TTS_VOICE", "en-NG-AbeoNeural")
    logo_trans = load_logo_transparent()
    logo_raw = Image.open(LOGO_PATH).convert("RGBA")

    beats = content["beats"]
    scene_mp4s = []
    audio_mp3s = []
    ass_events = []
    cur_t = 0.0

    for i, beat in enumerate(beats):
        mp3_path = out_dir / f"beat_{i}.mp3"
        png_path = out_dir / f"beat_{i}.png"
        clip_path = out_dir / f"beat_{i}.mp4"

        words = asyncio.run(_tts_beat(beat["voice"], voice, mp3_path))
        dur = _probe_duration(mp3_path) + 0.18
        _render_reel_scene_png(beat, content["portfolio"], i, logo_trans, logo_raw, png_path)

        # Render kinetic subtle zoom-in motion (1.0 -> 1.06 scale) at 30fps
        n_frames = max(30, int(round(dur * 30)))
        vf = (
            f"scale=1160:2062,zoompan=z='min(zoom+0.0005,1.06)':x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':d={n_frames}:s=1080x1920:fps=30,format=yuv420p"
        )
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(png_path),
             "-t", f"{dur:.3f}", "-vf", vf,
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(clip_path)],
            check=True,
        )
        scene_mp4s.append(clip_path)
        audio_mp3s.append(mp3_path)

        # Build word-level animated captions in 4-word chunks (with proportional fallback if TTS omits WordBoundary)
        if not words:
            toks = beat["voice"].split()
            speech_dur = max(0.4, dur - 0.18)
            total_chars = max(1, sum(len(t) for t in toks))
            pos = 0.0
            for t in toks:
                wd = speech_dur * (len(t) / total_chars)
                words.append({"w": t, "s": pos, "e": pos + wd})
                pos += wd

        for c_start in range(0, len(words), 4):
            chunk = words[c_start:c_start + 4]
            for wi, wobj in enumerate(chunk):
                ds = cur_t + wobj["s"]
                de = cur_t + (chunk[wi + 1]["s"] if wi + 1 < len(chunk) else wobj["e"] + 0.08)
                parts = []
                for j, ow in enumerate(chunk):
                    tok = ow["w"].upper()
                    if j == wi:
                        parts.append(r"{\c&H0038E8FF&\fscx114\fscy114\t(0,80,\fscx105\fscy105)}" + tok + r"{\c&H00FFFFFF&\fscx100\fscy100}")
                    else:
                        parts.append(tok)
                ass_events.append(f"Dialogue: 2,{_ass_time(ds)},{_ass_time(de)},CapBox,,0,0,0,,{' '.join(parts)}")
        cur_t += dur

    # Write ASS caption file
    font_name = "Segoe UI" if os.name == "nt" else "DejaVu Sans"
    ass_path = out_dir / "reel_captions.ass"
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CapBox,{font_name},56,&H00FFFFFF&,&H0000FFFF&,&H00120E0B&,&H88000000&,-1,0,0,0,100,100,1.2,0,1,5.5,3.5,2,60,60,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass_path.write_text(ass_header + "\n".join(ass_events) + "\n", encoding="utf-8")

    # Concat video + padded audio + studio vocal loudness + burn captions
    v_list = out_dir / "v_concat.txt"
    v_list.write_text("\n".join(f"file '{p.as_posix()}'" for p in scene_mp4s), encoding="utf-8")

    a_inputs = []
    a_filters = []
    for idx, ap in enumerate(audio_mp3s):
        a_inputs += ["-i", str(ap)]
        a_filters.append(f"[{idx + 1}:a]apad=pad_dur=0.18[a{idx}];")
    a_concat = "".join(f"[a{idx}]" for idx in range(len(audio_mp3s)))
    ass_esc = str(ass_path).replace("\\", "/").replace(":", "\\:")

    fc = (
        "".join(a_filters)
        + f"{a_concat}concat=n={len(audio_mp3s)}:v=0:a=1,"
        + "highpass=f=80,acompressor=threshold=-18dB:ratio=3:attack=8:release=100:makeup=2dB,"
        + "loudnorm=I=-14:TP=-1.0:LRA=8[aout];"
        + f"[0:v]ass=filename='{ass_esc}',format=yuv420p[vout]"
    )

    final_mp4 = out_dir / "siteglow_reel.mp4"
    cmd = (
        ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(v_list)]
        + a_inputs
        + ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
           "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
           str(final_mp4)]
    )
    subprocess.run(cmd, check=True)
    return final_mp4

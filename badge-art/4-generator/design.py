"""Haven Tashkent PCB badge — geometry + layer art generator.

All art is drawn on one canvas = the board's bounding box, at S px/mm,
so every PNG lines up 1:1 with the Edge.Cuts outline.
"""
import json, math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

S = 40                      # px per mm  (= 1016 dpi)
DPI = S * 25.4
OUT = "out"

# ---------------------------------------------------------------- brand
LIME, CARROT = (184, 193, 31), (252, 134, 22)
BANANA, PUMPKIN, FADED = (249, 221, 96), (232, 113, 54), (223, 160, 99)
UMBER, LUCKY = (120, 61, 43), (168, 162, 55)
CREAM = (255, 248, 234)
F_HEAD = "fonts/DarumadropOne-Regular.ttf"
F_BODY = "fonts/Jua-Regular.ttf"

# ---------------------------------------------------------------- layout (mm)
W = 58.0
HOLE = (W / 2, 6.0)          # hanging hole centre
TAB_R = 6.0                  # tab radius around hole
DRILL, PAD = 4.3, 8.0        # KiCad MountingHole_4.3mm_M4_Pad
LOGO_W = 50.0
LOGO_Y = 7.4
PLATE = (8.0, 40.6, 50.0, 53.4)   # x0,y0,x1,y1 name plate
PLATE_R = 3.0
BORDER = 2.0                 # board edge beyond logo / plate
DAVEN_W = 16.5
DAVEN_X = 40.0               # left edge of peeking Daven
DAVEN_BOTTOM = PLATE[1] + 2.4
CITY_Y = PLATE[3] + 3.1          # baseline of the city/date line
H = CITY_Y + 2.6


def px(v):
    return int(round(v * S))


CW, CH = px(W), px(H)


def blank(mode="L", fill=0):
    return Image.new(mode, (CW, CH), fill)


def disc(r_mm):
    r = max(1, px(r_mm))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def dilate(m, r):
    return cv2.dilate(m, disc(r))


def erode(m, r):
    return cv2.erode(m, disc(r), borderType=cv2.BORDER_CONSTANT, borderValue=0)


def load_rgba(path, width_mm):
    im = Image.open(path).convert("RGBA")
    im = im.crop(im.getchannel("A").getbbox())
    w = px(width_mm)
    h = round(im.height * w / im.width)
    return im.resize((w, h), Image.LANCZOS)


# ---------------------------------------------------------------- placed art
logo_wc = load_rgba("logos/haven-logo-watercolor.png", LOGO_W)
logo_or = load_rgba("logos/haven-logo-orange.png", LOGO_W)
LOGO_POS = (px((W - LOGO_W) / 2), px(LOGO_Y))
LOGO_H = logo_wc.height / S

daven = load_rgba("daven-pudding/daven-hero.png", DAVEN_W)
DAVEN_POS = (px(DAVEN_X), px(DAVEN_BOTTOM) - daven.height)


def placed_alpha(im, pos, thresh=60):
    c = blank()
    c.paste(im.getchannel("A"), pos)
    return (np.array(c) > thresh).astype(np.uint8) * 255


logo_mask = placed_alpha(logo_or, LOGO_POS)
daven_mask = placed_alpha(daven, DAVEN_POS)


def rrect_mask(box, r):
    c = blank()
    ImageDraw.Draw(c).rounded_rectangle([px(v) for v in box], radius=px(r), fill=255)
    return np.array(c)


def circle_mask(cx, cy, r):
    c = blank()
    ImageDraw.Draw(c).ellipse([px(cx - r), px(cy - r), px(cx + r), px(cy + r)], fill=255)
    return np.array(c)


plate_mask = rrect_mask(PLATE, PLATE_R)

# ---------------------------------------------------------------- outline
def build_outline():
    m = np.zeros((CH, CW), np.uint8)
    # fill the logo's inner gaps first so the sticker border is solid
    lg = cv2.morphologyEx(logo_mask, cv2.MORPH_CLOSE, disc(2.2))
    m |= dilate(lg, BORDER)
    m |= dilate(rrect_mask((5.0, 33.0, W - 5.0, H - BORDER), 4.0), BORDER)
    m |= dilate(daven_mask, 1.4)
    m |= circle_mask(*HOLE, TAB_R)
    # pad canvas so closing near edges behaves
    pad = px(6)
    mp = cv2.copyMakeBorder(m, pad, pad, pad, pad, cv2.BORDER_CONSTANT, 0)
    mp = cv2.morphologyEx(mp, cv2.MORPH_CLOSE, disc(3.0))   # concave corners >= 3 mm radius
    mp = cv2.morphologyEx(mp, cv2.MORPH_OPEN, disc(1.2))    # convex corners  >= 1.2 mm radius
    # fill holes
    cnts, _ = cv2.findContours(mp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    big = max(cnts, key=cv2.contourArea)
    mp = np.zeros_like(mp)
    cv2.drawContours(mp, [big], -1, 255, -1)
    # smooth the pixel staircase
    mp = cv2.GaussianBlur(mp, (0, 0), S * 0.25)
    mp = ((mp > 127) * 255).astype(np.uint8)
    return mp[pad:-pad, pad:-pad], mp, pad


outline_mask, outline_padded, PADPX = build_outline()


def outline_polygon():
    """Sub-pixel, smoothed outline polygon in mm (canvas coordinates)."""
    from skimage import measure
    soft = cv2.GaussianBlur(outline_padded.astype(np.float32), (0, 0), S * 0.15)
    cs = measure.find_contours(soft, 127.5)
    c = max(cs, key=len)[:, ::-1]                       # (row,col) -> (x,y)
    c = cv2.approxPolyDP(c.astype(np.float32).reshape(-1, 1, 2), 0.35, True)[:, 0, :].astype(float)
    return (c - PADPX) / S


if __name__ == "__main__":
    ys, xs = np.nonzero(outline_mask)
    print("canvas mm", W, H, "outline bbox mm",
          xs.min() / S, xs.max() / S, ys.min() / S, ys.max() / S)
    print("logo h", LOGO_H, "daven h", daven.height / S)
    Image.fromarray(outline_mask).save("dbg_outline.png")


# ---------------------------------------------------------------- text helpers
def font(path, cap_mm):
    """Return a PIL font whose capital-letter height is cap_mm."""
    probe = ImageFont.truetype(path, 200)
    b = probe.getbbox("H")
    cap = (b[3] - b[1]) / 200
    return ImageFont.truetype(path, max(4, round(px(cap_mm) / cap)))


def draw_text(img, xy_mm, text, path, cap_mm, fill, anchor="ls", spacing_mm=0.0):
    """anchor: 'ls' left-baseline, 'ms' middle-baseline, 'rs' right-baseline."""
    d = ImageDraw.Draw(img)
    f = font(path, cap_mm)
    if spacing_mm == 0:
        d.text((px(xy_mm[0]), px(xy_mm[1])), text, font=f, fill=fill, anchor=anchor)
        return
    # manual letter spacing
    widths = [f.getlength(ch) for ch in text]
    total = sum(widths) + px(spacing_mm) * (len(text) - 1)
    x = px(xy_mm[0]) - (total / 2 if anchor[0] == "m" else total if anchor[0] == "r" else 0)
    for ch, w in zip(text, widths):
        d.text((x, px(xy_mm[1])), ch, font=f, fill=fill, anchor="ls")
        x += w + px(spacing_mm)


def draw_dotted_line(img, xy_mm, parts, path, cap_mm, fill, gap_mm=1.6, dot_mm=0.55):
    """Centered text parts separated by drawn dots (Jua has no middle-dot glyph)."""
    f = font(path, cap_mm)
    ws = [f.getlength(p) / S for p in parts]
    total = sum(ws) + gap_mm * 2 * (len(parts) - 1)
    x = xy_mm[0] - total / 2
    d = ImageDraw.Draw(img)
    for i, (p, w) in enumerate(zip(parts, ws)):
        d.text((px(x), px(xy_mm[1])), p, font=f, fill=fill, anchor="ls")
        x += w
        if i < len(parts) - 1:
            cxm, cym, r = x + gap_mm, xy_mm[1] - cap_mm / 2, dot_mm / 2
            d.ellipse([px(cxm - r), px(cym - r), px(cxm + r), px(cym + r)], fill=fill)
            x += gap_mm * 2


def text_width_mm(text, path, cap_mm):
    return font(path, cap_mm).getlength(text) / S


def with_outline(im, r_mm, color=(255, 255, 255, 255)):
    """Sticker-style white outline around an RGBA image (returns bigger canvas offset)."""
    pad = px(r_mm) + 2
    a = np.array(im.getchannel("A"))
    a = cv2.copyMakeBorder(a, pad, pad, pad, pad, cv2.BORDER_CONSTANT, 0)
    o = cv2.dilate((a > 40).astype(np.uint8) * 255, disc(r_mm))
    o = cv2.GaussianBlur(o, (0, 0), 1.2)
    base = Image.new("RGBA", (a.shape[1], a.shape[0]), color[:3] + (0,))
    base.putalpha(Image.fromarray(o))
    base.alpha_composite(im, (pad, pad))
    return base, pad


# ---------------------------------------------------------------- variants
VARIANTS = {
    "participant": dict(
        role="HACKER", field=LIME, field2=LUCKY, plate_edge=CARROT,
        role_col=CARROT, ink=UMBER, sub=("TASHKENT", "14-15 NOV 2026"),
    ),
    "organizer": dict(
        role="ORGANIZER", field=UMBER, field2=(92, 44, 30), plate_edge=BANANA,
        role_col=UMBER, ink=UMBER, sub=("TASHKENT", "14-15 NOV 2026"),
    ),
}

HOLE_KEEPOUT = PAD / 2 + 0.6   # no ink within this radius of the hole centre
EDGE_INSET = 1.3               # white "sticker border" left unprinted


def front_color(v):
    """Full-colour UV print artwork (RGBA, transparent = bare white soldermask)."""
    cfg = VARIANTS[v]
    img = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    field = erode(outline_mask, EDGE_INSET)
    field &= ~circle_mask(*HOLE, HOLE_KEEPOUT + EDGE_INSET)
    # soft vertical gradient field
    grad = np.linspace(0, 1, CH)[:, None, None]
    c1, c2 = np.array(cfg["field"], float), np.array(cfg["field2"], float)
    col = (c1 * (1 - grad * 0.55) + c2 * grad * 0.55).astype(np.uint8)
    col = np.broadcast_to(col, (CH, CW, 3)).copy()
    layer = Image.fromarray(col).convert("RGBA")
    layer.putalpha(Image.fromarray(field))
    img.alpha_composite(layer)

    # logo with white sticker outline
    lg, pad = with_outline(logo_wc, 1.0)
    img.alpha_composite(lg, (LOGO_POS[0] - pad, LOGO_POS[1] - pad))

    # Daven peeking (behind the plate)
    dv, dpad = with_outline(daven, 0.7)
    img.alpha_composite(dv, (DAVEN_POS[0] - dpad, DAVEN_POS[1] - dpad))

    # name plate
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = PLATE
    d.rounded_rectangle([px(x0), px(y0), px(x1), px(y1)], radius=px(PLATE_R),
                        fill=cfg["plate_edge"] + (255,))
    e = 0.7
    d.rounded_rectangle([px(x0 + e), px(y0 + e), px(x1 - e), px(y1 - e)],
                        radius=px(PLATE_R - e), fill=CREAM + (255,))
    # role word
    cx = (x0 + x1) / 2
    draw_text(img, (cx, y0 + 5.6), cfg["role"], F_HEAD, 4.0, cfg["role_col"] + (255,), anchor="ms",
              spacing_mm=0.25)
    # name line
    ly = y1 - 2.3
    d.line([px(x0 + 9.0), px(ly), px(x1 - 3.0), px(ly)], fill=cfg["ink"] + (150,), width=px(0.2))
    draw_text(img, (x0 + 2.6, ly), "name", F_BODY, 1.5, cfg["ink"] + (255,))
    # city + date line under the plate (on the coloured field)
    draw_dotted_line(img, (cx, CITY_Y), cfg["sub"], F_BODY, 1.55, (255, 255, 255, 255))
    # no ink on the ENIG hole pad: clear the logo/Daven too, not only the field
    a = np.array(img.getchannel("A"))
    a[circle_mask(*HOLE, HOLE_KEEPOUT) > 0] = 0
    img.putalpha(Image.fromarray(a))
    return img


if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    for v in VARIANTS:
        im = front_color(v)
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.putalpha(Image.fromarray(outline_mask))
        canvas = Image.new("RGBA", im.size, (40, 40, 40, 255))
        canvas.alpha_composite(bg)
        canvas.alpha_composite(im)
        canvas.convert("RGB").resize((CW // 3, CH // 3), Image.LANCZOS).save(f"dbg_front_{v}.png")

"""Photo-ish mockups of each badge side, built from the exact layer PNGs."""
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
import design as d
import layers as L
from design import S, px

OUTL = L.OUTLINE
HW, HH = L.PWC, L.PHC
HOLE = L.HOLE_C

MASK = {"white": (246, 246, 242), "orange": (232, 110, 30), "black": (28, 28, 30), "yellow": (236, 196, 40)}
SILK = {"white": (250, 250, 250), "black": (20, 20, 20)}
FR4 = (206, 190, 128)


def circ(cx, cy, r, w=HW, h=HH):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([px(cx - r), px(cy - r), px(cx + r), px(cy + r)], fill=255)
    return np.array(m)


def gold_tex():
    yy, xx = np.mgrid[0:HH, 0:HW]
    t = ((xx + yy) / (HW + HH))
    t = 0.5 + 0.5 * np.sin(t * 9.0)
    c1, c2 = np.array([176, 132, 40.]), np.array([250, 222, 140.])
    return (c1 * (1 - t[..., None]) + c2 * t[..., None]).astype(np.uint8)


def fr4_tex():
    rng = np.random.default_rng(1)
    n = rng.normal(0, 7, (HH, HW, 1))
    weave = (np.sin(np.arange(HW) / 3.0)[None, :, None] * np.sin(np.arange(HH) / 3.0)[:, None, None]) * 6
    return np.clip(np.array(FR4, float) + n + weave, 0, 255).astype(np.uint8)


def side(top_rgb, outline, hole_xy, extra=None):
    """Turn a flat top-face RGB + outline into a lifted board with edge + shadow, RGBA."""
    pad = px(4)
    W2, H2 = HW + 2 * pad, HH + 2 * pad
    canvas = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    drill = circ(*hole_xy, d.DRILL / 2)
    body = outline & ~drill
    # shadow
    sh = np.zeros((H2, W2), np.uint8)
    sh[pad + px(1.2):pad + px(1.2) + HH, pad + px(0.6):pad + px(0.6) + HW] = body
    sh = cv2.GaussianBlur(sh, (0, 0), px(1.0))
    shadow = Image.new("RGBA", (W2, H2), (0, 0, 0, 255))
    shadow.putalpha(Image.fromarray((sh * 0.45).astype(np.uint8)))
    canvas.alpha_composite(shadow)
    # board edge (thickness)
    edge = Image.new("RGBA", (HW, HH), (150, 132, 80, 255))
    edge.putalpha(Image.fromarray(body))
    canvas.alpha_composite(edge, (pad, pad + px(0.55)))
    # top face
    face = Image.fromarray(top_rgb).convert("RGBA")
    face.putalpha(Image.fromarray(body))
    canvas.alpha_composite(face, (pad, pad))
    # inner wall of the plated hole
    ring = circ(*hole_xy, d.DRILL / 2 + 0.05) & ~circ(hole_xy[0], hole_xy[1] + 0.45, d.DRILL / 2)
    wall = Image.new("RGBA", (HW, HH), (140, 104, 30, 255))
    wall.putalpha(Image.fromarray(ring))
    canvas.alpha_composite(wall, (pad, pad))
    return canvas


def compose(mask_col, silk=None, silk_col="white", gold=None, uv=None, bare=None, hole_xy=HOLE):
    top = np.zeros((HH, HW, 3), np.uint8)
    top[:] = MASK[mask_col]
    # soldermask sheen
    yy = np.linspace(0, 1, HH)[:, None, None]
    top = np.clip(top.astype(float) * (1.03 - 0.06 * yy), 0, 255).astype(np.uint8)
    if bare is not None:
        top = np.where(bare[..., None] > 127, fr4_tex(), top)
    if uv is not None:
        u = np.array(uv).astype(float)
        a = u[..., 3:4] / 255
        top = (top * (1 - a) + u[..., :3] * a).astype(np.uint8)
    if silk is not None:
        sm = cv2.GaussianBlur(silk, (0, 0), 0.6)[..., None] / 255
        top = (top * (1 - sm) + np.array(SILK[silk_col]) * sm).astype(np.uint8)
    pad_ring = circ(*hole_xy, d.PAD / 2)
    g = pad_ring if gold is None else (gold | pad_ring)
    gm = cv2.GaussianBlur(g, (0, 0), 0.5)[..., None] / 255
    top = (top * (1 - gm) + gold_tex() * gm).astype(np.uint8)
    return top


def bar_pin_overlay(img, pad):
    """Draw a simple locking bar pin glued into the pin zone (back view)."""
    z = L.PIN_ZONE
    dr = ImageDraw.Draw(img)
    x0, x1 = px(z[0] + 2.5) + pad, px(z[2] - 2.5) + pad
    yc = px((z[1] + z[3]) / 2) + pad
    # base plate
    dr.rounded_rectangle([x0, yc - px(2.2), x1, yc + px(2.2)], radius=px(1.2), fill=(168, 170, 176, 255),
                         outline=(110, 112, 118, 255), width=2)
    for k in range(3):
        hx = x0 + (x1 - x0) * (k + 1) / 4
        dr.ellipse([hx - px(0.6), yc - px(0.6), hx + px(0.6), yc + px(0.6)], fill=(90, 92, 96, 255))
    # needle + clasp
    dr.line([x0 + px(1), yc - px(1.0), x1 - px(2.5), yc - px(1.6)], fill=(215, 216, 220, 255), width=px(0.7))
    dr.rounded_rectangle([x1 - px(4.0), yc - px(2.8), x1 - px(0.6), yc + px(0.4)], radius=px(0.8),
                         fill=(196, 198, 204, 255), outline=(110, 112, 118, 255), width=2)
    # hinge
    dr.ellipse([x0 - px(0.4), yc - px(2.2), x0 + px(2.6), yc + px(0.8)], fill=(196, 198, 204, 255),
               outline=(110, 112, 118, 255), width=2)


def render_all():
    out = {}
    for v in d.VARIANTS:
        uv = L.crop(d.front_color(v))
        out[f"{v}-front"] = side(compose("white", uv=uv), OUTL, HOLE)
        bs = L.back_silk(v)
        bo = L.back_outline
        bh = (L.WC - HOLE[0], HOLE[1])
        bare = L.zone_mask(0.0)
        back = side(compose("white", silk=bs, silk_col="black", bare=bare, hole_xy=bh), bo, bh)
        out[f"{v}-back"] = back
        pinned = back.copy()
        bar_pin_overlay(pinned, px(4))
        out[f"{v}-back-pinned"] = pinned
    # plan B
    gold = L.planb_gold()
    out["planB-participant-front"] = side(compose("orange", silk=L.planb_front_silk("participant"), gold=gold), OUTL, HOLE)
    out["planB-organizer-front"] = side(compose("black", silk=L.planb_front_silk("organizer"), gold=gold), OUTL, HOLE)
    return out


if __name__ == "__main__":
    import os
    os.makedirs("mock", exist_ok=True)
    res = render_all()
    for k, im in res.items():
        im.save(f"mock/{k}.png")
        print(k, im.size)

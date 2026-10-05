"""Back-side art, plan-B (no UV) front art, KiCad layer PNGs, outline export, mockups."""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter
import design as d
from design import px, S, W, H, CW, CH, HOLE, PAD, DRILL, F_HEAD, F_BODY

OUT = "out"
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------ crop every layer to the outline's bbox
_ys, _xs = np.nonzero(d.outline_mask)
CX0, CX1, CY0, CY1 = _xs.min(), _xs.max() + 1, _ys.min(), _ys.max() + 1
WC, HC = (CX1 - CX0) / S, (CY1 - CY0) / S          # board size in mm
PWC, PHC = CX1 - CX0, CY1 - CY0                     # in px
HOLE_C = (HOLE[0] - CX0 / S, HOLE[1] - CY0 / S)    # hole centre, cropped coords


def crop(a):
    if isinstance(a, Image.Image):
        return a.crop((CX0, CY0, CX1, CY1))
    return a[CY0:CY1, CX0:CX1].copy()


OUTLINE = crop(d.outline_mask)
# pin zone is centred on the hole's x so the badge hangs/sits straight (same in back view)
# (back-view coords: the hole appears at x = WC - HOLE_C[0] when you look at the back)
PIN_ZONE = (WC - HOLE_C[0] - 17.0, 14.0, WC - HOLE_C[0] + 17.0, 22.0)

# ------------------------------------------------------------ back (as seen from the back)
back_outline = np.fliplr(OUTLINE).copy()


def sketchy_daven_lines(height_mm):
    """Only the dark brown outline strokes of sketchy Daven -> single-colour line art."""
    im = Image.open("daven-pudding/sketchy-daven.png").convert("RGBA")
    im = im.crop(im.getchannel("A").getbbox())
    h = px(height_mm)
    w = round(im.width * h / im.height)
    im = im.resize((w, h), Image.LANCZOS)
    a = np.array(im).astype(int)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    # outline strokes are the darkest, reddish-brown pixels (~ (170,80,60))
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    m = (al > 120) & (lum < 125) & (r > g + 30)
    m = m.astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, d.disc(0.15))
    m = cv2.GaussianBlur(m, (0, 0), 1.0)
    return (m > 110).astype(np.uint8) * 255


def bracket_box(dr, box, arm, w, fill=255):
    x0, y0, x1, y1 = box
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        dr.line([px(cx), px(cy), px(cx + sx * arm), px(cy)], fill=fill, width=px(w))
        dr.line([px(cx), px(cy), px(cx), px(cy + sy * arm)], fill=fill, width=px(w))


def back_silk(v):
    """Back silkscreen (white=ink), drawn as seen when looking at the back."""
    img = Image.new("L", (PWC, PHC), 0)
    dr = ImageDraw.Draw(img)
    cx = WC / 2
    # pin-zone corner brackets (1 mm outside the bare zone)
    z = PIN_ZONE
    bracket_box(dr, (z[0] - 1.0, z[1] - 1.0, z[2] + 1.0, z[3] + 1.0), 3.0, 0.3)
    d.draw_text(img, ((z[0] + z[2]) / 2, z[3] + 3.4), "GLUE THE PIN HERE", F_BODY, 1.35, 255, anchor="ms",
                spacing_mm=0.15)

    # sketchy Daven thumbs-up
    dv = sketchy_daven_lines(22.0)
    dvx, dvy = px(6.5), px(28.5)
    region = np.array(img)
    hgt, wid = dv.shape
    region[dvy:dvy + hgt, dvx:dvx + wid] |= dv
    img = Image.fromarray(region)
    dr = ImageDraw.Draw(img)

    tx = 27.5   # left edge of text block
    if v == "participant":
        # checkbox + "I SHIPPED A GAME!"
        dr.rounded_rectangle([px(tx), px(30.0), px(tx + 4.2), px(34.2)], radius=px(0.6),
                             outline=255, width=px(0.35))
        d.draw_text(img, (tx + 5.4, 32.1 + 1.0), "I SHIPPED", F_HEAD, 2.1, 255)
        d.draw_text(img, (tx + 5.4, 35.9 + 1.0), "A GAME!", F_HEAD, 2.1, 255)
        d.draw_text(img, (tx, 41.0), "a judge ticks the box", F_BODY, 1.3, 255)
        d.draw_text(img, (tx, 43.2), "at Sunday's showcase", F_BODY, 1.3, 255)
    else:
        d.draw_text(img, (tx, 33.1), "THANK YOU", F_HEAD, 2.1, 255)
        d.draw_text(img, (tx, 36.9), "FOR BUILDING", F_HEAD, 2.1, 255)
        d.draw_text(img, (tx, 40.7), "HAVEN!", F_HEAD, 2.1, 255)
        d.draw_text(img, (tx, 43.6), "organizer team, 2026", F_BODY, 1.3, 255)

    d.draw_text(img, (tx, 47.6), "Hack Club Haven", F_BODY, 1.45, 255)
    d.draw_text(img, (tx, 49.9), "Tashkent, 14-15 Nov 2026", F_BODY, 1.3, 255)
    # bottom line
    d.draw_text(img, (cx, 54.2), "haven.hackclub.com/tashkent", F_BODY, 1.35, 255, anchor="ms")
    d.draw_dotted_line(img, (cx, 56.6), ("PCB made by PCBWay", "designed in KiCad"), F_BODY, 1.25, 255,
                       gap_mm=1.2, dot_mm=0.45)
    a = np.array(img)
    # keep silk 0.5 mm inside the board edge and off the pin zone / hole pad
    a &= d.erode(back_outline, 0.6)
    a &= ~zone_mask(0.0)
    a &= ~hole_mask_back(PAD / 2 + 0.4)
    return a


def zone_mask(grow):
    m = Image.new("L", (PWC, PHC), 0)
    z = PIN_ZONE
    ImageDraw.Draw(m).rounded_rectangle([px(z[0] - grow), px(z[1] - grow), px(z[2] + grow), px(z[3] + grow)],
                                        radius=px(1.0 + grow), fill=255)
    return np.array(m)


def hole_mask_back(r):
    return np.fliplr(crop(d.circle_mask(*HOLE, r))).copy()


# ------------------------------------------------------------ plan B front (no UV printing)
def leaves_mask():
    a = (np.array(d.logo_or.getchannel("A")) > 60).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(a)
    w = a.shape[1]
    keep = np.zeros_like(a)
    for i in range(1, n):
        x, y, bw, bh, area = st[i]
        if area > 5000 and (cen[i][0] < 0.14 * w or cen[i][0] > 0.86 * w):
            keep[lab == i] = 255
    c = np.zeros((CH, CW), np.uint8)
    x0, y0 = d.LOGO_POS
    c[y0:y0 + keep.shape[0], x0:x0 + keep.shape[1]] = keep
    return c


def planb_front_silk(v):
    """White silkscreen for the plan-B front: logo (minus leaves), plate frame, role, city."""
    cfg = d.VARIANTS[v]
    logo = d.logo_mask.copy()
    leaves = leaves_mask()
    logo &= ~d.dilate(leaves, 0.05)
    img = Image.fromarray(logo)
    dr = ImageDraw.Draw(img)
    x0, y0, x1, y1 = d.PLATE
    dr.rounded_rectangle([px(x0), px(y0), px(x1), px(y1)], radius=px(d.PLATE_R), outline=255, width=px(0.45))
    cx = (x0 + x1) / 2
    d.draw_text(img, (cx, y0 + 5.6), cfg["role"], F_HEAD, 4.0, 255, anchor="ms", spacing_mm=0.25)
    ly = y1 - 2.3
    dr.line([px(x0 + 9.0), px(ly), px(x1 - 3.0), px(ly)], fill=255, width=px(0.2))
    d.draw_text(img, (x0 + 2.6, ly), "name", F_BODY, 1.5, 255)
    d.draw_dotted_line(img, (cx, d.CITY_Y), cfg["sub"], F_BODY, 1.55, 255)
    # Daven head as a simple filled silhouette is too blobby in one colour -> skip on plan B
    a = np.array(img)
    a &= d.erode(d.outline_mask, 0.6)
    a &= ~d.circle_mask(*HOLE, PAD / 2 + 0.4)
    return crop(a)


def planb_gold():
    """Exposed ENIG gold areas on the plan-B front: the four leaves."""
    return crop(leaves_mask())


# ------------------------------------------------------------ exports
def save_layer(a, name, invert=False):
    """Save a KiCad Image-Converter-ready PNG: black = artwork, white = empty, exact DPI."""
    img = Image.fromarray(255 - a if not invert else a).convert("L")
    img.save(f"{OUT}/{name}.png", dpi=(d.DPI, d.DPI))


def save_rgba(im, name):
    im.save(f"{OUT}/{name}.png", dpi=(d.DPI, d.DPI))


def export_outline():
    pts = d.outline_polygon() - np.array([CX0 / S, CY0 / S])
    pts[:, 0] = pts[:, 0].clip(0, WC)
    pts[:, 1] = pts[:, 1].clip(0, HC)
    W, H = WC, HC
    # SVG (mm)
    path = "M " + " L ".join(f"{x:.3f},{y:.3f}" for x, y in pts) + " Z"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.3f}mm" height="{H:.3f}mm" '
           f'viewBox="0 0 {W:.3f} {H:.3f}">\n<path d="{path}" fill="none" stroke="black" stroke-width="0.1"/>\n</svg>\n')
    open(f"{OUT}/badge-outline.svg", "w").write(svg)
    # DXF R12, units mm, Y flipped (DXF is y-up) -- KiCad flips it back on import
    lines = ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4", "0", "ENDSEC",
             "0", "SECTION", "2", "ENTITIES"]
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        lines += ["0", "LINE", "8", "Edge.Cuts", "10", f"{x1:.4f}", "20", f"{-y1:.4f}", "30", "0",
                  "11", f"{x2:.4f}", "21", f"{-y2:.4f}", "31", "0"]
    lines += ["0", "ENDSEC", "0", "EOF"]
    open(f"{OUT}/badge-outline.dxf", "w").write("\n".join(lines) + "\n")
    return pts


if __name__ == "__main__":
    pts = export_outline()
    print("outline points", len(pts), "bbox", pts.min(0), pts.max(0))
    for v in d.VARIANTS:
        save_rgba(crop(d.front_color(v)), f"UV-front-color-{v}")
        save_layer(back_silk(v), f"B_SilkS-back-{v}")
        save_layer(planb_front_silk(v), f"planB-F_SilkS-front-{v}")
    save_layer(planb_gold(), "planB-F_Cu+F_Mask-gold-leaves")
    print("board mm", WC, HC, "hole", HOLE_C, "pin zone", PIN_ZONE)
    print("ok")

"""Put the PCBWay logo on the back of the Haven Tashkent badges.

PCBWay (Ava Wang, 1 Oct 2026) asked for their logo on the board. This script
redraws the bottom of the back silkscreen as:

        haven.hackclub.com/tashkent  •  designed in KiCad
             PCB made by  [PCBWay logo]

The logo is turned into one-colour silkscreen art:
  - green letters + orange swoosh are merged into one ink layer
  - where the swoosh crosses the "y" the two merge, the way one-colour
    versions of the PCBWay logo are normally printed
  - the swoosh's hairline tail is thickened to PCBWay's 0.15 mm minimum
    silkscreen line, so it doesn't break off in production

Run it from this folder (needs numpy, opencv-python, pillow, scikit-image):

    python3 sponsor_logo.py

It rewrites ../1-kicad-import/B_SilkS-back-participant.png and
B_SilkS-back-organizer.png in place (safe to run more than once: it clears the
bottom band before drawing) and writes a preview of each back to
../3-mockups/back-pcbway-*.png.

Files it uses (next to this script):
  logos/pcbway-logo.png    the PNG from Ava's email ("PCBWay logo.png")
  fonts/Jua-Regular.ttf    the badge's body font (Google Fonts, OFL)
"""
import os
import re
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from skimage.morphology import skeletonize

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "..", "1-kicad-import")
MOCK = os.path.join(HERE, "..", "3-mockups")
LOGO = os.path.join(HERE, "logos", "pcbway-logo.png")
FONT = os.path.join(HERE, "fonts", "Jua-Regular.ttf")

S = 40                     # px per mm (1016 dpi) - same as design.py
DPI = S * 25.4

# ---------------------------------------------------------------- layout (mm, back view)
CLEAR_BAND = (51.6, 58.6)  # old "url" + "PCB made by PCBWay" lines live in here
URL_BASELINE = 53.25
URL_CAP = 1.25
LOGO_LETTER_H = 2.5        # height of the "PCBWay" capitals on the board
LOGO_TOP = 54.25
MADE_BY_CAP = 1.3
MADE_BY_GAP = 1.1          # space between "PCB made by" and the logo
MIN_LINE = 0.18            # thinnest swoosh line (PCBWay minimum is 0.15 mm)
EDGE_KEEP = 0.6            # keep silk this far inside the board edge


def px(v):
    return int(round(v * S))


def disc(r_px):
    r = max(1, int(round(r_px)))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def font(cap_mm):
    """Jua at a given capital-letter height (same rule as design.font)."""
    probe = ImageFont.truetype(FONT, 200)
    b = probe.getbbox("H")
    cap = (b[3] - b[1]) / 200
    return ImageFont.truetype(FONT, max(4, round(px(cap_mm) / cap)))


# ---------------------------------------------------------------- logo -> one-colour mask
def logo_mask(letter_h_mm):
    """Return (mask uint8 0/255, letter_top_px, letter_bottom_px) scaled for the board."""
    im = np.array(Image.open(LOGO).convert("RGBA")).astype(int)
    r, g, b, a = im[..., 0], im[..., 1], im[..., 2], im[..., 3]
    solid = a > 128
    green = solid & (g > r)                      # #1f833b letters
    orange = solid & (r > g)                     # #d36221 swoosh
    ys, xs = np.nonzero(solid)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    green, orange = green[y0:y1, x0:x1], orange[y0:y1, x0:x1]

    # letter height in the source = the "P" stem: tallest green column run in the left 10 %
    gy = np.nonzero(green[:, : green.shape[1] // 10].any(1))[0]
    src_letter_h = gy.max() - gy.min() + 1
    k = px(letter_h_mm) / src_letter_h
    size = (max(1, round(green.shape[1] * k)), max(1, round(green.shape[0] * k)))

    def scale(m):
        s = cv2.resize(m.astype(np.uint8) * 255, size, interpolation=cv2.INTER_AREA)
        return (s > 127).astype(np.uint8) * 255

    G, O = scale(green), scale(orange)

    # thicken only the hairline part of the swoosh: centre line drawn at MIN_LINE width
    skel = skeletonize(O > 0).astype(np.uint8) * 255
    O = O | cv2.dilate(skel, disc(px(MIN_LINE) / 2))

    mask = G | O

    gy = np.nonzero((G > 0)[:, : G.shape[1] // 10].any(1))[0]
    return mask, int(gy.min()), int(gy.max())


# ---------------------------------------------------------------- board outline (back view)
def back_outline(shape):
    svg = open(os.path.join(ART, "badge-outline.svg")).read()
    d = re.search(r'<path d="([^"]+)"', svg).group(1)
    pts = [(float(x) * S, float(y) * S) for x, y in re.findall(r"([-\d.]+),([-\d.]+)", d)]
    m = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    m = np.fliplr(np.array(m)).copy()          # back view = mirrored left/right
    return cv2.erode(m, disc(px(EDGE_KEEP)))


# ---------------------------------------------------------------- draw the new bottom rows
def draw_sponsor_rows(ink):
    """ink: uint8 array, 255 = silkscreen, in back-view coordinates. Modified in place."""
    h, w = ink.shape
    cx = w / 2
    ink[px(CLEAR_BAND[0]):px(CLEAR_BAND[1]), :] = 0

    img = Image.fromarray(ink)
    d = ImageDraw.Draw(img)

    # row 1: url  •  designed in KiCad
    f1 = font(URL_CAP)
    parts = ("haven.hackclub.com/tashkent", "designed in KiCad")
    gap, dot = px(1.3), px(0.45)
    widths = [f1.getlength(p) for p in parts]
    total = sum(widths) + 2 * gap
    x = cx - total / 2
    d.text((x, px(URL_BASELINE)), parts[0], font=f1, fill=255, anchor="ls")
    x += widths[0] + gap
    cy = px(URL_BASELINE - URL_CAP / 2)
    d.ellipse([x - dot / 2, cy - dot / 2, x + dot / 2, cy + dot / 2], fill=255)
    x += gap
    d.text((x, px(URL_BASELINE)), parts[1], font=f1, fill=255, anchor="ls")

    # row 2: "PCB made by" + logo, centred as one group, text sitting on the logo's baseline
    logo, l_top, l_bot = logo_mask(LOGO_LETTER_H)
    f2 = font(MADE_BY_CAP)
    label = "PCB made by"
    lw = f2.getlength(label)
    group = lw + px(MADE_BY_GAP) + logo.shape[1]
    gx = int(round(cx - group / 2))
    oy = px(LOGO_TOP) - l_top                   # logo image y so its letters start at LOGO_TOP
    baseline = oy + l_bot + 1
    d.text((gx, baseline), label, font=f2, fill=255, anchor="ls")
    a = np.array(img)
    lx = int(round(gx + lw + px(MADE_BY_GAP)))
    region = a[oy:oy + logo.shape[0], lx:lx + logo.shape[1]]
    region |= logo[: region.shape[0], : region.shape[1]]
    return a


def preview(ink, path):
    """Back of the badge as it should come out: black silk on white mask, gold pin pad + ring."""
    h, w = ink.shape
    board = back_outline(ink.shape)
    board = cv2.dilate(board, disc(px(EDGE_KEEP)))   # undo the keep-out for the board shape
    out = np.full((h, w, 3), (236, 231, 220), np.uint8)
    out[board > 0] = (250, 250, 247)
    gold = (212, 175, 55)
    pin = Image.new("L", (w, h), 0)
    ImageDraw.Draw(pin).rounded_rectangle([px(11.875), px(14), px(45.875), px(22)], radius=px(0.3), fill=255)
    out[np.array(pin) > 0] = gold
    ring = Image.new("L", (w, h), 0)
    hx = w / S - 27.0                                 # hole x in back view
    ImageDraw.Draw(ring).ellipse([px(hx - 4), px(2), px(hx + 4), px(10)], fill=255)
    ImageDraw.Draw(ring).ellipse([px(hx - 2.15), px(3.85), px(hx + 2.15), px(8.15)], fill=0)
    out[np.array(ring) > 0] = gold
    out[ink > 0] = (25, 25, 25)
    Image.fromarray(out).resize((w // 2, h // 2), Image.LANCZOS).save(path)


def main():
    os.makedirs(MOCK, exist_ok=True)
    for v in ("participant", "organizer"):
        p = os.path.join(ART, f"B_SilkS-back-{v}.png")
        src = np.array(Image.open(p).convert("L"))
        ink = (src < 128).astype(np.uint8) * 255          # black = artwork in the PNG
        ink = draw_sponsor_rows(ink)
        ink &= back_outline(ink.shape)
        Image.fromarray(255 - ink).save(p, dpi=(DPI, DPI))
        preview(ink, os.path.join(MOCK, f"back-pcbway-{v}.png"))
        print("updated", os.path.relpath(p, HERE))


if __name__ == "__main__":
    main()

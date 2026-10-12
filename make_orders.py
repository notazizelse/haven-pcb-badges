"""Build the PCBWay order folders + zips for both badges in one go.

Run from the repo root after plotting Gerbers + drill in KiCad (Step 7):

    python make_orders.py              # folders named with today's date
    python make_orders.py 2026-10-12   # or pick the date

For each badge it makes orders/<date>_<variant>/ containing:
  - every file from that KiCad project's gerber/ folder (Gerbers, drill, job file)
  - TOP_UV-front-color-<variant>.png    the colour print
  - TOP_positioning-<variant>.png       where the print goes
  - TOP_reference-<variant>-front.png   picture of the finished front
  - README_UV-<variant>.txt             notes for PCBWay's engineer
and zips all of it (flat, no subfolders) into orders/<date>_<variant>/<date>_<variant>.zip.

It refuses to run if a Gerber folder is missing a layer, if the drill file is
missing, or if the Gerbers are older than the back-art PNG (= you changed the art
but forgot to re-plot). Standard library only.
"""
import datetime
import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(ROOT, "badge-art")
PRINT = os.path.join(ART, "2-pcbway-color-print")

BADGES = {
    "participant": "haven-tashkent",
    "organizer": "haven-tashkent_organizer",
}
LAYERS = ["F_Cu.gtl", "B_Cu.gbl", "F_Mask.gts", "B_Mask.gbs",
          "F_Silkscreen.gto", "B_Silkscreen.gbo", "Edge_Cuts.gm1"]


def fail(msg):
    print("STOP:", msg)
    sys.exit(1)


def build(variant, project, date):
    gerber = os.path.join(ROOT, project, "gerber")
    if not os.path.isdir(gerber):
        fail(f"{project}/gerber/ not found - plot the Gerbers in KiCad first")
    for layer in LAYERS:
        if not os.path.isfile(os.path.join(gerber, f"{project}-{layer}")):
            fail(f"{project}/gerber/{project}-{layer} is missing - re-plot (Step 7)")
    if not os.path.isfile(os.path.join(gerber, f"{project}.drl")):
        fail(f"{project}/gerber/{project}.drl is missing - click Generate Drill Files (Step 7)")

    back_art = os.path.join(ART, "1-kicad-import", f"B_SilkS-back-{variant}.png")
    gbo = os.path.join(gerber, f"{project}-B_Silkscreen.gbo")
    if os.path.getmtime(gbo) < os.path.getmtime(back_art):
        fail(f"{project} Gerbers are older than B_SilkS-back-{variant}.png - "
             "put the new back art in KiCad and re-plot first")

    extras = {
        f"UV-front-color-{variant}.png": f"TOP_UV-front-color-{variant}.png",
        f"positioning-{variant}-top.png": f"TOP_positioning-{variant}.png",
        f"reference-{variant}-front.png": f"TOP_reference-{variant}-front.png",
        f"README_UV-{variant}.txt": f"README_UV-{variant}.txt",
    }

    name = f"{date}_{variant}"
    out = os.path.join(ROOT, "orders", name)
    if os.path.isdir(out):
        shutil.rmtree(out)                     # rebuilding the same day replaces it
    os.makedirs(out)

    files = []
    for f in sorted(os.listdir(gerber)):
        shutil.copy2(os.path.join(gerber, f), os.path.join(out, f))
        files.append(f)
    for src, dst in extras.items():
        p = os.path.join(PRINT, src)
        if not os.path.isfile(p):
            fail(f"badge-art/2-pcbway-color-print/{src} is missing")
        shutil.copy2(p, os.path.join(out, dst))
        files.append(dst)

    zpath = os.path.join(out, f"{name}.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(out, f), arcname=f)
    print(f"orders/{name}/{name}.zip  ({len(files)} files, {os.path.getsize(zpath) // 1024} KB)")


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    for variant, project in BADGES.items():
        build(variant, project, date)
    print("Upload each zip as its own PCBWay order (Step 9).")


if __name__ == "__main__":
    main()

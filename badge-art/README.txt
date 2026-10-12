HAVEN TASHKENT PCB BADGES - ART PACK
=====================================
Full step-by-step guide: the "Haven Tashkent PCB Badges: Design, KiCad & Ordering Guide" doc.

Board: 55.875 x 59.1 mm, 2 layers, 1.6 mm, ENIG. Every PNG below is exactly the board's
bounding box at 1016 dpi (40 px/mm), so every image lines up with the outline 1:1.

KEY NUMBERS (KiCad coordinates, when the outline is imported at X=100, Y=100)
  Outline top-left ............... (100.00, 100.00)
  Every art footprint goes at .... (127.94, 129.55)   <- centre of the board's bounding box
  Hanging hole footprint ......... (127.00, 106.00)   MountingHole:MountingHole_4.3mm_M4_Pad
  Back pin pad (B.Mask rectangle)  (110.00, 114.00) to (144.00, 122.00), filled

1-kicad-import/
  badge-outline.svg / .dxf ............ Edge.Cuts outline (use SVG; DXF as backup)
  B_SilkS-back-participant.png ........ back silkscreen, participant (drawn as seen from the back)
  B_SilkS-back-organizer.png .......... back silkscreen, organizer
  planB-F_SilkS-front-*.png ........... PLAN B ONLY: front silkscreen if colour printing isn't possible
  planB-F_Cu+F_Mask-gold-leaves.png ... PLAN B ONLY: gold leaves (convert twice: F.Mask and F.Cu)
  In all of these: black = artwork, white = nothing.

2-pcbway-color-print/
  UV-front-color-*.png ................ full-colour front print for PCBWay (transparent = plain white mask)
  reference-*-front.png ............... picture of the finished board, for PCBWay's engineer

3-mockups/ ............................ previews of every side + contact sheets
4-generator/ .......................... Python scripts that made all of this. To rebuild, put the brand-kit
                                        folders fonts/, logos/, daven-pudding/ next to the scripts and run
                                        python3 layers.py && python3 mockup.py && python3 sheets.py
                                        (needs numpy, opencv-python, pillow, scikit-image). Layout numbers are at the top of design.py.
                                        sponsor_logo.py draws the PCBWay logo row on the back (logo in logos/pcbway-logo.png).
                                        Run it on its own (python3 sponsor_logo.py) to update just the two B_SilkS PNGs.

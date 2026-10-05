# Haven Tashkent PCB badges

Die-cut PCB badges for Hack Club Haven Tashkent (14–15 Nov 2026): lime-green **HACKER** for participants,
burnt-umber **ORGANIZER** for the team. 55.9 × 59.1 mm, 2 layers, ENIG, full-colour front printed by PCBWay.

- **Main repo:** GitLab. **Copy:** GitHub (`notazizelse/haven-pcb-badges`) gets every push automatically.
- New here? Read the **Jumpstart guide** doc (linked in the team Hub) before your first change.

| Folder | What's in it |
| --- | --- |
| `haven-tashkent/` | The KiCad 10 project (participant board) |
| `badge-art/1-kicad-import/` | Outline + layer PNGs you import into KiCad |
| `badge-art/2-pcbway-color-print/` | Colour print PNGs + reference images sent with the order |
| `badge-art/3-mockups/` | Previews of every side |
| `badge-art/4-generator/` | Python that draws all the art (`design.py` holds the layout numbers) |
| `orders/` | The exact zip you sent PCBWay for each order |

Key numbers in KiCad (outline imported at X 100, Y 100): art footprints at (127.94, 129.55),
hole `MountingHole_4.3mm_M4_Pad` at (127.00, 106.00), bare pin pad on B.Mask from (110, 114) to (144, 122).

PCB manufacturing sponsored by PCBWay.

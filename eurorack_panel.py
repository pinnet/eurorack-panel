#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Danny Arnold
"""Generate a KiCad 10 Eurorack front-panel board (.kicad_pcb) for a given HP width.

Usage examples
  python eurorack_panel.py 8                      -> eurorack_8hp.kicad_pcb, outline + rail holes
  python eurorack_panel.py 8 --jacks 8 --cols 2   -> plus 8 jack holes in a 2 x 4 grid
  python eurorack_panel.py 12 -o mymodule.kicad_pcb --slots

Standards used (Doepfer A-100, the de-facto Eurorack reference)
  * Panel height 128.5 mm (3U).
  * Width: Doepfer's published panel widths where listed, otherwise HP * 5.08 - 0.3 mm
    (panels are slightly under nominal so neighbours fit side by side).
  * Rail mounting holes: centres 3.0 mm from top and bottom edges, 7.5 mm from the
    left edge; panels of 10 HP or more get a second hole per rail at 7.5 + (HP - 3) * 5.08 mm.
    Default 3.2 mm round holes (M3 clearance); --slots makes them 3.2 x 5.2 mm ovals for slack.

Jack holes default to 6.2 mm (3.5 mm Thonkiconn PJ398SM / PJ301M-12 nut clearance).
Jacks are laid out as an evenly spaced grid inside the area between the rails.
Pure Python, no KiCad install needed; open the output with KiCad's PCB editor.
MIT licence - see LICENSE.
"""

from __future__ import annotations

import argparse
import math
import sys
import uuid

PANEL_HEIGHT = 128.5
HP_PITCH = 5.08
RAIL_HOLE_Y = 3.0          # from top / bottom edge
RAIL_HOLE_X = 7.5          # from left edge
JACK_ZONE = (8.0, 120.5)   # y range (from top edge) jacks are distributed within

DOEPFER_WIDTHS = {
    1: 5.00, 2: 9.80, 4: 20.00, 6: 30.00, 8: 40.30, 10: 50.50, 12: 60.60,
    14: 70.80, 16: 80.90, 18: 91.30, 20: 101.30, 21: 106.30, 22: 111.40,
    28: 141.90, 42: 213.00,
}


def panel_width(hp: int) -> float:
    return DOEPFER_WIDTHS.get(hp, round(hp * HP_PITCH - 0.3, 2))


def rail_hole_xs(hp: int, width: float) -> list[float]:
    if hp < 3:  # too narrow for the 7.5 mm offset; centre it
        return [width / 2]
    xs = [RAIL_HOLE_X]
    if hp >= 10:
        xs.append(RAIL_HOLE_X + (hp - 3) * HP_PITCH)
    return xs


def _u() -> str:
    return str(uuid.uuid4())


def _f(v: float) -> str:
    return f"{round(v, 4):g}"


FONT = """(effects
\t\t\t\t(font
\t\t\t\t\t(size 1 1)
\t\t\t\t\t(thickness 0.15)
\t\t\t\t)
\t\t\t)"""


def edge_line(a, b) -> str:
    return f"""\t(gr_line
\t\t(start {_f(a[0])} {_f(a[1])})
\t\t(end {_f(b[0])} {_f(b[1])})
\t\t(stroke
\t\t\t(width 0.05)
\t\t\t(type default)
\t\t)
\t\t(layer "Edge.Cuts")
\t\t(uuid "{_u()}")
\t)
"""


def hole_footprint(name: str, ref: str, value: str, x: float, y: float,
                   dia: float, slot_len: float | None = None) -> str:
    if slot_len:
        pad = f"""\t\t(pad "" np_thru_hole oval
\t\t\t(at 0 0)
\t\t\t(size {_f(slot_len)} {_f(dia)})
\t\t\t(drill oval {_f(slot_len)} {_f(dia)})
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(uuid "{_u()}")
\t\t)
"""
        crt = max(slot_len, dia) / 2 + 0.5
    else:
        pad = f"""\t\t(pad "" np_thru_hole circle
\t\t\t(at 0 0)
\t\t\t(size {_f(dia)} {_f(dia)})
\t\t\t(drill {_f(dia)})
\t\t\t(layers "*.Cu" "*.Mask")
\t\t\t(uuid "{_u()}")
\t\t)
"""
        crt = dia / 2 + 0.5
    off = crt + 1.0
    return f"""\t(footprint "eurorack:{name}"
\t\t(layer "F.Cu")
\t\t(uuid "{_u()}")
\t\t(at {_f(x)} {_f(y)})
\t\t(property "Reference" "{ref}"
\t\t\t(at 0 {_f(-off)} 0)
\t\t\t(layer "F.Fab")
\t\t\t(uuid "{_u()}")
\t\t\t{FONT}
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at 0 {_f(off)} 0)
\t\t\t(layer "F.Fab")
\t\t\t(hide yes)
\t\t\t(uuid "{_u()}")
\t\t\t{FONT}
\t\t)
\t\t(attr exclude_from_pos_files exclude_from_bom)
\t\t(fp_circle
\t\t\t(center 0 0)
\t\t\t(end {_f(crt)} 0)
\t\t\t(stroke
\t\t\t\t(width 0.05)
\t\t\t\t(type solid)
\t\t\t)
\t\t\t(fill no)
\t\t\t(layer "F.CrtYd")
\t\t\t(uuid "{_u()}")
\t\t)
{pad}\t)
"""


def dimension(x0, y0, y1, label) -> str:
    did = _u()
    return f"""\t(dimension
\t\t(type orthogonal)
\t\t(layer "Dwgs.User")
\t\t(uuid "{did}")
\t\t(pts
\t\t\t(xy {_f(x0)} {_f(y1)}) (xy {_f(x0)} {_f(y0)})
\t\t)
\t\t(height -8)
\t\t(orientation 1)
\t\t(format
\t\t\t(prefix "")
\t\t\t(suffix "")
\t\t\t(units 3)
\t\t\t(units_format 0)
\t\t\t(precision 4)
\t\t\t(suppress_zeroes yes)
\t\t)
\t\t(style
\t\t\t(thickness 0.1)
\t\t\t(arrow_length 1.27)
\t\t\t(text_position_mode 0)
\t\t\t(arrow_direction outward)
\t\t\t(extension_height 0.58642)
\t\t\t(extension_offset 0.5)
\t\t\t(keep_text_aligned yes)
\t\t)
\t\t(gr_text "{label}"
\t\t\t(at {_f(x0 - 8.8)} {_f((y0 + y1) / 2)} 90)
\t\t\t(layer "Dwgs.User")
\t\t\t(uuid "{did}")
\t\t\t{FONT}
\t\t)
\t)
"""


def note(x, y, text) -> str:
    return f"""\t(gr_text "{text}"
\t\t(at {_f(x)} {_f(y)} 0)
\t\t(layer "Dwgs.User")
\t\t(uuid "{_u()}")
\t\t{FONT}
\t)
"""


HEADER = """(kicad_pcb
\t(version 20260206)
\t(generator "eurorack_panel.py")
\t(generator_version "10.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A4")
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1")
\t\t(23 "Eco2.User" user "User.Eco2")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t)
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t)
\t(net 0 "")
"""


def build(hp: int, jacks: int, cols: int | None, jack_hole: float,
          rail_hole: float, slots: bool, ox: float, oy: float) -> tuple[str, list[str]]:
    w, h = panel_width(hp), PANEL_HEIGHT
    warnings: list[str] = []
    x1, y1 = ox + w, oy + h
    out = [HEADER]
    for a, b in [((ox, oy), (x1, oy)), ((x1, oy), (x1, y1)),
                 ((x1, y1), (ox, y1)), ((ox, y1), (ox, oy))]:
        out.append(edge_line(a, b))

    slot_len = rail_hole + 2.0 if slots else None
    n = 0
    for y in (RAIL_HOLE_Y, h - RAIL_HOLE_Y):
        for x in rail_hole_xs(hp, w):
            n += 1
            out.append(hole_footprint("RailHole_M3", f"H{n}", f"rail hole {rail_hole}mm",
                                      ox + x, oy + y, rail_hole, slot_len))

    if jacks:
        if cols is None:
            max_cols = max(1, min(jacks, int(w // 12)))  # ~12 mm per column is comfortable
            cols = math.ceil(jacks / math.ceil(jacks / max_cols))  # balance the grid
        rows = math.ceil(jacks / cols)
        top, bot = JACK_ZONE
        row_pitch = (bot - top) / rows
        col_pitch = w / cols
        if col_pitch < 9.5:
            warnings.append(f"column pitch {col_pitch:.1f} mm is tight for 3.5 mm jack nuts (aim for >= 9.5 mm)")
        if row_pitch < 9.5:
            warnings.append(f"row pitch {row_pitch:.1f} mm is tight for 3.5 mm jack nuts (aim for >= 9.5 mm)")
        k = 0
        for r in range(rows):
            for c in range(cols):
                if k >= jacks:
                    break
                k += 1
                out.append(hole_footprint("Jack_3.5mm_PanelHole", f"J{k}",
                                          f"3.5mm jack hole {jack_hole}mm",
                                          ox + (c + 0.5) * col_pitch,
                                          oy + top + (r + 0.5) * row_pitch, jack_hole))

    out.append(dimension(ox, oy, y1, f"{h:g}"))
    out.append(note(ox + w / 2, oy - 4, f"{hp}HP Eurorack panel {w:g} x {h:g} mm"))
    out.append("\t(embedded_fonts no)\n)\n")
    return "".join(out), warnings


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Generate a KiCad Eurorack front panel for a given HP.")
    p.add_argument("hp", type=int, help="panel width in HP (1 HP = 5.08 mm)")
    p.add_argument("-o", "--output", help="output .kicad_pcb (default eurorack_<hp>hp.kicad_pcb)")
    p.add_argument("--jacks", type=int, default=0, help="number of 3.5 mm jack holes (default 0)")
    p.add_argument("--cols", type=int, help="jack columns (default: fit to width)")
    p.add_argument("--jack-hole", type=float, default=6.2, help="jack hole diameter mm (default 6.2)")
    p.add_argument("--rail-hole", type=float, default=3.2, help="rail hole diameter mm (default 3.2)")
    p.add_argument("--slots", action="store_true", help="oval rail slots instead of round holes")
    p.add_argument("--origin", type=float, nargs=2, default=(60.0, 52.0), metavar=("X", "Y"),
                   help="top-left corner position on the sheet, mm (default 60 52)")
    a = p.parse_args(argv)
    if not 1 <= a.hp <= 104:
        p.error("hp must be between 1 and 104")
    text, warnings = build(a.hp, a.jacks, a.cols, a.jack_hole, a.rail_hole, a.slots, *a.origin)
    path = a.output or f"eurorack_{a.hp}hp.kicad_pcb"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"wrote {path}: {a.hp}HP, {panel_width(a.hp):g} x {PANEL_HEIGHT:g} mm, {a.jacks} jack(s)")
    for w in warnings:
        print("warning:", w, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

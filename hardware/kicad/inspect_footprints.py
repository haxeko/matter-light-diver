#!/usr/bin/env python3
"""In courtyard bbox (tuong doi goc footprint) va vi tri pad cua moi footprint dung trong design_db."""
import os, sys
import pcbnew
from pcbnew import ToMM
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design_db as db
KICAD_FP = "/usr/share/kicad/footprints"
DRIVER_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib", "driver.pretty")

def load(fpid):
    lib, name = fpid.split(":")
    path = DRIVER_LIB if lib == "driver" else os.path.join(KICAD_FP, lib + ".pretty")
    return pcbnew.FootprintLoad(path, name)

def crtyd_bbox(fp):
    xs, ys = [], []
    for g in fp.GraphicalItems():
        if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            bb = g.GetBoundingBox()
            xs += [ToMM(bb.GetLeft()), ToMM(bb.GetRight())]; ys += [ToMM(bb.GetTop()), ToMM(bb.GetBottom())]
    if not xs:
        bb = fp.GetBoundingBox(False, False)
        xs = [ToMM(bb.GetLeft()), ToMM(bb.GetRight())]; ys = [ToMM(bb.GetTop()), ToMM(bb.GetBottom())]
    return min(xs), min(ys), max(xs), max(ys)

seen = set()
for c in db.C:
    if c["fp"] in seen:
        continue
    seen.add(c["fp"])
    fp = load(c["fp"])
    if fp is None:
        print("MISSING", c["fp"]); continue
    x0, y0, x1, y1 = crtyd_bbox(fp)
    pads = [(p.GetNumber(), round(ToMM(p.GetPosition().x), 2), round(ToMM(p.GetPosition().y), 2)) for p in fp.Pads()]
    pads_s = " ".join(f"{n}@({x},{y})" for n, x, y in pads[:12]) + (" ..." if len(pads) > 12 else "")
    print(f"{c['fp']:75s} crtyd x[{x0:6.2f},{x1:6.2f}] y[{y0:6.2f},{y1:6.2f}] size {x1-x0:5.2f}x{y1-y0:5.2f} | {pads_s}")

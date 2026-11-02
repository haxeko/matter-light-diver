#!/usr/bin/env python3
"""
make_footprints.py - Sinh cac footprint rieng cua du an vao lib/driver.pretty (KiCad 7).

  - ESP32-C6-MINI-1 : chuyen tu footprint thu vien KiCad moi (format 2026) ve KiCad 7
  - Transformer_PQ20-20_5+5, CM_Choke_UU9.8, CP_Radial_D10mm_L20mm_Horizontal,
    Fuse_2410_6032Metric, Pads_1x04_P2.54mm
Chay:  python3 make_footprints.py [duong_dan_ESP32-C6-MINI-1.kicad_mod]
"""
import os
import re
import sys
import pcbnew
from pcbnew import VECTOR2I, FromMM

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib", "driver.pretty")
os.makedirs(LIB, exist_ok=True)
IO = pcbnew.PCB_PLUGIN()


def mm(x, y):
    return VECTOR2I(FromMM(x), FromMM(y))


def new_fp(name, smd=True, descr=""):
    fp = pcbnew.FOOTPRINT(None)
    fp.SetFPID(pcbnew.LIB_ID("driver", name))
    fp.SetReference("REF**")
    fp.SetValue(name)
    fp.SetDescription(descr)
    fp.SetAttributes(pcbnew.FP_SMD if smd else pcbnew.FP_THROUGH_HOLE)
    fp.Reference().SetPosition(mm(0, -1))
    fp.Value().SetPosition(mm(0, 1))
    fp.Value().SetLayer(pcbnew.F_Fab)
    return fp


def pad_smd(fp, num, x, y, w, h, shape="rect", rot=0.0, rr=0.0):
    p = pcbnew.PAD(fp)
    p.SetNumber(str(num))
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    if shape == "roundrect":
        p.SetShape(pcbnew.PAD_SHAPE_ROUNDRECT)
        p.SetRoundRectRadiusRatio(rr if rr else 0.25)
    elif shape == "circle":
        p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    elif shape == "oval":
        p.SetShape(pcbnew.PAD_SHAPE_OVAL)
    else:
        p.SetShape(pcbnew.PAD_SHAPE_RECT)
    p.SetSize(mm(w, h))
    p.SetPosition(mm(x, y))
    p.SetOrientationDegrees(rot)
    p.SetLayerSet(pcbnew.PAD.SMDMask())
    p.SetLocalCoord()
    fp.Add(p)
    return p


def pad_tht(fp, num, x, y, dia, drill, shape="circle", w=None, h=None):
    p = pcbnew.PAD(fp)
    p.SetNumber(str(num))
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    if shape == "rect":
        p.SetShape(pcbnew.PAD_SHAPE_RECT)
    elif shape == "oval":
        p.SetShape(pcbnew.PAD_SHAPE_OVAL)
    else:
        p.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    p.SetSize(mm(w or dia, h or dia))
    p.SetDrillSize(mm(drill, drill))
    p.SetPosition(mm(x, y))
    p.SetLayerSet(pcbnew.PAD.PTHMask())
    p.SetLocalCoord()
    fp.Add(p)
    return p


def line(fp, x1, y1, x2, y2, layer=pcbnew.F_SilkS, width=0.12):
    s = pcbnew.FP_SHAPE(fp)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(mm(x1, y1))
    s.SetEnd(mm(x2, y2))
    s.SetLayer(layer)
    s.SetWidth(FromMM(width))
    s.SetLocalCoord()
    fp.Add(s)


def rect(fp, x1, y1, x2, y2, layer=pcbnew.F_SilkS, width=0.12):
    line(fp, x1, y1, x2, y1, layer, width)
    line(fp, x2, y1, x2, y2, layer, width)
    line(fp, x2, y2, x1, y2, layer, width)
    line(fp, x1, y2, x1, y1, layer, width)


def circle(fp, cx, cy, r, layer=pcbnew.F_SilkS, width=0.12):
    s = pcbnew.FP_SHAPE(fp)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetStart(mm(cx, cy))
    s.SetEnd(mm(cx + r, cy))
    s.SetLayer(layer)
    s.SetWidth(FromMM(width))
    s.SetLocalCoord()
    fp.Add(s)


def save(fp):
    IO.FootprintSave(LIB, fp)
    print("saved", fp.GetFPID().GetLibItemName())


# ------------------------------------------------------------------ ESP32-C6-MINI-1 (convert)
def esp32c6(src):
    txt = open(src, encoding="utf-8").read()
    fp = new_fp("ESP32-C6-MINI-1", True, "ESP32-C6-MINI-1 module 13.2x16.6 mm, pad layout from KiCad library (converted to KiCad 7)")
    n = 0
    for m in re.finditer(r'\(pad "([^"]+)" (smd|thru_hole) (\w+)\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s*\(size ([-\d.]+) ([-\d.]+)\)', txt):
        num, kind, shape, x, y, rot, w, h = m.groups()
        pad_smd(fp, num, float(x), float(y), float(w), float(h), "roundrect" if shape == "roundrect" else "rect", float(rot or 0))
        n += 1
    for m in re.finditer(r'\(fp_line\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*\(stroke\s*\(width ([\d.]+)\)[^()]*(?:\([^()]*\))?\s*\)\s*\(layer "([^"]+)"\)', txt):
        x1, y1, x2, y2, w, lay = m.groups()
        layer = {"F.SilkS": pcbnew.F_SilkS, "F.Fab": pcbnew.F_Fab}.get(lay)     # bo courtyard goc (keepout 43x32 mm)
        if layer is not None:
            line(fp, float(x1), float(y1), float(x2), float(y2), layer, float(w))
    # courtyard = than module 13.2 x 16.6 mm (+0.25); phan anten: y -10.7 .. -5.6 (phia -y)
    rect(fp, -6.85, -10.95, 6.85, 6.15, pcbnew.F_CrtYd, 0.05)
    rect(fp, -6.6, -10.7, 6.6, 5.9, pcbnew.F_Fab, 0.1)
    line(fp, -6.6, -5.6, 6.6, -5.6, pcbnew.F_Fab, 0.1)
    for m in re.finditer(r'\(fp_rect\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*\(stroke\s*\(width ([\d.]+)\)[^()]*(?:\([^()]*\))?\s*\)\s*(?:\(fill[^)]*\)\s*)?\(layer "([^"]+)"\)', txt):
        x1, y1, x2, y2, w, lay = m.groups()
        layer = {"F.SilkS": pcbnew.F_SilkS, "F.CrtYd": pcbnew.F_CrtYd, "F.Fab": pcbnew.F_Fab}.get(lay)
        if layer is not None:
            rect(fp, float(x1), float(y1), float(x2), float(y2), layer, float(w))
    print("ESP32-C6-MINI-1: %d pads converted" % n)
    save(fp)


# ------------------------------------------------------------------ PQ20/20 transformer, 5+5 pins
def pq2020():
    # Bobbin PQ20/20 horizontal: 2 rows of 5 pins, pitch 4.0 mm, row spacing 15.2 mm (xac nhan voi bobbin thuc te)
    fp = new_fp("Transformer_PQ20-20_5+5", False, "PQ20/20 horizontal bobbin 5+5 pins, pitch 4.0 mm, rows 15.2 mm, body 22 x 20.5 mm - verify with bobbin drawing")
    pitch, rowsp = 4.0, 15.2
    for i in range(5):
        y = (i - 2) * pitch
        pad_tht(fp, i + 1, -rowsp / 2, y, 2.2, 1.2, "rect" if i == 0 else "circle")     # so cap (trai)
        pad_tht(fp, 10 - i, rowsp / 2, y, 2.2, 1.2)                                       # thu cap (phai): 6..10
    rect(fp, -10.25, -11.0, 10.25, 11.0, pcbnew.F_SilkS)
    rect(fp, -10.75, -11.5, 10.75, 11.5, pcbnew.F_CrtYd, 0.05)
    rect(fp, -10.25, -11.0, 10.25, 11.0, pcbnew.F_Fab, 0.1)
    line(fp, 0, -11.0, 0, 11.0, pcbnew.F_SilkS)      # danh dau hang rao cach ly qua giua bien ap
    save(fp)


# ------------------------------------------------------------------ CM choke UU9.8
def uu98():
    # 4 pins: winding A = 1-2 (left), winding B = 3-4 (right); pin spacing 7.0 (y) x 10.0 (x)
    fp = new_fp("CM_Choke_UU9.8", False, "UU9.8 common-mode choke, 4 pins 10.0 x 7.0 mm, body 12.5 x 10.5 mm - verify with part drawing")
    pad_tht(fp, 1, -5.0, -3.5, 2.0, 1.1, "rect")
    pad_tht(fp, 2, -5.0, 3.5, 2.0, 1.1)
    pad_tht(fp, 3, 5.0, -3.5, 2.0, 1.1)
    pad_tht(fp, 4, 5.0, 3.5, 2.0, 1.1)
    rect(fp, -6.25, -5.25, 6.25, 5.25, pcbnew.F_SilkS)
    rect(fp, -6.75, -5.75, 6.75, 5.75, pcbnew.F_CrtYd, 0.05)
    rect(fp, -6.25, -5.25, 6.25, 5.25, pcbnew.F_Fab, 0.1)
    save(fp)


# ------------------------------------------------------------------ horizontal radial electrolytic D10 L20
def cp_horizontal():
    fp = new_fp("CP_Radial_D10mm_L20mm_Horizontal", False, "Radial electrolytic D10 x L20 mm lying flat, leads bent 90 deg, pitch 5.0 mm; body extends +x from the pads")
    pad_tht(fp, 1, 0.0, -2.5, 2.0, 1.0, "rect")    # +
    pad_tht(fp, 2, 0.0, 2.5, 2.0, 1.0)             # -
    rect(fp, 2.0, -5.0, 22.5, 5.0, pcbnew.F_SilkS)
    line(fp, 2.0, -5.0, 2.0, 5.0, pcbnew.F_SilkS, 0.3)
    rect(fp, -1.5, -5.5, 23.0, 5.5, pcbnew.F_CrtYd, 0.05)
    rect(fp, 2.0, -5.0, 22.5, 5.0, pcbnew.F_Fab, 0.1)
    save(fp)


# ------------------------------------------------------------------ Fuse 2410 (6.1 x 2.6 mm)
def fuse2410():
    fp = new_fp("Fuse_2410_6032Metric", True, "SMD fuse 2410 (6.1 x 2.6 mm), e.g. Littelfuse 0463 / Hollyland 6125")
    pad_smd(fp, 1, -2.7, 0, 1.8, 3.0)
    pad_smd(fp, 2, 2.7, 0, 1.8, 3.0)
    rect(fp, -3.2, -1.5, 3.2, 1.5, pcbnew.F_Fab, 0.1)
    line(fp, -1.5, -1.6, 1.5, -1.6, pcbnew.F_SilkS)
    line(fp, -1.5, 1.6, 1.5, 1.6, pcbnew.F_SilkS)
    rect(fp, -3.9, -1.8, 3.9, 1.8, pcbnew.F_CrtYd, 0.05)
    save(fp)


# ------------------------------------------------------------------ 1x4 pads 2.54 mm (USB programming pads)
def pads1x4():
    fp = new_fp("Pads_1x04_P2.54mm", True, "4 SMD pads 2.54 mm pitch for pogo pins / soldered wires")
    for i in range(4):
        pad_smd(fp, i + 1, (i - 1.5) * 2.54, 0, 1.8, 2.2, "roundrect")
    rect(fp, -5.4, -1.5, 5.4, 1.5, pcbnew.F_SilkS)
    rect(fp, -5.6, -1.7, 5.6, 1.7, pcbnew.F_CrtYd, 0.05)
    save(fp)


# ------------------------------------------------------------------ pad han day (AC vao / LED ra)
def wirepads(name, n, pitch, drill, dia, descr):
    fp = new_fp(name, False, descr)
    for i in range(n):
        pad_tht(fp, i + 1, (i - (n - 1) / 2) * pitch, 0, dia, drill, "rect" if i == 0 else "circle")
    w = (n - 1) * pitch / 2 + dia / 2 + 0.6
    rect(fp, -w, -dia / 2 - 0.6, w, dia / 2 + 0.6, pcbnew.F_SilkS)
    rect(fp, -w - 0.25, -dia / 2 - 0.85, w + 0.25, dia / 2 + 0.85, pcbnew.F_CrtYd, 0.05)
    save(fp)


if __name__ == "__main__":
    wirepads("WirePads_1x02_P5.08mm", 2, 5.08, 1.5, 3.0, "2 THT pads for mains wires 0.75 sqmm, pitch 5.08 mm")
    wirepads("WirePads_1x03_P3.81mm", 3, 3.81, 1.2, 2.4, "3 THT pads for LED wires 0.5 sqmm, pitch 3.81 mm")
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "lib", "src", "ESP32-C6-MINI-1_kicad10.kicad_mod")
    if os.path.exists(src):
        esp32c6(src)
    else:
        print("ESP32-C6-MINI-1 source footprint not found:", src)
    pq2020()
    uu98()
    cp_horizontal()
    fuse2410()
    pads1x4()
    print("done ->", LIB)

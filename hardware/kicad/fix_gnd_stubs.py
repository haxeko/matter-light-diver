#!/usr/bin/env python3
"""
fix_gnd_stubs.py - Noi cac pad GND (GND_P/GND_S) con ho bang via stub xuong vung dong lop kia.

Voi moi pad GND SMD bi DRC bao "unconnected": thu lan luot cac vi tri via quanh pad (8 huong, 2 khoang cach),
them track ngan tu tam pad toi via, do lai vung dong, chay DRC; giu lai neu khong phat sinh vi pham moi va
so muc 'unconnected_items' giam, nguoc lai go bo va thu vi tri khac.
Chay: python3 fix_gnd_stubs.py [file.kicad_pcb]
"""
import math
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "matter_cct_driver.kicad_pcb")
REP = os.path.join(HERE, "drc_tmp_stub.txt")
BAD = ("clearance", "hole_clearance", "items_not_allowed", "via_dangling", "track_dangling",
       "copper_edge_clearance", "shorting_items", "holes_co_located")
GND_NETS = ("GND_S", "GND_P")
VIA_DIA, VIA_DRILL, TRACK_W = 0.6, 0.3, 0.3
HOLE_GAP = 0.25          # khoang cach lo-lo toi thieu (DRC chay tu Python khong kiem tra lo-lo cung net)


def hole_list(board):
    """[(x, y, duong kinh lo)] cua moi via va pad xuyen lo (mm)"""
    out = []
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            out.append((pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y), pcbnew.ToMM(t.GetDrillValue())))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSizeX() > 0:
                out.append((pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y), pcbnew.ToMM(max(p.GetDrillSizeX(), p.GetDrillSizeY()))))
    return out


def hole_ok(holes, x, y):
    for hx, hy, hd in holes:
        if ((hx - x) ** 2 + (hy - y) ** 2) ** 0.5 < VIA_DRILL / 2 + hd / 2 + HOLE_GAP:
            return False
    return True


def drc(board):
    pcbnew.WriteDRCReport(board, REP, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(REP).read()
    kinds = {}
    for k in re.findall(r"^\[([a-z_]+)\]", txt, re.M):
        kinds[k] = kinds.get(k, 0) + 1
    return kinds, txt


def unconnected_gnd_pads(txt):
    seen, out = set(), []
    for b in re.split(r"\n(?=\[)", txt):
        if not b.startswith("[unconnected_items]"):
            continue
        for m in re.finditer(r"@\(([-\d.]+) mm, ([-\d.]+) mm\): Pad (\S+) \[(GND_[SP])\] of (\S+) on (\S+)", b):
            key = (m.group(5), m.group(3), m.group(1), m.group(2))
            if key not in seen:
                seen.add(key)
                out.append(dict(ref=m.group(5), num=m.group(3), x=float(m.group(1)), y=float(m.group(2)),
                                net=m.group(4), layer=m.group(6)))
    return out


def find_pad(board, item):
    fp = board.FindFootprintByReference(item["ref"])
    if fp is None:
        return None
    for p in fp.Pads():
        if p.GetNumber() == item["num"] and abs(pcbnew.ToMM(p.GetPosition().x) - item["x"]) < 0.05 \
                and abs(pcbnew.ToMM(p.GetPosition().y) - item["y"]) < 0.05:
            return p
    return None


def mm(x):
    return int(round(x * 1e6))


def main():
    board = pcbnew.LoadBoard(PCB)
    kinds, txt = drc(board)
    base_bad = sum(kinds.get(k, 0) for k in BAD)
    cur = kinds.get("unconnected_items", 0)
    print("bat dau: unconnected %d, vi pham khac %d" % (cur, base_bad))
    todo = unconnected_gnd_pads(txt)
    print("pad GND can noi:", len(todo))
    added = 0
    holes = hole_list(board)
    for item in todo:
        pad = find_pad(board, item)
        if pad is None or pad.GetDrillSizeX() > 0:          # bo qua pad xuyen lo
            continue
        layer = pcbnew.F_Cu if item["layer"] == "F.Cu" else pcbnew.B_Cu
        net = board.GetNetcodeFromNetname(item["net"])
        sx, sy = pcbnew.ToMM(pad.GetSizeX()), pcbnew.ToMM(pad.GetSizeY())
        ok = False
        for extra in (0.0, 0.3, 0.6):
            for k in range(8):
                a = k * math.pi / 4
                dx, dy = math.cos(a), math.sin(a)
                # khoang cach tu tam pad: nua canh pad theo huong + clearance 0.25 + ban kinh via + extra
                half = abs(dx) * sx / 2 + abs(dy) * sy / 2
                d = half + 0.25 + VIA_DIA / 2 + extra
                vx, vy = item["x"] + dx * d, item["y"] + dy * d
                vx, vy = round(vx * 8) / 8, round(vy * 8) / 8            # bam luoi 0.125 mm
                if not hole_ok(holes, vx, vy):
                    continue
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(mm(item["x"]), mm(item["y"]))); tr.SetEnd(pcbnew.VECTOR2I(mm(vx), mm(vy)))
                tr.SetWidth(mm(TRACK_W)); tr.SetLayer(layer); tr.SetNetCode(net); board.Add(tr)
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy))); v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetWidth(mm(VIA_DIA)); v.SetDrill(mm(VIA_DRILL)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetNetCode(net); board.Add(v)
                pcbnew.ZONE_FILLER(board).Fill(board.Zones())
                kinds, txt2 = drc(board)
                bad = sum(kinds.get(k, 0) for k in BAD)
                unc = kinds.get("unconnected_items", 0)
                if bad <= base_bad and unc < cur:
                    cur = unc; ok = True; added += 1
                    holes.append((vx, vy, VIA_DRILL))
                    print("  %s.%s %s: via (%.3f, %.3f) -> unconnected %d" % (item["ref"], item["num"], item["net"], vx, vy, cur))
                    break
                board.Remove(tr); board.Remove(v)
            if ok:
                break
        if not ok:
            print("  %s.%s %s: khong tim duoc vi tri via" % (item["ref"], item["num"], item["net"]))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    kinds, txt = drc(board)
    print("ket thuc: them %d via stub, unconnected %d, vi pham khac %d" % (added, kinds.get("unconnected_items", 0), sum(kinds.get(k, 0) for k in BAD)))
    if os.path.exists(REP):
        os.remove(REP)


if __name__ == "__main__":
    main()

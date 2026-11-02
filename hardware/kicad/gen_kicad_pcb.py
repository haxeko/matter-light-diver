#!/usr/bin/env python3
"""
gen_kicad_pcb.py - Sinh file PCB KiCad (matter_cct_driver.kicad_pcb) tu design_db.py bang API pcbnew (KiCad 7).

Buoc: tao board -> nap footprint (thu vien KiCad + lib/driver.pretty) -> gan net -> dat linh kien theo floorplan
      -> vien board 30x90 mm bo tron, ranh phay cach ly -> vung keepout (anten, hang rao) -> vung dong GND
      -> (tuy chon) di day bang router noi bo -> luu .kicad_pcb + .kicad_pro + fp-lib-table -> bao cao DRC.
Chay: python3 gen_kicad_pcb.py [--route] [--no-drc]
"""
import json
import os
import sys

import pcbnew
from pcbnew import VECTOR2I, FromMM

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design_db as db  # noqa: E402

KICAD_FP = "/usr/share/kicad/footprints"
DRIVER_LIB = os.path.join(HERE, "lib", "driver.pretty")
PCB_PATH = os.path.join(HERE, "matter_cct_driver.kicad_pcb")
PRO_PATH = os.path.join(HERE, "matter_cct_driver.kicad_pro")
OX, OY = 20.0, 20.0          # goc board trong toa do KiCad (mm)


def P(x, y):
    """toa do board (mm, goc tren-trai) -> VECTOR2I KiCad"""
    return VECTOR2I(FromMM(OX + x), FromMM(OY + y))


def load_footprint(fpid):
    lib, name = fpid.split(":")
    path = DRIVER_LIB if lib == "driver" else os.path.join(KICAD_FP, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit("Khong tim thay footprint %s trong %s" % (fpid, path))
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def build_board(route=False):
    board = pcbnew.BOARD()
    ds = board.GetDesignSettings()
    ds.m_CopperLayerCount = 2
    ds.SetBoardThickness(FromMM(1.6))
    ds.m_MinClearance = FromMM(0.2)
    ds.m_TrackMinWidth = FromMM(0.2)
    ds.m_ViasMinSize = FromMM(0.5)
    ds.m_MinThroughDrill = FromMM(0.3)
    ds.m_CopperEdgeClearance = FromMM(0.4)
    ds.m_SolderMaskExpansion = FromMM(0.05)

    # ---------------- nets
    nets = {}
    for name in sorted(db.nets().keys()):
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n

    # ---------------- footprints: nap, gan net
    fps = {}
    for c in db.C:
        fp = load_footprint(c["fp"])
        fp.SetReference(c["ref"])
        fp.SetValue(c["value"])
        for pad in fp.Pads():
            net = c["pins"].get(pad.GetNumber())
            if net and net != "NC":
                pad.SetNet(nets[net])
        fp.Reference().SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8)))
        fp.Reference().SetTextThickness(FromMM(0.12))
        fp.Value().SetVisible(False)
        board.Add(fp)
        fps[c["ref"]] = fp

    def crtyd_size(fp, rot):
        """kich thuoc courtyard (w, h) sau khi xoay rot (do)"""
        xs, ys = [], []
        for g in fp.GraphicalItems():
            if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                bb = g.GetBoundingBox()
                xs += [pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight())]
                ys += [pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())]
        w, h = (max(xs) - min(xs), max(ys) - min(ys)) if xs else (3.0, 2.0)
        return (h, w) if int(rot) % 180 == 90 else (w, h)

    def place(fp, x, y, rot, layer):
        fp.SetPosition(P(x, y))
        fp.SetOrientationDegrees(rot)
        if layer == "B":
            fp.Flip(fp.GetPosition(), False)
            fp.SetOrientationDegrees(rot)

    # dat co dinh
    for c in db.C:
        if c["pos"] is not None:
            x, y, rot = c["pos"]
            place(fps[c["ref"]], x, y, rot, c["layer"])
    # dat tu dong theo vung (shelf packing)
    for rname, (x0, y0, x1, y1, layer, gap, mode, gap_y) in db.REGIONS.items():
        items = db.region_items(rname)
        cx, cy, rowh, colw = x0, y0, 0.0, 0.0
        for c in items:
            fp = fps[c["ref"]]
            w, h = crtyd_size(fp, c["rot"])
            if mode == "row":
                if cx + w > x1 + 1e-6 and cx > x0:
                    cx, cy, rowh = x0, cy + rowh + gap_y, 0.0
                if cy + h > y1 + 1e-6 or cx + w > x1 + 1e-6:
                    print("CANH BAO: vung %s tran khi dat %s" % (rname, c["ref"]))
                place(fp, cx + w / 2, cy + h / 2, c["rot"], layer)
                if os.environ.get("PACK_DEBUG"):
                    print("  pack %-6s %-14s at (%.2f, %.2f) size %.2fx%.2f" % (c["ref"], rname, cx + w / 2, cy + h / 2, w, h))
                cx += w + gap
                rowh = max(rowh, h)
            else:
                if cy + h > y1 + 1e-6 and cy > y0:
                    cy, cx, colw = y0, cx + colw + gap, 0.0
                if cx + w > x1 + 1e-6 or cy + h > y1 + 1e-6:
                    print("CANH BAO: vung %s tran khi dat %s" % (rname, c["ref"]))
                place(fp, cx + w / 2, cy + h / 2, c["rot"], layer)
                cy += h + gap_y
                colw = max(colw, w)

    # ---------------- vien board (hinh chu nhat bo tron)
    W, H, R = db.BOARD_W, db.BOARD_H, db.BOARD_RADIUS
    def edge_line(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(x1, y1)); s.SetEnd(P(x2, y2))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1))
        board.Add(s)
    def edge_arc(cx, cy, a0, a1):
        # cung 90 do, ban kinh R, tam (cx, cy); a0 -> a1 theo do (0 = +x, 90 = +y KiCad)
        import math
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_ARC)
        am = (a0 + a1) / 2
        pt = lambda a: P(cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a)))
        s.SetArcGeometry(pt(a0), pt(am), pt(a1))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FromMM(0.1))
        board.Add(s)
    edge_line(R, 0, W - R, 0)
    edge_line(W, R, W, H - R)
    edge_line(W - R, H, R, H)
    edge_line(0, H - R, 0, R)
    edge_arc(W - R, R, 270, 360)
    edge_arc(W - R, H - R, 0, 90)
    edge_arc(R, H - R, 90, 180)
    edge_arc(R, R, 180, 270)
    # ranh phay cach ly (cutout kin)
    for (x1, y1, x2, y2) in db.ISO_SLOTS:
        edge_line(x1, y1, x2, y1); edge_line(x2, y1, x2, y2); edge_line(x2, y2, x1, y2); edge_line(x1, y2, x1, y1)

    # ---------------- rule areas (keepout)
    def rule_area(poly, layers=(pcbnew.F_Cu, pcbnew.B_Cu), name="", tracks=True, vias=True, pour=True, fp=False):
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(tracks); z.SetDoNotAllowVias(vias); z.SetDoNotAllowCopperPour(pour)
        z.SetDoNotAllowFootprints(fp); z.SetDoNotAllowPads(False)
        ls = pcbnew.LSET()
        for l in layers:
            ls.addLayer(l)
        z.SetLayerSet(ls)
        z.SetZoneName(name)
        o = z.Outline(); o.NewOutline()
        for (x, y) in poly:
            o.Append(FromMM(OX + x), FromMM(OY + y))
        board.Add(z)
        return z
    ax1, ay1, ax2, ay2 = db.ANTENNA_KEEPOUT
    rule_area([(ax1, ay1), (ax2, ay1), (ax2, ay2), (ax1, ay2)], name="antenna_keepout")
    bx = db.BARRIER_X
    rule_area([(bx - 0.6, 0), (bx + 0.6, 0), (bx + 0.6, 30.0), (bx - 0.6, 30.0)], name="iso_barrier")
    mx1, my1, mx2, my2 = db.MODULE_TRACK_KEEPOUT_F
    rule_area([(mx1, my1), (mx2, my1), (mx2, my2), (mx1, my2)], layers=(pcbnew.F_Cu,), name="module_no_tracks_top", pour=False)

    # ---------------- vung dong GND (fill sau khi di day)
    def copper_zone(net, poly, layer, name, clearance=0.3, minw=0.25, prio=0):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(nets[net])
        z.SetZoneName(name)
        z.SetLocalClearance(FromMM(clearance))
        z.SetMinThickness(FromMM(minw))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(FromMM(0.4)); z.SetThermalReliefSpokeWidth(FromMM(0.5))
        z.SetAssignedPriority(prio)
        o = z.Outline(); o.NewOutline()
        for (x, y) in poly:
            o.Append(FromMM(OX + x), FromMM(OY + y))
        board.Add(z)
        return z
    prim = [(1.0, 1.0), (bx - 0.6, 1.0), (bx - 0.6, 29.0), (1.0, 29.0)]
    sec = [(bx + 0.6, 1.0), (89.0, 1.0), (89.0, 29.0), (bx + 0.6, 29.0)]
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        sfx = "F" if layer == pcbnew.F_Cu else "B"
        copper_zone("GND_P", prim, layer, "GND_P_" + sfx, clearance=0.6, prio=1)
        copper_zone("GND_S", sec, layer, "GND_S_" + sfx, clearance=0.3, prio=1)

    # ---------------- chu tren silk
    def text(x, y, s, size=1.0, layer=pcbnew.F_SilkS, rot=0):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(s); t.SetPosition(P(x, y)); t.SetLayer(layer)
        t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size))); t.SetTextThickness(FromMM(0.15))
        t.SetTextAngleDegrees(rot)
        board.Add(t)
    text(13, 1.2, "!! 230 VAC - NGUY HIEM !!", 1.0)
    text(68, 15.5, "SELV", 1.2)
    text(66.3, 29.3, "DIP: 250+100.S1+200.S2+400.S3 mA", 0.5)
    text(26.0, 29.2, "matter-light-driver v1 30x95", 0.6)

    if route:
        import router
        router.route_board(board, nets, fps, db)
    return board


def fill_zones(path):
    """ZONE_FILLER can bi segfault tren board tao moi -> luu, nap lai roi fill."""
    board = pcbnew.LoadBoard(path)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(path, board)
    return board


def write_project():
    classes = []
    for name, (tw, cl, vd, vdr) in db.NET_CLASSES.items():
        entry = {"name": name, "clearance": cl, "track_width": tw, "via_diameter": vd, "via_drill": vdr,
                 "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,
                 "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1, "wire_width": 6, "bus_width": 12,
                 "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}
        if name != "Default":
            entry["nets"] = sorted(n for n in db.nets() if db.net_class(n) == name)
        classes.append(entry)
    pro = {
        "board": {"design_settings": {"defaults": {}, "rules": {
            "min_clearance": 0.2, "min_copper_edge_clearance": 0.4, "min_hole_clearance": 0.25,
            "min_track_width": 0.2, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3,
            "solder_mask_clearance": 0.0, "solder_mask_min_width": 0.0},
            "rule_severities": {"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore", "silk_overlap": "warning", "silk_over_copper": "ignore", "text_height": "ignore", "text_thickness": "ignore", "solder_mask_bridge": "warning", "silk_edge_clearance": "warning", "footprint_type_mismatch": "ignore", "starved_thermal": "warning"}},
                  "layer_presets": [], "viewports": []},
        "boards": [], "cvpcb": {"equivalence_files": []}, "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": "matter_cct_driver.kicad_pro", "version": 1},
        "net_settings": {"classes": classes, "meta": {"version": 3}, "net_colors": None, "netclass_assignments": None, "netclass_patterns": []},
        "pcbnew": {"last_paths": {"gencad": "", "idf": "", "netlist": "", "specctra_dsn": "", "step": "", "vrml": ""}, "page_layout_descr_file": ""},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [], "text_variables": {},
    }
    json.dump(pro, open(PRO_PATH, "w"), indent=2)
    open(os.path.join(HERE, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "driver")(type "KiCad")(uri "${KIPRJMOD}/lib/driver.pretty")(options "")(descr "Footprint rieng cua du an"))\n)\n')
    open(os.path.join(HERE, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "driver")(type "KiCad")(uri "${KIPRJMOD}/lib/driver.kicad_sym")(options "")(descr "Symbol rieng cua du an"))\n)\n')


def cleanup_violations(path, max_iter=8):
    """Xoa cac doan track/via bi DRC bao (clearance, dangling, keepout...) - net do thanh 'chua noi' thay vi vi pham."""
    import re
    def seg_dist(px, py, ax, ay, bx, by):
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5
    total = 0
    for it in range(max_iter):
        board = pcbnew.LoadBoard(path)
        rep = os.path.join(HERE, "drc_tmp.txt")
        pcbnew.WriteDRCReport(board, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
        txt = open(rep).read()
        bad = []
        for b in re.split(r"\n(?=\[)", txt):
            m = re.match(r"\[(clearance|hole_clearance|track_dangling|via_dangling|items_not_allowed|holes_co_located|copper_edge_clearance)\]", b)
            if not m:
                continue
            for mm in re.finditer(r"@\(([-\d.]+) mm, ([-\d.]+) mm\): (Track|Via) \[([^\]]*)\][^\n]*?(?:length ([\d.]+) mm)?", b):
                bad.append((float(mm.group(1)), float(mm.group(2)), mm.group(3), mm.group(4), float(mm.group(5)) if mm.group(5) else None))
        if not bad:
            break
        removed = 0
        for t in list(board.GetTracks()):
            is_via = t.GetClass() == "PCB_VIA"
            net = t.GetNetname()
            if is_via:
                px_, py_ = pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y)
                hit = any(k == "Via" and n == net and abs(px_ - x) < 0.05 and abs(py_ - y) < 0.05 for (x, y, k, n, ln) in bad)
            else:
                ax, ay = pcbnew.ToMM(t.GetStart().x), pcbnew.ToMM(t.GetStart().y)
                bx, by = pcbnew.ToMM(t.GetEnd().x), pcbnew.ToMM(t.GetEnd().y)
                L = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
                hit = any(k == "Track" and n == net and (ln is None or abs(ln - L) < 0.02) and seg_dist(x, y, ax, ay, bx, by) < 0.15 for (x, y, k, n, ln) in bad)
            if hit:
                board.Remove(t); removed += 1
        filler = pcbnew.ZONE_FILLER(board)
        filler.Fill(board.Zones())
        pcbnew.SaveBoard(path, board)
        total += removed
        print("cleanup vong %d: %d vi pham, xoa %d doan" % (it + 1, len(bad), removed))
        if removed == 0:
            break
    if os.path.exists(os.path.join(HERE, "drc_tmp.txt")):
        os.remove(os.path.join(HERE, "drc_tmp.txt"))
    return total


def run_drc(board):
    rep = os.path.join(HERE, "drc_report.txt")
    pcbnew.WriteDRCReport(board, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(rep).read()
    import re
    m = re.search(r"\*\* Found (\d+) DRC violations \*\*", txt)
    u = re.search(r"\*\* Found (\d+) unconnected pads \*\*", txt)
    kinds = {}
    for k in re.findall(r"^\[([a-z_]+)\]", txt, re.M):
        kinds[k] = kinds.get(k, 0) + 1
    ignore = {"lib_footprint_issues", "lib_footprint_mismatch", "silk_overlap", "silk_over_copper", "text_height",
              "text_thickness", "silk_edge_clearance", "starved_thermal", "footprint_type_mismatch"}
    real = {k: v for k, v in kinds.items() if k not in ignore}
    print("DRC: %s violations (%s ngoai silk/thu vien), %s unconnected" % (m.group(1) if m else "?", sum(real.values()), u.group(1) if u else "?"))
    print("  ", real)
    return txt


if __name__ == "__main__":
    route = "--route" in sys.argv
    board = build_board(route=route)
    write_project()
    pcbnew.SaveBoard(PCB_PATH, board)
    board = fill_zones(PCB_PATH)
    print("saved", PCB_PATH)
    if route and "--no-drc" not in sys.argv:
        cleanup_violations(PCB_PATH)
        board = pcbnew.LoadBoard(PCB_PATH)
    if "--no-drc" not in sys.argv:
        run_drc(board)

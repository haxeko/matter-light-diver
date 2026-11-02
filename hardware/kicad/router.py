#!/usr/bin/env python3
"""
router.py - Bo di day luoi (grid maze router) 2 lop cho board nay, dung voi API pcbnew (KiCad 7).

Nguyen ly: luoi 0.25 mm, moi o luu id net chiem (hoac -1 trong, -2 cam). Voi moi net, cac o cua net khac
duoc "no" them (w/2 + clearance) -> BFS/A* 8 huong, cho phep via. Net duoc noi dan theo kieu cay:
pad gan nhat -> tap da noi. Net GND_P / GND_S khong di day (dung vung dong). Net so cap chi duoc di
trong x < BARRIER, net thu cap chi trong x > BARRIER.
"""
import heapq
import math
import os

import numpy as np
import pcbnew
from pcbnew import VECTOR2I, FromMM, ToMM

PITCH = 0.125                # mm / o luoi
OX, OY = 20.0, 20.0          # goc board trong toa do KiCad
EDGE_MARGIN = 0.45           # mm tu mep board
VIA_DIA, VIA_DRILL = 0.6, 0.3
VIA_COST = 30                # chi phi doi lop (so o)
DIAG = 1.41421
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
FREE, BLOCK = -1, -2
GND_NETS = {"GND_P", "GND_S"}
NECK_MM = 1.6                # doan gan pad dung be rong = kich thuoc pad


class Grid:
    def __init__(self, w_mm, h_mm):
        self.nx = int(round(w_mm / PITCH)) + 1
        self.ny = int(round(h_mm / PITCH)) + 1
        self.occ = np.full((2, self.ny, self.nx), FREE, dtype=np.int32)   # [layer, y, x]

    def cell(self, x_mm, y_mm):
        return int(round(x_mm / PITCH)), int(round(y_mm / PITCH))

    def fill_rect(self, layer_idx, x1, y1, x2, y2, val):
        # chi danh dau o co TAM nam trong hinh chu nhat (sai so nua o duoc bu bang MARGIN khi no)
        i1, j1 = int(math.ceil(min(x1, x2) / PITCH - 1e-9)), int(math.ceil(min(y1, y2) / PITCH - 1e-9))
        i2, j2 = int(math.floor(max(x1, x2) / PITCH + 1e-9)), int(math.floor(max(y1, y2) / PITCH + 1e-9))
        i1, j1 = max(i1, 0), max(j1, 0)
        i2, j2 = min(i2, self.nx - 1), min(j2, self.ny - 1)
        if i2 >= i1 and j2 >= j1:
            self.occ[layer_idx, j1:j2 + 1, i1:i2 + 1] = val

    def fill_disk(self, layer_idx, cx, cy, r_mm, val):
        i0, j0 = self.cell(cx, cy)
        r = int(math.ceil(r_mm / PITCH))
        for dj in range(-r, r + 1):
            for di in range(-r, r + 1):
                if di * di + dj * dj <= r * r:
                    i, j = i0 + di, j0 + dj
                    if 0 <= i < self.nx and 0 <= j < self.ny:
                        self.occ[layer_idx, j, i] = val


def erode(mask, r):
    return ~dilate(~mask, r)


MARGIN = 0.9                 # o: bu sai so luoi (nua o rasterize + duong cheo)


def dilate(mask, r):
    """no mask (bool 2D) theo dia ban kinh r o (r co the la so thuc)"""
    out = mask.copy()
    ny, nx = mask.shape
    R = int(math.ceil(r))
    for dj in range(-R, R + 1):
        for di in range(-R, R + 1):
            if di == 0 and dj == 0 or di * di + dj * dj > r * r:
                continue
            src = mask[max(0, -dj):ny - max(0, dj), max(0, -di):nx - max(0, di)]
            out[max(0, dj):ny - max(0, -dj), max(0, di):nx - max(0, -di)] |= src
    return out


class Ctx:
    pass


def prepare(board, nets, db):
    """dung luoi chuong ngai + danh sach pad theo net"""
    c = Ctx()
    W, H = db.BOARD_W, db.BOARD_H
    g = Grid(W, H)
    c.g = g
    net_ids = {name: i for i, name in enumerate(sorted(nets.keys()))}
    id_net = {i: n for n, i in net_ids.items()}
    bx = db.BARRIER_X

    # ---- chuong ngai co dinh: mep board, hang rao, keepout anten, ranh phay
    base_block = np.zeros((g.ny, g.nx), dtype=bool)
    m = int(math.ceil(EDGE_MARGIN / PITCH))
    base_block[:m, :] = True; base_block[-m:, :] = True; base_block[:, :m] = True; base_block[:, -m:] = True
    # goc bo tron: chan vung ngoai cung tron
    R = db.BOARD_RADIUS
    for (cx, cy) in ((R, R), (W - R, R), (R, H - R), (W - R, H - R)):
        i0, j0 = g.cell(cx, cy)
        rr = int(round(R / PITCH))
        for dj in range(-rr, rr + 1):
            for di in range(-rr, rr + 1):
                i, j = i0 + di, j0 + dj
                xm, ym = i * PITCH, j * PITCH
                corner = (xm < R and cx == R or xm > W - R and cx == W - R) and (ym < R and cy == R or ym > H - R and cy == H - R)
                if corner and math.hypot(xm - cx, ym - cy) > R - EDGE_MARGIN and 0 <= i < g.nx and 0 <= j < g.ny:
                    base_block[j, i] = True
    i1, _ = g.cell(bx - 0.6, 0); i2, _ = g.cell(bx + 0.6, 0)
    base_block[:, i1:i2 + 1] = True
    ax1, ay1, ax2, ay2 = db.ANTENNA_KEEPOUT
    i1, j1 = g.cell(ax1, ay1); i2, j2 = g.cell(ax2, ay2)
    base_block[j1:j2 + 1, i1:i2 + 1] = True
    for (x1, y1, x2, y2) in db.ISO_SLOTS:
        i1, j1 = g.cell(x1 - 0.5, y1 - 0.5); i2, j2 = g.cell(x2 + 0.5, y2 + 0.5)
        base_block[max(j1, 0):j2 + 1, max(i1, 0):i2 + 1] = True
    for L in (0, 1):
        g.occ[L][base_block] = BLOCK
    mx1, my1, mx2, my2 = db.MODULE_TRACK_KEEPOUT_F
    i1, j1 = g.cell(mx1, my1); i2, j2 = g.cell(mx2, my2)
    g.occ[0][j1:j2 + 1, i1:i2 + 1] = BLOCK            # lop tren duoi module: cam track (pad se ghi de sau)

    # ---- pad -> luoi
    pads_by_net = {}
    pad_cells = {}
    hole_mask = np.zeros((g.ny, g.nx), dtype=bool)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            name = pad.GetNetname()
            bb = pad.GetBoundingBox()
            x1, y1 = ToMM(bb.GetLeft()) - OX, ToMM(bb.GetTop()) - OY
            x2, y2 = ToMM(bb.GetRight()) - OX, ToMM(bb.GetBottom()) - OY
            layers = [i for i, L in enumerate(LAYERS) if pad.IsOnLayer(L)]
            val = net_ids.get(name, BLOCK) if name else BLOCK
            for L in layers:
                g.fill_rect(L, x1, y1, x2, y2, val)
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
                i1, j1 = g.cell(x1, y1); i2, j2 = g.cell(x2, y2)
                hole_mask[max(j1, 0):j2 + 1, max(i1, 0):i2 + 1] = True
            if name in net_ids:
                cx, cy = ToMM(pad.GetPosition().x) - OX, ToMM(pad.GetPosition().y) - OY
                mind = min(ToMM(pad.GetSize().x), ToMM(pad.GetSize().y))
                pads_by_net.setdefault(name, []).append((cx, cy, layers, fp.GetReference(), pad.GetNumber(), mind))
                i1, j1 = g.cell(x1, y1); i2, j2 = g.cell(x2, y2)
                for L in layers:
                    for jj in range(max(j1, 0), min(j2, g.ny - 1) + 1):
                        for ii in range(max(i1, 0), min(i2, g.nx - 1) + 1):
                            pad_cells[(L, ii, jj)] = (cx, cy, mind)
        # rule area nam trong footprint (vd. keepout cua nut nhan)
        for z in fp.Zones():
            if z.GetIsRuleArea() and (z.GetDoNotAllowTracks() or z.GetDoNotAllowVias()):
                bb = z.GetBoundingBox()
                zx1, zy1 = ToMM(bb.GetLeft()) - OX, ToMM(bb.GetTop()) - OY
                zx2, zy2 = ToMM(bb.GetRight()) - OX, ToMM(bb.GetBottom()) - OY
                for L in (0, 1):
                    if z.GetLayerSet().Contains(LAYERS[L]):
                        g.fill_rect(L, zx1, zy1, zx2, zy2, BLOCK)
    c.pad_cells = pad_cells
    c.via_forbid = dilate(base_block, (VIA_DIA / 2) / PITCH + MARGIN)
    c.occ_pad = g.occ.copy()                      # trang thai chi co pad + keepout (dung cho rip-up)
    c.hole_block = dilate(hole_mask, (VIA_DIA / 2 + 0.5) / PITCH + MARGIN)
    c.net_ids, c.id_net, c.pads_by_net, c.base_block = net_ids, id_net, pads_by_net, base_block
    c.nets, c.db, c.board = nets, db, board
    return c


def route_board(board, nets, fps, db, debug_net=None):
    c = prepare(board, nets, db)
    g = c.g
    net_ids, id_net, pads_by_net = c.net_ids, c.id_net, c.pads_by_net
    bx = db.BARRIER_X
    prim = set(db.PRIMARY_NETS)

    def params(net):
        tw, cl, vd, vdr = db.NET_CLASSES[db.net_class(net)]
        return tw, cl

    def region_mask(net):
        mk = np.zeros((g.ny, g.nx), dtype=bool)
        ib, _ = g.cell(bx, 0)
        if net in prim:
            mk[:, ib:] = True
        else:
            mk[:, :ib] = True
        return mk

    def est_len(net):
        pts = pads_by_net.get(net, [])
        if len(pts) < 2:
            return 0
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        return (max(xs) - min(xs)) + (max(ys) - min(ys))

    fine_refs = {"U9", "U3", "U5", "U6", "U7", "U8", "U4", "U1", "U2", "Q2", "Q3"}

    def prio(n):
        cls = db.net_class(n)
        fine = any(p[3] in fine_refs for p in pads_by_net.get(n, []))
        if n in prim:
            return 0 if cls in ("HV", "AC") else 1
        if cls == "SIG" and fine:
            return 0
        if cls == "SIG":
            return 1
        if cls == "PWR_L":
            return 2
        return 3

    order = sorted([n for n in nets if n not in GND_NETS and len(pads_by_net.get(n, [])) >= 2],
                   key=lambda n: (prio(n), est_len(n)))
    if debug_net:
        order = [n for n in order if n == debug_net]
    stats = {"tracks": 0, "vias": 0}
    failed = []

    def mark_cells(path, widths, nid):
        for (L, i, j), w in zip(path, widths):
            rw = int(math.ceil(w / 2 / PITCH))
            for dj in range(-rw, rw + 1):
                for di in range(-rw, rw + 1):
                    if di * di + dj * dj <= rw * rw:
                        ii, jj = i + di, j + dj
                        if 0 <= ii < g.nx and 0 <= jj < g.ny and g.occ[L, jj, ii] == FREE:
                            g.occ[L, jj, ii] = nid
        rv = int(math.ceil(VIA_DIA / 2 / PITCH))
        for k in range(1, len(path)):
            if path[k][0] != path[k - 1][0]:
                _, i, j = path[k]
                for L in (0, 1):
                    for dj in range(-rv, rv + 1):
                        for di in range(-rv, rv + 1):
                            if di * di + dj * dj <= rv * rv:
                                ii, jj = i + di, j + dj
                                if 0 <= ii < g.nx and 0 <= jj < g.ny and g.occ[L, jj, ii] == FREE:
                                    g.occ[L, jj, ii] = nid

    def route_net(net, nid, tw, cl, final, ignore_tracks=False):
        """di day mot net voi be rong tw; tra ve (ok, so track, so via, set net bi cat). Khong final + that bai -> rollback."""
        pads = sorted(pads_by_net[net], key=lambda p: -len(p[2]))
        occ_ref = c.occ_pad if ignore_tracks else g.occ
        ripped = set()
        w_neck = min([tw] + [max(0.25, p[5]) for p in pads])
        r_cells = (tw / 2 + cl) / PITCH + MARGIN
        r_neck = (w_neck / 2 + cl) / PITCH + MARGIN
        via_r = (VIA_DIA / 2 + cl) / PITCH + MARGIN
        neck_cells = int(round(NECK_MM / PITCH))
        reg = region_mask(net)
        near_pad = np.zeros((g.ny, g.nx), dtype=bool)
        for p in pads:
            i0, j0 = g.cell(p[0], p[1])
            near_pad[max(j0 - neck_cells, 0):j0 + neck_cells + 1, max(i0 - neck_cells, 0):i0 + neck_cells + 1] = True
        blocked = []
        for L in (0, 1):
            other = (occ_ref[L] != FREE) & (occ_ref[L] != nid)
            blocked.append(((dilate(other, r_cells) & ~near_pad) | (dilate(other, r_neck) & near_pad)) | reg)
        via_blocked = dilate((occ_ref[0] != FREE) & (occ_ref[0] != nid), via_r) | dilate((occ_ref[1] != FREE) & (occ_ref[1] != nid), via_r) | reg | c.hole_block | c.via_forbid
        own = [(g.occ[L] == nid) for L in (0, 1)]
        rw_own = int(math.ceil(w_neck / 2 / PITCH))
        own_core = [erode(own[L], rw_own) for L in (0, 1)]
        conn = [np.zeros((g.ny, g.nx), dtype=bool) for _ in (0, 1)]

        def mark_pad(p):
            i0, j0 = g.cell(p[0], p[1])
            for L in p[2]:
                stack = [(i0, j0)]
                seen = set()
                while stack:
                    i, j = stack.pop()
                    if (i, j) in seen or not (0 <= i < g.nx and 0 <= j < g.ny) or not own[L][j, i] or conn[L][j, i]:
                        continue
                    seen.add((i, j)); conn[L][j, i] = True
                    stack += [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
                if not seen and 0 <= i0 < g.nx and 0 <= j0 < g.ny:
                    conn[L][j0, i0] = True

        snapshot_occ = g.occ.copy()
        pre_tracks = {t.m_Uuid.AsString() for t in board.GetTracks()}
        n_t = n_v = 0
        mark_pad(pads[0])
        remaining = pads[1:]
        ok = True
        while remaining:
            cj, ci = np.nonzero(conn[0] | conn[1])
            best, bestd = None, 1e9
            for p in remaining:
                i0, j0 = g.cell(p[0], p[1])
                d = np.min(np.abs(ci - i0) + np.abs(cj - j0)) if len(ci) else 0
                if d < bestd:
                    best, bestd = p, d
            p = best
            remaining.remove(p)
            for L in p[2]:
                ii0, jj0 = g.cell(p[0], p[1])
                if 0 <= ii0 < g.nx and 0 <= jj0 < g.ny:
                    own_core[L][jj0, ii0] = True
            path = astar(g, p, conn, blocked, via_blocked, own_core, nid)
            if path is None:
                if final:
                    failed.append((net, p[3] + "." + p[4]))
                    if debug_net or os.environ.get("DEBUG_FAIL") == net:
                        debug_dump(g, p, conn, blocked, own_core, nid, id_net)
                    mark_pad(p)
                    continue
                ok = False
                break
            widths = [w_neck if near_pad[j, i] else tw for (L, i, j) in path]
            if ignore_tracks:
                # cac net khac co track trong hanh lang -> rip-up
                rr = int(math.ceil(r_cells))
                for (L, i, j) in path:
                    sub = g.occ[L, max(j - rr, 0):j + rr + 1, max(i - rr, 0):i + rr + 1]
                    for v in np.unique(sub):
                        if v >= 0 and v != nid and id_net[v] not in GND_NETS:
                            ripped.add(id_net[v])
                for rn in ripped:
                    rip_up(rn)
            t_, v_ = emit(board, nets[net], path, widths, p, c.pad_cells)
            n_t += t_; n_v += v_
            mark_cells(path, widths, nid)
            for (L, i, j) in path:
                own[L][j, i] = True; conn[L][j, i] = True; own_core[L][j, i] = True
            mark_pad(p)
            for L in (0, 1):
                blocked[L] &= ~own_core[L]
        if not ok:
            # rollback: xoa track/via vua them, khoi phuc luoi
            for t in list(board.GetTracks()):
                if t.m_Uuid.AsString() not in pre_tracks:
                    board.Remove(t)
            g.occ[:] = snapshot_occ
            return False, 0, 0, set()
        return True, n_t, n_v, ripped

    def rip_up(net):
        """xoa track/via cua net khoi board va luoi (giu pad)"""
        nid = net_ids[net]
        for t in list(board.GetTracks()):
            if t.GetNetname() == net:
                board.Remove(t)
        for L in (0, 1):
            m = (g.occ[L] == nid) & (c.occ_pad[L] != nid)
            g.occ[L][m] = FREE

    def try_route(net, allow_rip):
        nid = net_ids[net]
        tw0, cl = params(net)
        wmin = 0.5 if db.net_class(net) == "PWR_S" else 0.25
        attempts = sorted({tw0, round(max(wmin, tw0 * 0.6), 2), round(max(wmin, tw0 * 0.35), 2)}, reverse=True)
        for tw in attempts:
            ok, n_t, n_v, _ = route_net(net, nid, tw, cl, final=False)
            if ok:
                stats["tracks"] += n_t; stats["vias"] += n_v
                if tw != tw0:
                    narrowed[net] = tw
                return True, set()
        if allow_rip:
            ok, n_t, n_v, ripped = route_net(net, nid, attempts[-1], cl, final=False, ignore_tracks=True)
            if ok:
                stats["tracks"] += n_t; stats["vias"] += n_v
                narrowed[net] = attempts[-1]
                return True, ripped
        return False, set()

    narrowed = {}
    queue = list(order)
    done = set()
    rounds = 0
    MAX_ROUNDS = 1                     # rip-up/reroute tat (gay dao dong); chi dung fallback be rong
    rip_count = {}
    while queue and rounds < MAX_ROUNDS:
        rounds += 1
        requeue = []
        for net in queue:
            allow = rounds > 1 and rip_count.get(net, 0) < 3
            ok, ripped = try_route(net, allow)
            if ok:
                done.add(net)
                for rn in ripped:
                    if rn in done:
                        done.discard(rn)
                    rip_count[rn] = rip_count.get(rn, 0) + 1
                    if rn not in requeue:
                        requeue.append(rn)
            else:
                requeue.append(net)
        # cac net bi rip-up va net that bai -> vong sau
        queue = [n for n in requeue if n not in done]
        if queue:
            print("   vong %d: con %d net chua xong -> %s" % (rounds, len(queue), ", ".join(queue[:8])))
    # vong cuoi: di day mot phan + bao that bai cho nhung net con lai
    failed[:] = []
    for net in queue:
        nid = net_ids[net]
        tw0, cl = params(net)
        ok, n_t, n_v, _ = route_net(net, nid, 0.25 if db.net_class(net) != "PWR_S" else 0.5, cl, final=True)
        stats["tracks"] += n_t; stats["vias"] += n_v
    if narrowed:
        print("   net dung be rong nho hon lop: " + ", ".join("%s=%.2f" % kv for kv in sorted(narrowed.items())))
    if not debug_net:
        n_gv = gnd_via_stubs(board, nets, c)
        print("router: %d via stub GND" % n_gv)
    print("router: %d tracks, %d vias, %d failed" % (stats["tracks"], stats["vias"], len(failed)))
    for f in failed:
        print("   KHONG DI DUOC:", f)
    return failed


def path_widths(path, tw, pad, pad_cells):
    """be rong tung o: gan pad (dau/cuoi) dung min(tw, kich thuoc pad)"""
    n = len(path)
    neck = int(round(NECK_MM / PITCH))
    w_start = min(tw, max(0.25, pad[5]))
    end_pad = pad_cells.get(path[-1])
    w_end = min(tw, max(0.25, end_pad[2])) if end_pad else tw
    ws = []
    for k in range(n):
        w = tw
        if k < neck:
            w = min(w, w_start)
        if n - 1 - k < neck:
            w = min(w, w_end)
        ws.append(w)
    return ws


def gnd_via_stubs(board, nets, c):
    """moi pad SMD GND: track ngan + via toi o trong gan nhat de noi vao vung dong hai lop"""
    from collections import deque
    g = c.g
    n_v = 0
    via_r = (VIA_DIA / 2 + 0.3) / PITCH + MARGIN
    def P(i, j):
        return VECTOR2I(FromMM(OX + i * PITCH), FromMM(OY + j * PITCH))
    for net in GND_NETS:
        if net not in nets:
            continue
        nid = c.net_ids[net]
        via_bad = dilate((g.occ[0] != FREE) & (g.occ[0] != nid), via_r) | dilate((g.occ[1] != FREE) & (g.occ[1] != nid), via_r) | c.hole_block | c.via_forbid
        for (cx, cy, layers, ref, num, mind) in c.pads_by_net.get(net, []):
            if len(layers) == 2 or ref in ("U9",):
                continue            # pad THT / module: vung dong noi truc tiep
            L = layers[0]
            i0, j0 = g.cell(cx, cy)
            w = min(0.5, max(0.25, mind))
            rw = (w / 2 + 0.2) / PITCH + MARGIN + 0.5
            blocked = dilate((g.occ[L] != FREE) & (g.occ[L] != nid), rw)
            rw = int(math.ceil(rw))
            core = erode(g.occ[L] == nid, int(math.ceil(w / 2 / PITCH)))
            dq = deque([(i0, j0)]); prev = {(i0, j0): None}
            found = None
            while dq:
                i, j = dq.popleft()
                if not via_bad[j, i] and (abs(i - i0) + abs(j - j0)) >= 3:
                    found = (i, j); break
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < g.nx and 0 <= jj < g.ny and (ii, jj) not in prev and (not blocked[jj, ii] or core[jj, ii]):
                        prev[(ii, jj)] = (i, j); dq.append((ii, jj))
                if len(prev) > 8000:
                    break
            if found is None:
                continue
            pts = [found]
            while prev[pts[-1]] is not None:
                pts.append(prev[pts[-1]])
            pts.reverse()
            a = VECTOR2I(FromMM(OX + cx), FromMM(OY + cy))
            # doan thang: tam pad -> (di theo cac o, gop thang hang)
            seg = [a] + [P(*q) for q in pts]
            simp = [seg[0]]
            for k in range(1, len(seg) - 1):
                d1 = (seg[k].x - simp[-1].x, seg[k].y - simp[-1].y)
                d2 = (seg[k + 1].x - seg[k].x, seg[k + 1].y - seg[k].y)
                if d1[0] * d2[1] - d1[1] * d2[0] != 0:
                    simp.append(seg[k])
            simp.append(seg[-1])
            for s_, e_ in zip(simp[:-1], simp[1:]):
                if s_ == e_:
                    continue
                t = pcbnew.PCB_TRACK(board); t.SetStart(s_); t.SetEnd(e_); t.SetWidth(FromMM(w)); t.SetLayer(LAYERS[L]); t.SetNet(nets[net]); board.Add(t)
            v = pcbnew.PCB_VIA(board); v.SetPosition(P(*found)); v.SetDrill(FromMM(VIA_DRILL)); v.SetWidth(FromMM(VIA_DIA))
            v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(nets[net]); board.Add(v)
            n_v += 1
            for (i, j) in pts:
                for dj in range(-rw, rw + 1):
                    for di in range(-rw, rw + 1):
                        if 0 <= i + di < g.nx and 0 <= j + dj < g.ny and g.occ[L, j + dj, i + di] == FREE:
                            g.occ[L, j + dj, i + di] = nid
            fi, fj = found
            for LL in (0, 1):
                for dj in range(-3, 4):
                    for di in range(-3, 4):
                        if di * di + dj * dj <= 9 and 0 <= fi + di < g.nx and 0 <= fj + dj < g.ny and g.occ[LL, fj + dj, fi + di] == FREE:
                            g.occ[LL, fj + dj, fi + di] = nid
            vr = int(math.ceil(via_r))
            via_bad[max(fj - vr - 3, 0):fj + vr + 4, max(fi - vr - 3, 0):fi + vr + 4] = True
    return n_v


def astar(g, pad, conn, blocked, via_blocked, own, nid):
    """A* tu pad (cac o own cua pad) den bat ky o nao trong conn (tap da noi). Tra ve [(L,i,j)...]"""
    cx, cy, layers = pad[0], pad[1], pad[2]
    i0, j0 = g.cell(cx, cy)
    targets = [conn[0], conn[1]]
    tj, ti = np.nonzero(conn[0] | conn[1])
    if len(ti) == 0:
        return None
    def h(i, j):
        return 0.0 if len(ti) > 4000 else float(np.min(np.maximum(np.abs(ti - i), np.abs(tj - j))))
    start = []
    for L in layers:
        if 0 <= i0 < g.nx and 0 <= j0 < g.ny:
            start.append((L, i0, j0))
    if not start:
        return None
    dist = {}
    prev = {}
    pq = []
    for s in start:
        dist[s] = 0.0
        heapq.heappush(pq, (h(s[1], s[2]), 0.0, s))
    moves = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, DIAG), (1, -1, DIAG), (-1, 1, DIAG), (-1, -1, DIAG)]
    found = None
    expansions = 0
    while pq:
        f, dcur, (L, i, j) = heapq.heappop(pq)
        if dcur > dist.get((L, i, j), 1e18):
            continue
        if targets[L][j, i]:
            found = (L, i, j)
            break
        expansions += 1
        if expansions > 2500000:
            break
        for di, dj, c in moves:
            ii, jj = i + di, j + dj
            if not (0 <= ii < g.nx and 0 <= jj < g.ny):
                continue
            if blocked[L][jj, ii] and not own[L][jj, ii]:
                continue
            nd = dcur + c
            key = (L, ii, jj)
            if nd < dist.get(key, 1e18):
                dist[key] = nd; prev[key] = (L, i, j)
                heapq.heappush(pq, (nd + h(ii, jj), nd, key))
        # via
        L2 = 1 - L
        if not via_blocked[j, i]:
            nd = dcur + VIA_COST
            key = (L2, i, j)
            if nd < dist.get(key, 1e18):
                dist[key] = nd; prev[key] = (L, i, j)
                heapq.heappush(pq, (nd + h(i, j), nd, key))
    if found is None:
        return None
    path = [found]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def emit(board, netinfo, path, widths, pad, pad_cells):
    """tao PCB_TRACK / PCB_VIA tu duong luoi; noi tam pad dau va tam pad dich (neu ket thuc trong pad)"""
    def P(i, j):
        return VECTOR2I(FromMM(OX + i * PITCH), FromMM(OY + j * PITCH))
    def add_track(a, b, L, w):
        if a == b:
            return 0
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(a); t.SetEnd(b); t.SetWidth(FromMM(w)); t.SetLayer(L); t.SetNet(netinfo)
        board.Add(t)
        return 1
    n_t = n_v = 0
    cx, cy = pad[0], pad[1]
    n_t += add_track(VECTOR2I(FromMM(OX + cx), FromMM(OY + cy)), P(path[0][1], path[0][2]), LAYERS[path[0][0]], widths[0])
    k = 1
    seg_start = 0
    while k < len(path):
        L0 = path[seg_start][0]
        L1, i1, j1 = path[k]
        if L1 != L0:
            if (path[seg_start][1], path[seg_start][2]) != (path[k - 1][1], path[k - 1][2]):
                n_t += add_track(P(path[seg_start][1], path[seg_start][2]), P(path[k - 1][1], path[k - 1][2]), LAYERS[L0], widths[seg_start])
            pos = P(i1, j1)
            dup = any(t.GetClass() == "PCB_VIA" and t.GetPosition() == pos for t in board.GetTracks())
            if not dup:
                v = pcbnew.PCB_VIA(board)
                v.SetPosition(pos); v.SetDrill(FromMM(VIA_DRILL)); v.SetWidth(FromMM(VIA_DIA))
                v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(netinfo)
                board.Add(v); n_v += 1
            seg_start = k
            k += 1
            continue
        di, dj = path[k][1] - path[k - 1][1], path[k][2] - path[k - 1][2]
        kk = k
        while kk + 1 < len(path) and path[kk + 1][0] == L0 and widths[kk + 1] == widths[seg_start] and \
                (path[kk + 1][1] - path[kk][1], path[kk + 1][2] - path[kk][2]) == (di, dj):
            kk += 1
        n_t += add_track(P(path[seg_start][1], path[seg_start][2]), P(path[kk][1], path[kk][2]), LAYERS[L0], widths[seg_start])
        seg_start = kk
        k = kk + 1
    end_pad = pad_cells.get(path[-1])
    if end_pad:
        n_t += add_track(P(path[-1][1], path[-1][2]), VECTOR2I(FromMM(OX + end_pad[0]), FromMM(OY + end_pad[1])), LAYERS[path[-1][0]], widths[-1])
    return n_t, n_v


def debug_dump(g, pad, conn, blocked, own, nid, id_net, R=14):
    cx, cy, layers, ref, num = pad[:5]
    i0, j0 = g.cell(cx, cy)
    print("DEBUG pad %s.%s at cell (%d,%d) layers %s own=%s" % (ref, num, i0, j0, layers, [bool(own[L][j0, i0]) for L in (0, 1)]))
    for L in layers:
        print(" layer", L, "('.' free, '#' blocked, 'o' own, 'T' target, 'X' start)")
        for j in range(j0 - R, j0 + R + 1):
            row = ""
            for i in range(i0 - R, i0 + R + 1):
                if not (0 <= i < g.nx and 0 <= j < g.ny):
                    row += " "; continue
                ch = "."
                if blocked[L][j, i]: ch = "#"
                if own[L][j, i]: ch = "o"
                if conn[L][j, i]: ch = "T"
                if (i, j) == (i0, j0): ch = "X"
                row += ch
            print("  " + row)
    # cac net chan quanh start
    seen = {}
    for L in layers:
        for j in range(j0 - 6, j0 + 7):
            for i in range(i0 - 6, i0 + 7):
                if 0 <= i < g.nx and 0 <= j < g.ny:
                    v = g.occ[L, j, i]
                    if v >= 0 and v != nid:
                        seen[id_net[v]] = seen.get(id_net[v], 0) + 1
    print("  net lan can:", seen)

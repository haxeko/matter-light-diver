#!/usr/bin/env python3
"""Sinh floorplan PCB 30 x 90 mm (SVG) cho driver 40 W; ban 30 x 60 mm (<= 20 W) mo ta trong docs/05."""
S = 10.0                      # px / mm
L, W = 90.0, 30.0             # mm
OX, OY = 40, 60               # le trai / tren (px)
out = []

def px(x): return OX + x * S
def py(y): return OY + y * S
def esc(t): return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def rect(x1, y1, x2, y2, label, fill, stroke="#333", fs=9, dash=None, rot=False):
    dd = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<rect x="{px(x1):.1f}" y="{py(y1):.1f}" width="{(x2-x1)*S:.1f}" height="{(y2-y1)*S:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="1"{dd}/>')
    cx, cy = px((x1 + x2) / 2), py((y1 + y2) / 2)
    lines = label.split("\n")
    tr = f' transform="rotate(-90 {cx:.1f} {cy:.1f})"' if rot else ""
    y0 = cy - (len(lines) - 1) * (fs + 1) / 2 + fs / 3
    for i, t in enumerate(lines):
        out.append(f'<text x="{cx:.1f}" y="{y0 + i*(fs+1):.1f}" text-anchor="middle" font-size="{fs}" font-family="Arial, Helvetica, sans-serif" fill="#111"{tr}>{esc(t)}</text>')
def text(x, y, t, fs=10, anchor="start", color="#333", bold=False):
    out.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{fs}" font-weight="{"bold" if bold else "normal"}" font-family="Arial, Helvetica, sans-serif" fill="{color}">{esc(t)}</text>')

Wpx, Hpx = int(px(L) + 40), int(py(W) + 170)
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wpx}" height="{Hpx}" viewBox="0 0 {Wpx} {Hpx}">')
out.append('<defs><pattern id="hp" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#c0392b" stroke-width="1"/></pattern>'
           '<pattern id="hg" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#1e8449" stroke-width="1"/></pattern>'
           '<pattern id="hk" width="5" height="5" patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="5" y2="5" stroke="#7f8c8d" stroke-width="0.8"/></pattern></defs>')
out.append(f'<rect width="{Wpx}" height="{Hpx}" fill="#fff"/>')
text(OX, 24, "Floorplan PCB driver CCT 3 dây – 30 × 90 mm, FR4 1.6 mm, 2 lớp, đồng 2 oz (bản 40 W). Tỉ lệ 10 px = 1 mm.", 13, bold=True)
text(OX, 42, "Màu: đỏ = sơ cấp (điện áp lưới), xanh lá = thứ cấp SELV, vàng = giao diện người dùng, xám gạch = keep-out đồng (creepage / anten).", 10)

# board
out.append(f'<rect x="{px(0)}" y="{py(0)}" width="{L*S}" height="{W*S}" fill="#f4f6f7" stroke="#000" stroke-width="2" rx="{2*S}"/>')
# vung so cap / thu cap
out.append(f'<rect x="{px(0.4)}" y="{py(0.4)}" width="{44.6*S}" height="{29.2*S}" fill="#fdf2f0" stroke="none"/>')
out.append(f'<rect x="{px(45)}" y="{py(0.4)}" width="{44.6*S}" height="{29.2*S}" fill="#eefaf1" stroke="none"/>')
# dai so cap duoi bien ap (track FB/GND_P ra opto, Y)
rect(35, 27, 66, 29.6, "", "url(#hp)", "#c0392b")
text(px(36), py(28.6) + 3, "dải đồng SƠ CẤP (GND_P, FB) → U2 / CY1", 8, "start", "#c0392b")
# keep-out creepage
rect(45.2, 19, 56, 27, "KEEP-OUT đồng\nthứ cấp (creepage\n≥ 8 mm)", "url(#hk)", "#7f8c8d", 7)
rect(66.5, 19, 74, 27, "KEEP-OUT", "url(#hk)", "#7f8c8d", 7)
rect(66, 27, 74, 29.6, "", "url(#hk)", "#7f8c8d")
# hang rao cach ly (zigzag)
pts = [(45, 0), (45, 23.5), (70, 23.5), (70, 30)]
out.append('<polyline points="' + " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in pts) + '" fill="none" stroke="#c0392b" stroke-width="2" stroke-dasharray="6 4"/>')
text(px(45) + 4, py(0) - 6, "hàng rào cách ly (≥ 8 mm creepage, rãnh phay 1 mm ở y = 0–3.5 và 23.5–30)", 9, "start", "#c0392b")

P, Sc, UI = "#fadbd8", "#d5f5e3", "#fef9e7"
# ---- so cap
rect(1, 1, 11, 8.6, "J1 AC IN\n2×5.08 mm", P)
rect(12, 1, 19, 4, "F1 2410", P, fs=8)
rect(20.5, 1, 25, 4.5, "BR1", P, fs=8)
rect(12, 5, 22, 10, "RV1 MOV ø10 (đứng)", P, fs=8)
rect(23, 5.5, 32, 9.5, "RT1 NTC ø9", P, fs=8)
rect(1, 9.5, 13, 19, "L1 CM choke\nUU9.8", P)
rect(14, 11, 27, 16, "CX1 X2 100 nF", P, fs=8)
rect(1, 19.5, 21, 29.5, "C1 47 µF / 400 V  (ø10×20, nằm)", P, fs=8)
rect(28, 11, 34.5, 20, "Q1\nDPAK", P, fs=8)
rect(22, 17, 27.5, 20.5, "clamp\nD1 R1 C2", P, fs=7)
rect(22, 21, 34, 29.5, "U1 UCC28740 + R2 (CS)\nR5/R6, C6–C8, R8", P, fs=8)
rect(35, 1, 55.5, 23, "T1  PQ20/20\n(chân sơ cấp trái, thứ cấp phải)\n20.5 × 22 mm, cao 16 mm", "#f9e79f", "#9a7d0a", 9)
# ---- qua hang rao
rect(56.5, 19.3, 61, 29.7, "U2 opto\nSOP-4 LC", "#fdf6d8", "#9a7d0a", 7)
rect(62, 19.3, 66, 29.7, "CY1\nY1", "#fdf6d8", "#9a7d0a", 7)
# ---- thu cap
rect(56.5, 1, 64.5, 6.5, "D2 ES3J SMC", Sc, fs=8)
rect(56.5, 7.5, 64.5, 15.5, "C4 100 µF/63 V\nø8 (đứng)", Sc, fs=8)
rect(56.5, 16, 66, 18.8, "R7 shunt 2×1206", Sc, fs=7)
rect(65.5, 1, 73.5, 8, "U3 op-amp, U4 TL431\nR9–R23, D4, R17", Sc, fs=7)
rect(65.5, 8.5, 73.5, 15.5, "Buck 5 V: U7 + L2\nD6, C14–C16", Sc, fs=7)
rect(67, 16, 73.5, 18.8, "U8 LDO 3V3", Sc, fs=7)
rect(74, 1, 80, 8, "Q2 Q3\nU5 U6", Sc, fs=8)
rect(80.5, 1, 89, 8, "SW1–3 DIP\n(3 vị trí)", UI, "#b7950b", 8)
rect(74, 8.8, 87.2, 22, "U9 ESP32-C6-MINI-1\n13.2 × 16.6 mm\n(anten hướng mép phải ►)", Sc, "#1e8449", 8)
rect(87.2, 8.8, 90, 22, "", "url(#hk)", "#7f8c8d")
rect(79, 22.5, 89.5, 29.5, "J2 OUT 3 dây\nV+ CW– WW–", UI, "#b7950b", 8)
rect(74.5, 22.5, 78.5, 25.5, "SW4", UI, "#b7950b", 7)
rect(74.5, 26, 78.5, 29.5, "LED", UI, "#b7950b", 7)
# lo bat vit
for (x, y) in [(2.2, 2.2), (2.2, 27.8), (87.8, 2.2), (87.8, 27.8)]:
    pass
# kich thuoc
out.append(f'<line x1="{px(0)}" y1="{py(W)+18}" x2="{px(L)}" y2="{py(W)+18}" stroke="#333" stroke-width="1"/>')
text(px(L / 2), py(W) + 32, "90 mm (bản 40 W) – có thể rút còn 60–65 mm với bản ≤ 20 W (xem docs/05)", 10, "middle")
out.append(f'<line x1="{px(L)+18}" y1="{py(0)}" x2="{px(L)+18}" y2="{py(W)}" stroke="#333" stroke-width="1"/>')
text(px(L) + 24, py(W / 2) + 4, "30 mm", 10, "start")
text(OX, py(W) + 56, "Ghi chú: linh kiện SMD nhỏ (R, C 0603, SOT-23) của phía thứ cấp có thể đặt mặt dưới để rút ngắn chiều dài. Vùng dưới module ESP32-C6 và vùng anten (x ≥ 87 mm) không đổ đồng cả hai lớp.", 9)
text(OX, py(W) + 72, "Đường dòng lớn: AC→BR1→C1→T1→Q1→R2→C1 (vòng nhỏ, cùng lớp). Thứ cấp: T1→D2→C4→R7 (vòng nhỏ). Buck: U7→L2→C15 và D6 sát U7. Tụ CY1 nối cực âm C1 ↔ GND_S ngay cạnh T1.", 9)
text(OX, py(W) + 88, "Vỏ nhựa PC (không kim loại) để anten hoạt động; dây AC/LED cố định bằng kẹp; khoảng cách linh kiện cao (C1, T1, L1) tới nắp ≥ 2 mm. Chiều cao tổng ≤ 21 mm.", 9)
out.append('</svg>')
open("hardware/pcb/floorplan_30x90.svg", "w").write("\n".join(out))
print("ok floorplan")

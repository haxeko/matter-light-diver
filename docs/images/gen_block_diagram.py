#!/usr/bin/env python3
"""Sinh so do khoi (SVG) cua driver den CCT 3 day ESP32-C6 Matter/Thread."""
W, H = 1180, 640
out = []
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def box(x, y, w, h, lines, fill="#eef4ff", stroke="#1f4e9c", bold_first=True, fs=13):
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" ry="6" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
    n = len(lines); lh = fs + 4
    y0 = y + h / 2 - (n - 1) * lh / 2 + fs / 3
    for i, t in enumerate(lines):
        fw = "bold" if (i == 0 and bold_first) else "normal"
        out.append(f'<text x="{x + w/2}" y="{y0 + i*lh:.1f}" text-anchor="middle" font-size="{fs}" font-weight="{fw}" font-family="Arial, Helvetica, sans-serif" fill="#111">{esc(t)}</text>')
def arrow(x1, y1, x2, y2, label=None, color="#333", dash=None, lpos=0.5, dy=-5):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.8" marker-end="url(#ah)"{d}/>')
    if label:
        lx, ly = x1 + (x2 - x1) * lpos, y1 + (y2 - y1) * lpos + dy
        out.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="11" font-family="Arial, Helvetica, sans-serif" fill="{color}">{esc(label)}</text>')
def text(x, y, t, fs=12, anchor="start", color="#333", bold=False):
    out.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{fs}" font-weight="{"bold" if bold else "normal"}" font-family="Arial, Helvetica, sans-serif" fill="{color}">{esc(t)}</text>')

out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Arial, Helvetica, sans-serif">')
out.append('<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#333"/></marker></defs>')
out.append(f'<rect width="{W}" height="{H}" fill="#fff"/>')
text(W/2, 28, "Sơ đồ khối driver đèn CCT 3 dây – ESP32-C6, Matter over Thread, nguồn flyback cách ly", 17, "middle", "#111", True)

# vung so cap / thu cap
out.append('<rect x="20" y="50" width="470" height="560" rx="10" fill="#fff5f0" stroke="#c0392b" stroke-dasharray="6 4"/>')
text(30, 70, "PHÍA SƠ CẤP (điện áp lưới – nguy hiểm)", 12, "start", "#c0392b", True)
out.append('<rect x="520" y="50" width="640" height="560" rx="10" fill="#f0fff4" stroke="#1e8449" stroke-dasharray="6 4"/>')
text(530, 70, "PHÍA THỨ CẤP – SELV (cách ly 3.75 kV, creepage ≥ 8 mm)", 12, "start", "#1e8449", True)
out.append('<line x1="505" y1="50" x2="505" y2="610" stroke="#888" stroke-width="2" stroke-dasharray="3 3"/>')
text(505, 625, "hàng rào cách ly", 11, "middle", "#666")

# chuoi nguon so cap
box(35, 100, 90, 60, ["AC IN", "176–264 VAC", "L / N"], fill="#ffe9e0")
box(150, 95, 120, 70, ["Bảo vệ & lọc EMI", "F1 T2A, MOV 10D471", "CM choke, X2 100 nF"], fs=11)
box(295, 95, 120, 70, ["Chỉnh lưu + bulk", "MB10S / 4×1N4007", "C 47 µF / 400 V"], fs=11)
arrow(125, 130, 150, 130); arrow(270, 130, 295, 130)
box(150, 220, 140, 80, ["Điều khiển flyback", "U1 UCC28740", "Q1 MOSFET 650 V", "clamp RCD / TVS"], fs=11)
box(330, 210, 150, 100, ["Biến áp PQ20/20", "Np 42 : Ns 24 : Naux 14", "Lp 490 µH, 75 kHz", "VOR 80 V, cách ly tăng cường"], fs=11)
arrow(355, 165, 355, 210, "HV DC 215–373 V", lpos=0.5, dy=-4)
out.append('<line x1="355" y1="165" x2="355" y2="190" stroke="#333" stroke-width="1.8"/>')
arrow(290, 260, 330, 260)
box(150, 340, 140, 60, ["Cuộn phụ VCC", "12–26 V → U1 VDD", "VS: OVP / CC sơ cấp"], fs=11)
arrow(330, 290, 290, 360, dash="4 3")
box(150, 440, 140, 60, ["Khởi động HV", "2×1 MΩ từ bulk", "(≈ 25 µA)"], fs=11)
arrow(355, 165, 220, 440, dash="4 3")

# opto
box(440, 400, 120, 70, ["Opto PC817 / EL817", "cách ly 5 kV", "creepage ≥ 8 mm"], fill="#fdf6d8", stroke="#9a7d0a", fs=11)
arrow(440, 435, 220, 300, "FB (giảm công suất)", dash=None, lpos=0.6, dy=14)
# Y cap
box(440, 520, 120, 44, ["C Y1 2.2 nF", "sơ cấp ↔ thứ cấp (EMI)"], fill="#fdf6d8", stroke="#9a7d0a", fs=11)

# thu cap
box(535, 210, 140, 100, ["Chỉnh lưu thứ cấp", "D ES3J 600 V / 3 A", "C 100 µF / 63 V", "V+ = 20–42 V (CC)", "45 V kẹp (CV, đèn tắt)"], fs=11)
arrow(480, 260, 535, 260)
box(700, 210, 160, 100, ["Vòng CC + CV", "R sense 0.15 Ω, gain ×5", "U3 op-amp (CC), U4 TL431 (CV)", "wired-OR → opto", "Imax cứng 1.0 A"], fs=11)
arrow(675, 260, 700, 260)
arrow(700, 300, 560, 435, "kéo LED opto", lpos=0.55, dy=14)

box(890, 95, 250, 70, ["ĐẦU RA 3 DÂY", "V+ (chung, anode) | CW– | WW–", "đèn CCT 2700–6500 K, Vf 20–42 V"], fill="#e8f8f5", stroke="#117a65", fs=12)
arrow(605, 210, 605, 130); out.append('<line x1="605" y1="130" x2="890" y2="130" stroke="#333" stroke-width="1.8"/>')
text(740, 122, "V+", 11, "middle")
box(890, 210, 120, 100, ["Chuyển kênh CW/WW", "Q2, Q3 MOSFET 60 V", "U5, U6 74AHCT1G125", "(dịch mức 3.3 → 5 V)", "PWM 4 kHz bù nhau"], fs=11)
arrow(950, 210, 950, 165, "CW– / WW–", lpos=0.5, dy=-4)
arrow(860, 260, 890, 260, "I tổng", dy=-6)

box(535, 350, 130, 60, ["Buck 5 V", "LMR16006 / XL7005", "22 µH, 600 mA"], fs=11)
arrow(605, 310, 605, 350)
box(700, 350, 100, 60, ["LDO 3.3 V", "ME6211 / RT9013", "500 mA"], fs=11)
arrow(665, 380, 700, 380)
box(840, 350, 290, 110, ["ESP32-C6-MINI-1  (Matter over Thread)", "RISC-V 160 MHz, 802.15.4 + BLE 5 (commissioning)", "Color Temperature Light (0x010C)", "LEDC PWM: DIM-ref 12 bit, CW/WW 4 kHz", "ADC: V+, I_out, NTC  |  GPIO: DIP ×3, nút, LED"], fs=11)
arrow(800, 380, 840, 380, "3V3")
arrow(960, 350, 960, 310, "PWM_CW, PWM_WW", lpos=0.5, dy=-4)
arrow(840, 420, 780, 310, "PWM_DIM → RC → Vref", lpos=0.5, dy=16)
arrow(760, 330, 840, 440, "ADC I_out / V+", lpos=0.5, dy=16, dash="4 3")

box(535, 500, 150, 70, ["3 nút gạt DIP (SW1..3)", "250 + 100·S1 + 200·S2", "+ 400·S3 mA (8 mức)"], fill="#fff8e1", stroke="#b7950b", fs=11)
box(710, 500, 120, 70, ["Nút nhấn", "identify / reset", "(giữ 5 s = factory reset)"], fill="#fff8e1", stroke="#b7950b", fs=11)
box(855, 500, 120, 70, ["LED trạng thái", "+ NTC quá nhiệt", "(giảm dòng > 85 °C)"], fill="#fff8e1", stroke="#b7950b", fs=11)
box(1000, 500, 140, 70, ["Nạp & debug", "USB-JTAG (GPIO12/13)", "UART0 pad, EN, BOOT"], fill="#fff8e1", stroke="#b7950b", fs=11)
arrow(610, 500, 900, 460, "GPIO18/19/20", lpos=0.3, dy=-6)
arrow(770, 500, 930, 460)
arrow(915, 500, 960, 460)
arrow(1070, 500, 1010, 460)
out.append('</svg>')
open("docs/images/block_diagram.svg", "w").write("\n".join(out))
print("ok block_diagram.svg")

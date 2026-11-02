#!/usr/bin/env python3
"""Khoi 3: U1 UCC28740, chia ap VS, khoi dong HV, opto U2 (phia transistor), tu Y."""
import schemdraw
import schemdraw.elements as elm

OUT = "hardware/schematics/03_controller.svg"
d = schemdraw.Drawing(file=OUT, show=False)
d.config(unit=2.0, fontsize=9, lw=1.3)
BLUE = "#1f4e9c"

def net(x, y, name, loc="right"):
    d.add(elm.Dot(radius=0.06).at((x, y)))
    d.add(elm.Label().at((x, y)).label(name, loc=loc, color=BLUE))

def lbl(x, y, text, fs=8, ha="left"):
    d.add(elm.Label().at((x, y)).label(text, fontsize=fs, halign=ha))

d += elm.Label().at((0, 9.8)).label("Khối 3 – Điều khiển flyback U1 UCC28740 (SOIC-7), chia áp VS, khởi động HV, opto U2 (phía sơ cấp), tụ Y", fontsize=12, halign="left")

U1 = elm.Ic(pins=[
    elm.IcPin(name="HV", pin="7", side="left", anchorname="HV"),
    elm.IcPin(name="FB", pin="3", side="left", anchorname="FB"),
    elm.IcPin(name="VS", pin="2", side="left", anchorname="VS"),
    elm.IcPin(name="VDD", pin="1", side="left", anchorname="VDD"),
    elm.IcPin(name="CS", pin="5", side="right", anchorname="CS"),
    elm.IcPin(name="DRV", pin="6", side="right", anchorname="DRV"),
    elm.IcPin(name="GND", pin="4", side="bottom", anchorname="GND"),
], size=(3.6, 7.6), pinspacing=1.9, edgepadH=0.4)
d += U1.right().at((11.0, 3.0)).anchor("center")
lbl(11.0, 7.3, "U1  UCC28740 (SOIC-7)\nthay thế: NCP1250B, OB2273 (đổi bù/VS)", 9, "center")

# VDD (tren cung)
p = U1.VDD
d += elm.Line().at(p).to((p[0] - 1.2, p[1]))
d += elm.Dot().at((p[0] - 1.2, p[1]))
d += elm.Capacitor().at((p[0] - 1.2, p[1])).to((p[0] - 1.2, p[1] - 1.3))
lbl(p[0] - 1.5, p[1] - 0.65, "C8\n100 nF", 8, "right")
d += elm.Ground().at((p[0] - 1.2, p[1] - 1.3))
d += elm.Line().at((p[0] - 1.2, p[1])).to((p[0] - 3.4, p[1]))
net(p[0] - 3.4, p[1], "VDD  (← D3/C3, khối 2)", "left")

# VS
p = U1.VS
d += elm.Line().at(p).to((p[0] - 1.2, p[1]))
d += elm.Dot().at((p[0] - 1.2, p[1]))
d += elm.Resistor().at((p[0] - 1.2, p[1])).to((p[0] - 3.8, p[1]))
lbl(p[0] - 2.5, p[1] + 0.35, "R5  150 kΩ 1 %", 8, "center")
net(p[0] - 3.8, p[1], "AUX  (← cuộn phụ)", "left")
d += elm.Resistor().at((p[0] - 1.2, p[1])).to((p[0] - 1.2, p[1] - 1.6))
lbl(p[0] - 1.5, p[1] - 0.8, "R6\n20 kΩ 1 %", 8, "right")
d += elm.Ground().at((p[0] - 1.2, p[1] - 1.6))
lbl(0.2, U1.absanchors["VDD"][1] + 1.2, "VS lấy mẫu V+ qua cuộn phụ: OVP ≈ 50 V, phát hiện\nvalley (QR), giới hạn CC sơ cấp Imax ≈ 1.1 A", 8, "left")

# FB <- opto
p = U1.FB
d += elm.Line().at(p).to((p[0] - 1.0, p[1]))
d += elm.Dot().at((p[0] - 1.0, p[1]))
d += elm.Capacitor().at((p[0] - 1.0, p[1])).to((p[0] - 1.0, p[1] - 1.3))
lbl(p[0] - 1.3, p[1] - 0.65, "C6\n1 nF", 8, "right")
d += elm.Ground().at((p[0] - 1.0, p[1] - 1.3))
U2 = elm.Ic(pins=[elm.IcPin(name="K", pin="2", side="left", anchorname="K"),
                  elm.IcPin(name="A", pin="1", side="left", anchorname="A"),
                  elm.IcPin(name="E", pin="3", side="right", anchorname="E"),
                  elm.IcPin(name="C", pin="4", side="right", anchorname="C")],
            size=(2.2, 2.2), pinspacing=1.2)
d += U2.right().at((p[0] - 4.6, p[1] + 0.2)).anchor("center")
col, emi = U2.absanchors["C"], U2.absanchors["E"]
an, ca = U2.absanchors["A"], U2.absanchors["K"]
d += elm.Line().at((p[0] - 1.0, p[1])).to((p[0] - 2.4, p[1]))
d += elm.Line().at((p[0] - 2.4, p[1])).to((p[0] - 2.4, col[1]))
d += elm.Line().at((p[0] - 2.4, col[1])).to(col)
d += elm.Line().at(emi).to((p[0] - 2.4, emi[1]))
d += elm.Line().at((p[0] - 2.4, emi[1])).to((p[0] - 2.4, emi[1] - 0.6))
d += elm.Ground().at((p[0] - 2.4, emi[1] - 0.6))
lbl(p[0] - 4.6, p[1] - 1.35, "U2  PC817C / EL817(S1), CTR 200–400 %, creepage ≥ 8 mm (SOP-4 LC / DIP-4 10.16)\nLED A/K phía thứ cấp – transistor C/E phía sơ cấp", 7, "center")
d += elm.Line().at(an).to((an[0] - 1.0, an[1]))
net(an[0] - 1.0, an[1], "OPTO_A  (← +5 V qua R17, khối 4)", "left")
d += elm.Line().at(ca).to((ca[0] - 1.0, ca[1]))
net(ca[0] - 1.0, ca[1], "OPTO_K  (← wired-OR CC/CV, khối 4)", "left")

# HV
p = U1.HV
d += elm.Line().at(p).to((p[0] - 1.2, p[1]))
d += elm.Resistor().at((p[0] - 1.2, p[1])).to((p[0] - 3.8, p[1]))
lbl(p[0] - 2.5, p[1] - 0.45, "R8  1 kΩ / 1206 (giới hạn dòng HV)", 8, "center")
net(p[0] - 3.8, p[1], "+HV", "left")

# CS, DRV, GND
p = U1.CS
d += elm.Line().at(p).to((p[0] + 1.0, p[1]))
d += elm.Dot().at((p[0] + 1.0, p[1]))
d += elm.Capacitor().at((p[0] + 1.0, p[1])).to((p[0] + 1.0, p[1] - 1.3))
lbl(p[0] + 1.3, p[1] - 0.65, "C7  220 pF\n(lọc spike CS)")
d += elm.Ground().at((p[0] + 1.0, p[1] - 1.3))
d += elm.Line().at((p[0] + 1.0, p[1])).to((p[0] + 2.6, p[1]))
net(p[0] + 2.6, p[1], "CS  (← R4, khối 2)", "right")
p = U1.DRV
d += elm.Line().at(p).to((p[0] + 2.6, p[1]))
net(p[0] + 2.6, p[1], "DRV  (→ R3 → cổng Q1)", "right")
p = U1.GND
d += elm.Line().at(p).to((p[0], p[1] - 0.5))
d += elm.Ground().at((p[0], p[1] - 0.5)).label("GND_P", "right")

# tu Y
d += elm.Dot(open=True).at((15.0, -2.4)).label("GND_P", "left")
d += elm.Capacitor().at((15.0, -2.4)).to((18.0, -2.4))
lbl(16.5, -1.95, "CY1  2.2 nF / 250 VAC, lớp Y1\nbắc qua hàng rào cách ly (giảm nhiễu CM)", 8, "center")
d += elm.Dot(open=True).at((18.0, -2.4)).label("GND_S", "right")
lbl(0.0, -2.2, "Toàn bộ GND ở khối này là GND_P (cực âm C1). U1 đặt sát Q1/R2; C8 sát chân VDD; R6, C7 sát chân IC;\nđường CS ngắn. Chân HV: UCC28740 có nguồn khởi động 700 V tích hợp – không cần điện trở MΩ.", 8, "left")
d.save(OUT)
print("ok", OUT)

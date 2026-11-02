#!/usr/bin/env python3
"""Khoi 2: tang cong suat flyback - bien ap T1, MOSFET Q1, clamp, cuon phu (phia so cap), chinh luu thu cap."""
import schemdraw
import schemdraw.elements as elm

OUT = "hardware/schematics/02_flyback_stage.svg"
d = schemdraw.Drawing(file=OUT, show=False)
d.config(unit=2.0, fontsize=9, lw=1.3)
BLUE = "#1f4e9c"

def net(x, y, name, loc="right"):
    d.add(elm.Dot(radius=0.06).at((x, y)))
    d.add(elm.Label().at((x, y)).label(name, loc=loc, color=BLUE))

def lbl(x, y, text, fs=8, ha="left"):
    d.add(elm.Label().at((x, y)).label(text, fontsize=fs, halign=ha))

d += elm.Label().at((0, 11.6)).label("Khối 2 – Tầng công suất flyback: T1 PQ20/20, Q1 650 V, clamp RCD/TVS, cuộn phụ VDD (sơ cấp), chỉnh lưu thứ cấp", fontsize=12, halign="left")

# bien ap chinh (cuon phu ve rieng ben duoi cho de doc)
T1 = elm.Transformer(t1=8, t2=6, core=True).at((9.0, 7.0)).anchor("p1")
d += T1
A = T1.absanchors
mt, mb = A["p1"], A["p2"]
st, sb = (A["s1"], A["s2"]) if A["s1"][1] > A["s2"][1] else (A["s2"], A["s1"])
lbl(mt[0] + 0.6, mt[1] + 1.0, "T1  PQ20/20 – cách ly tăng cường 3.75 kV\nNp 42 : Ns 24 : Naux 14  |  Lp 490 µH ±10 %\nLlk ≤ 1.5 % Lp (quấn sandwich), fs 75 kHz", 8, "left")

# +HV rail
yHV = mt[1] + 2.2
d += elm.Line().at(mt).to((mt[0], yHV))
d += elm.Line().at((mt[0], yHV)).to((1.0, yHV))
net(1.0, yHV, "+HV", "left")
# clamp RCD
xc = mt[0] - 3.0
d += elm.Dot().at((xc, yHV))
d += elm.Dot().at((xc - 2.0, yHV))
d += elm.Line().at(mb).to((xc, mb[1]))
d += elm.Dot().at((xc, mb[1]))
d += elm.Diode().at((xc, mb[1])).to((xc, mb[1] + 1.8))
lbl(xc + 0.3, mb[1] + 0.9, "D1  ES1J\n600 V / 1 A, nhanh")
d += elm.Dot().at((xc, mb[1] + 1.8))
d += elm.Resistor().at((xc, mb[1] + 1.8)).to((xc, yHV))
lbl(xc + 0.3, (mb[1] + 1.8 + yHV) / 2, "R1  11 kΩ / 2 W\n(2× 22 kΩ 2512 song song)")
d += elm.Line().at((xc, mb[1] + 1.8)).to((xc - 2.0, mb[1] + 1.8))
d += elm.Capacitor().at((xc - 2.0, mb[1] + 1.8)).to((xc - 2.0, yHV))
lbl(xc - 2.3, (mb[1] + 1.8 + yHV) / 2, "C2  12 nF\n400 V", 8, "right")
lbl(0.2, mb[1] + 0.9, "Tuỳ chọn: TVS P6KE150A\nthay cho R1/C2 (giảm tổn hao)", 8, "left")

# Q1
d += elm.Line().at(mb).to((mb[0], mb[1] - 1.8))
Q1 = elm.NFet(bulk=False).reverse().at((mb[0], mb[1] - 1.8)).anchor("drain")
d += Q1
lbl(Q1.drain[0] + 0.5, Q1.drain[1] - 0.5, "Q1  N-MOSFET 650 V / 4–6 A\nRds(on) ≤ 1.5 Ω, TO-220F / DPAK\n(STF6N65K3, WSF6N65, SVF4N65)")
yS = Q1.source[1] - 0.6
d += elm.Line().at(Q1.source).to((Q1.source[0], yS))
d += elm.Dot().at((Q1.source[0], yS))
d += elm.Resistor().at((Q1.source[0], yS)).to((Q1.source[0], yS - 2.0))
lbl(Q1.source[0] + 0.3, yS - 1.0, "R2  0R43 / 1 W\n(2× 0R82 1206 song song)")
d += elm.Ground().at((Q1.source[0], yS - 2.0)).label("GND_P", "right")
d += elm.Line().at((Q1.source[0], yS)).to((Q1.source[0] - 1.0, yS))
d += elm.Resistor().at((Q1.source[0] - 1.0, yS)).to((Q1.source[0] - 3.0, yS)).label("R4  1 kΩ", "top")
net(Q1.source[0] - 3.0, yS, "CS  (→ U1 pin 5)", "left")
g = Q1.gate
d += elm.Line().at(g).to((g[0] - 0.4, g[1]))
d += elm.Resistor().at((g[0] - 0.4, g[1])).to((g[0] - 2.4, g[1])).label("R3  10 Ω", "top")
net(g[0] - 2.4, g[1], "DRV  (← U1 pin 6)", "left")

# cuon phu (phia so cap) - ve rieng
xa, ya = 2.2, -2.6
d += elm.Inductor2(loops=3).at((xa, ya)).to((xa, ya - 1.6))
lbl(xa - 0.3, ya - 0.8, "T1 cuộn phụ\n(Naux 14 vg,\ncùng lõi)", 8, "right")
d += elm.Dot().at((xa, ya))
d += elm.Line().at((xa, ya)).to((xa, ya + 0.9))
net(xa, ya + 0.9, "AUX (→ R5/R6, khối 3)", "top")
d += elm.Diode().at((xa, ya)).to((xa + 2.2, ya))
lbl(xa + 1.1, ya + 0.35, "D3  US1J", 8, "center")
d += elm.Dot().at((xa + 2.2, ya))
d += elm.Capacitor(polar=True).at((xa + 2.2, ya)).to((xa + 2.2, ya - 1.6))
lbl(xa + 2.5, ya - 0.8, "C3  10 µF / 50 V")
d += elm.Line().at((xa, ya - 1.6)).to((xa + 2.2, ya - 1.6))
d += elm.Dot().at((xa + 2.2, ya - 1.6))
d += elm.Ground().at((xa + 2.2, ya - 1.6)).label("GND_P", "right")
d += elm.Line().at((xa + 2.2, ya)).to((xa + 4.0, ya))
net(xa + 4.0, ya, "VDD  12–26 V  (→ U1 pin 1)", "right")
lbl(xa - 0.3, ya + 1.6, "Chấm cực tính: AUX cùng pha với cuộn thứ cấp (flyback).", 8, "left")

# thu cap
d += elm.Line().at(st).to((st[0] + 1.0, st[1]))
d += elm.Diode().at((st[0] + 1.0, st[1])).to((st[0] + 3.0, st[1]))
lbl(st[0] + 2.0, st[1] + 0.35, "D2  ES3J (SMC)  600 V / 3 A\nVrrm cần ≥ 260 V, trr 35 ns", 8, "center")
xV = st[0] + 3.0
d += elm.Dot().at((xV, st[1]))
yG = sb[1]
d += elm.Capacitor(polar=True).at((xV, st[1])).to((xV, yG))
lbl(xV + 0.3, (st[1] + yG) / 2, "C4  100 µF / 63 V\nlow-ESR, 105 °C")
d += elm.Dot().at((xV, yG))
d += elm.Line().at((xV, st[1])).to((xV + 3.2, st[1]))
d += elm.Dot().at((xV + 3.2, st[1]))
d += elm.Capacitor().at((xV + 3.2, st[1])).to((xV + 3.2, yG))
lbl(xV + 3.5, (st[1] + yG) / 2, "C5  100 nF\n100 V X7R")
d += elm.Dot().at((xV + 3.2, yG))
d += elm.Line().at((xV + 3.2, st[1])).to((xV + 4.8, st[1]))
net(xV + 4.8, st[1], "V+   20–42 V (CC) / 45 V (CV)", "right")
d += elm.Line().at(sb).to((xV, yG))
d += elm.Line().at((xV + 3.2, yG)).to((xV + 4.8, yG))
d += elm.Ground().at((xV + 4.8, yG)).label("GND_S", "right")
lbl(st[0] + 2.0, yG - 0.5, "(shunt dòng R7 nằm ở khối 5 – chỉ đo dòng LED)", 8, "center")
xb = (mt[0] + st[0]) / 2
d += elm.Line().at((xb, mt[1] + 0.6)).to((xb, mb[1] - 0.6)).linestyle("--").color("#c0392b").linewidth(1.0)
d += elm.Label().at((xb + 0.25, mb[1] - 0.9)).label("hàng rào cách ly", fontsize=8, color="#c0392b", halign="left")
d.save(OUT)
print("ok", OUT)

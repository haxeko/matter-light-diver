#!/usr/bin/env python3
"""Khoi 6 (thu cap): buck 5 V LMR16006 tu V+ (20-45 V), LDO 3.3 V cho ESP32-C6."""
import schemdraw
import schemdraw.elements as elm

OUT = "hardware/schematics/06_aux_supply.svg"
d = schemdraw.Drawing(file=OUT, show=False)
d.config(unit=2.0, fontsize=9, lw=1.3)
BLUE = "#1f4e9c"

def net(x, y, name, loc="right"):
    d.add(elm.Dot(radius=0.06).at((x, y)))
    d.add(elm.Label().at((x, y)).label(name, loc=loc, color=BLUE))

def lbl(x, y, text, fs=8, ha="left"):
    d.add(elm.Label().at((x, y)).label(text, fontsize=fs, halign=ha))

d += elm.Label().at((0, 7.4)).label("Khối 6 – Nguồn phụ thứ cấp: buck 5 V (U7 LMR16006Y, 60 V / 0.6 A) từ V+ 20–45 V, LDO 3.3 V (U8) cho ESP32-C6", fontsize=12, halign="left")

U7 = elm.Ic(pins=[elm.IcPin(name="FB", pin="4", side="left", anchorname="FB"),
                  elm.IcPin(name="EN", pin="3", side="left", anchorname="EN"),
                  elm.IcPin(name="VIN", pin="2", side="left", anchorname="VIN"),
                  elm.IcPin(name="BOOT", pin="6", side="right", anchorname="BOOT"),
                  elm.IcPin(name="SW", pin="5", side="right", anchorname="SW"),
                  elm.IcPin(name="GND", pin="1", side="bottom", anchorname="GND")],
            size=(2.8, 4.0), pinspacing=1.4)
d += U7.right().at((6.0, 3.0)).anchor("center")
lbl(6.0, 6.3, "U7  LMR16006YDDCR (SOT-23-6, 700 kHz)\nthay thế: MP9486A, XL7005A (đổi chia áp FB)", 8, "center")
vin = U7.absanchors["VIN"]
d += elm.Line().at(vin).to((vin[0] - 3.6, vin[1]))
d += elm.Dot().at((vin[0] - 3.6, vin[1]))
d += elm.Capacitor().at((vin[0] - 3.6, vin[1])).to((vin[0] - 3.6, vin[1] - 1.6))
lbl(vin[0] - 3.9, vin[1] - 0.8, "C16  4.7 µF\n100 V X7R\n+ 100 nF", 8, "right")
d += elm.Ground().at((vin[0] - 3.6, vin[1] - 1.6))
d += elm.Line().at((vin[0] - 3.6, vin[1])).to((vin[0] - 5.4, vin[1]))
net(vin[0] - 5.4, vin[1], "V+  (20–45 V)", "left")
en = U7.absanchors["EN"]
d += elm.Line().at(en).to((en[0] - 0.7, en[1]))
d += elm.Dot().at((en[0] - 0.7, vin[1]))
d += elm.Resistor().at((en[0] - 0.7, en[1])).to((en[0] - 0.7, vin[1]))
lbl(en[0] - 0.7, vin[1] + 0.45, "R28 100 kΩ (EN ← VIN)", 7, "center")
fb = U7.absanchors["FB"]
d += elm.Line().at(fb).to((fb[0] - 1.0, fb[1]))
d += elm.Dot().at((fb[0] - 1.0, fb[1]))
d += elm.Resistor().at((fb[0] - 1.0, fb[1])).to((fb[0] - 1.0, fb[1] - 1.8))
lbl(fb[0] - 1.3, fb[1] - 0.9, "R30\n10 kΩ 1 %", 8, "right")
d += elm.Ground().at((fb[0] - 1.0, fb[1] - 1.8))
sw = U7.absanchors["SW"]
boot = U7.absanchors["BOOT"]
d += elm.Line().at(sw).to((sw[0] + 1.0, sw[1]))
d += elm.Dot().at((sw[0] + 1.0, sw[1]))
d += elm.Capacitor().at((sw[0] + 1.0, sw[1])).to((sw[0] + 1.0, boot[1]))
lbl(sw[0] + 1.3, (sw[1] + boot[1]) / 2, "C17 100 nF\n(bootstrap)")
d += elm.Line().at(boot).to((sw[0] + 1.0, boot[1]))
d += elm.Diode().at((sw[0] + 1.0, sw[1] - 2.2)).to((sw[0] + 1.0, sw[1]))
lbl(sw[0] + 1.3, sw[1] - 1.1, "D6  SS16 / SS110\n(Schottky 60–100 V)")
d += elm.Ground().at((sw[0] + 1.0, sw[1] - 2.2))
d += elm.Inductor().at((sw[0] + 1.0, sw[1])).to((sw[0] + 3.6, sw[1]))
lbl(sw[0] + 2.3, sw[1] + 0.4, "L2  22 µH / 1 A (CD54 / 5×5)", 8, "center")
d += elm.Dot().at((sw[0] + 3.6, sw[1]))
d += elm.Capacitor().at((sw[0] + 3.6, sw[1])).to((sw[0] + 3.6, sw[1] - 2.2))
lbl(sw[0] + 3.9, sw[1] - 1.1, "C18  22 µF ×2\n10 V X7R")
d += elm.Ground().at((sw[0] + 3.6, sw[1] - 2.2))
d += elm.Line().at((sw[0] + 3.6, sw[1])).to((sw[0] + 5.2, sw[1]))
d += elm.Dot().at((sw[0] + 5.2, sw[1]))
net(sw[0] + 5.2, sw[1] + 0.0, "+5 V  (opto, U3, U5/U6, LDO)", "top")
# chia ap FB tu +5V
d += elm.Line().at((sw[0] + 3.6, sw[1])).to((sw[0] + 3.6, sw[1] + 1.4))
d += elm.Line().at((sw[0] + 3.6, sw[1] + 1.4)).to((fb[0] - 1.0, sw[1] + 1.4))
d += elm.Resistor().at((fb[0] - 1.0, sw[1] + 1.4)).to((fb[0] - 1.0, fb[1]))
lbl(fb[0] - 1.3, (sw[1] + 1.4 + fb[1]) / 2, "R29 56 kΩ 1 %\nVout = 0.765 ×\n(1 + 56/10) = 5.05 V", 8, "right")
g = U7.absanchors["GND"]
d += elm.Line().at(g).to((g[0], g[1] - 0.5))
d += elm.Ground().at((g[0], g[1] - 0.5)).label("GND_S", "right")

# LDO
U8 = elm.Ic(pins=[elm.IcPin(name="VIN", pin="1", side="left", anchorname="VIN"),
                  elm.IcPin(name="EN", pin="3", side="left", anchorname="EN"),
                  elm.IcPin(name="VOUT", pin="5", side="right", anchorname="VOUT"),
                  elm.IcPin(name="GND", pin="2", side="bottom", anchorname="GND")],
            size=(2.6, 2.4), pinspacing=1.2)
d += U8.right().at((16.5, -2.6)).anchor("center")
lbl(16.5, -0.9, "U8  ME6211C33 / RT9013-33 (SOT-23-5, 500 mA)", 8, "center")
v = U8.absanchors["VIN"]
d += elm.Line().at(v).to((v[0] - 1.2, v[1]))
d += elm.Dot().at((v[0] - 1.2, v[1]))
d += elm.Capacitor().at((v[0] - 1.2, v[1])).to((v[0] - 1.2, v[1] - 1.6))
lbl(v[0] - 1.5, v[1] - 0.8, "C19 1 µF", 8, "right")
d += elm.Ground().at((v[0] - 1.2, v[1] - 1.6))
d += elm.Line().at((v[0] - 1.2, v[1])).to((v[0] - 2.8, v[1]))
net(v[0] - 2.8, v[1], "+5 V", "left")
e = U8.absanchors["EN"]
d += elm.Line().at(e).to((e[0] - 1.2, e[1]))
d += elm.Line().at((e[0] - 1.2, e[1])).to((e[0] - 1.2, v[1]))
o = U8.absanchors["VOUT"]
d += elm.Line().at(o).to((o[0] + 1.2, o[1]))
d += elm.Dot().at((o[0] + 1.2, o[1]))
d += elm.Capacitor().at((o[0] + 1.2, o[1])).to((o[0] + 1.2, o[1] - 1.6))
lbl(o[0] + 1.5, o[1] - 0.8, "C20 10 µF + 100 nF\n(sát chân 3V3 module)")
d += elm.Ground().at((o[0] + 1.2, o[1] - 1.6))
d += elm.Line().at((o[0] + 1.2, o[1])).to((o[0] + 3.0, o[1]))
net(o[0] + 3.0, o[1], "+3V3  (ESP32-C6, ≤ 350 mA đỉnh)", "right")
g = U8.absanchors["GND"]
d += elm.Line().at(g).to((g[0], g[1] - 0.5))
d += elm.Ground().at((g[0], g[1] - 0.5)).label("GND_S", "right")
lbl(0.0, -4.6, "Tổn hao: buck ≈ 0.2 W (η 85 %), LDO ≈ 0.26 W @150 mA. Tổng dòng kéo từ V+: 25–55 mA. Đặt D6, C16, U7 thành vòng nhỏ; L2 cách anten ≥ 10 mm.\n"
    "Có thể bỏ LDO và dùng buck 3.3 V trực tiếp nếu chấp nhận lái cổng FET bằng 3.3 V (Rds cao hơn ~40 %).", 8, "left")
d.save(OUT)
print("ok", OUT)

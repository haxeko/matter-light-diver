#!/usr/bin/env python3
"""Khoi 5 (thu cap): dich muc 3.3->5 V, MOSFET kenh CW/WW, shunt R7, dau ra 3 day."""
import schemdraw
import schemdraw.elements as elm

OUT = "hardware/schematics/05_output_switch.svg"
d = schemdraw.Drawing(file=OUT, show=False)
d.config(unit=2.0, fontsize=9, lw=1.3)
BLUE = "#1f4e9c"

def net(x, y, name, loc="right"):
    d.add(elm.Dot(radius=0.06).at((x, y)))
    d.add(elm.Label().at((x, y)).label(name, loc=loc, color=BLUE))

def lbl(x, y, text, fs=8, ha="left"):
    d.add(elm.Label().at((x, y)).label(text, fontsize=fs, halign=ha))

d += elm.Label().at((0, 11.6)).label("Khối 5 – Thứ cấp: dịch mức 3.3 → 5 V, MOSFET kênh CW / WW (common-anode), shunt dòng R7, đầu ra 3 dây", fontsize=12, halign="left")

def channel(y, name, gpio, uref, qref, rg, rpd):
    # bo dem 74AHCT1G125
    U = elm.Ic(pins=[elm.IcPin(name="A", pin="2", side="left", anchorname="A"),
                     elm.IcPin(name="Y", pin="4", side="right", anchorname="Y"),
                     elm.IcPin(name="OE", pin="1", side="bottom", anchorname="OE", invert=True),
                     elm.IcPin(name="VCC", pin="5", side="top", anchorname="VCC")],
               size=(2.0, 1.6), pinspacing=1.0)
    d.add(U.right().at((4.0, y)).anchor("center"))
    lbl(4.0, y - 1.5, f"{uref}  74AHCT1G125\n(Vih 2 V → chấp nhận 3.3 V)", 8, "center")
    a = U.absanchors["A"]
    d.add(elm.Line().at(a).to((a[0] - 1.4, a[1])))
    net(a[0] - 1.4, a[1], f"{name}  ({gpio}, 3.3 V, PWM 4 kHz)", "left")
    oe = U.absanchors["OE"]
    d.add(elm.Line().at(oe).to((oe[0], oe[1] - 0.4)))
    d.add(elm.Ground().at((oe[0], oe[1] - 0.4)))
    vcc = U.absanchors["VCC"]
    d.add(elm.Line().at(vcc).to((vcc[0], vcc[1] + 0.4)))
    d.add(elm.Vdd().at((vcc[0], vcc[1] + 0.4)).label("+5 V"))
    yy = U.absanchors["Y"]
    d.add(elm.Resistor().at(yy).to((yy[0] + 2.0, yy[1])))
    lbl(yy[0] + 1.0, yy[1] + 0.35, f"{rg}  47 Ω", 8, "center")
    # NFet.reverse(): gate = drain + (-1.37, -0.75), source = drain + (0, -1.5)
    Q = elm.NFet(bulk=False).reverse().at((yy[0] + 2.0 + 1.37, yy[1] + 0.75)).anchor("drain")
    d.add(Q)
    g, dr, sr = Q.absanchors["gate"], Q.absanchors["drain"], Q.absanchors["source"]
    d.add(elm.Dot().at((yy[0] + 2.0, yy[1])))
    d.add(elm.Resistor().at((yy[0] + 2.0, yy[1])).to((yy[0] + 2.0, yy[1] - 1.8)))
    lbl(yy[0] + 1.7, yy[1] - 0.9, f"{rpd}\n100 kΩ", 8, "right")
    d.add(elm.Ground().at((yy[0] + 2.0, yy[1] - 1.8)))
    lbl(dr[0] + 0.4, dr[1] + 0.5, f"{qref}  IRLML0060 / AO3160\n60 V, Rds ≤ 0.25 Ω @ 4.5 V, SOT-23", 8, "left")
    return dr, sr

d1, s1 = channel(7.5, "PWM_CW", "GPIO0", "U5", "Q2", "R24", "R25")
d2, s2 = channel(1.5, "PWM_WW", "GPIO1", "U6", "Q3", "R26", "R27")
# drain -> dau ra
xj = d1[0] + 5.0
d += elm.Line().at(d1).to((d1[0], d1[1] + 0.6))
d += elm.Line().at((d1[0], d1[1] + 0.6)).to((xj - 1.0, d1[1] + 0.6))
d += elm.Line().at(d2).to((d2[0], d2[1] + 0.6))
d += elm.Line().at((d2[0], d2[1] + 0.6)).to((xj - 1.0, d2[1] + 0.6))
J2 = elm.Header(rows=3, pinsleft=["V+", "CW–", "WW–"], pinalignleft="center").right().at((xj, d1[1] + 1.2)).anchor("pin1")
d += J2
lbl(xj + 0.9, d1[1] - 1.6, "J2  đầu ra 3 dây\n(cầu đấu 3.5 mm / JST-XH)\nV+ chung (anode), CW–, WW–", 8, "left")
pins = {k: J2.absanchors[k] for k in ("pin1", "pin2", "pin3")}
ys = sorted(pins.items(), key=lambda kv: -kv[1][1])
pV, pCW, pWW = [v for _, v in ys]
d += elm.Line().at(pV).to((pV[0] - 2.4, pV[1]))
net(pV[0] - 2.4, pV[1], "V+", "left")
d += elm.Line().at((xj - 1.0, d1[1] + 0.6)).to((xj - 1.0, pCW[1]))
d += elm.Line().at((xj - 1.0, pCW[1])).to(pCW)
d += elm.Line().at((xj - 1.0, d2[1] + 0.6)).to((xj - 1.0, pWW[1]))
d += elm.Line().at((xj - 1.0, pWW[1])).to(pWW)
# source chung -> shunt
ys_ = s2[1] - 0.8
d += elm.Line().at(s1).to((s1[0], s1[1] - 0.4))
d += elm.Line().at((s1[0], s1[1] - 0.4)).to((s1[0] + 0.8, s1[1] - 0.4))
d += elm.Line().at((s1[0] + 0.8, s1[1] - 0.4)).to((s1[0] + 0.8, ys_))
d += elm.Line().at(s2).to((s2[0], ys_))
d += elm.Dot().at((s2[0], ys_))
d += elm.Line().at((s1[0] + 0.8, ys_)).to((s2[0], ys_))
d += elm.Line().at((s2[0], ys_)).to((s2[0] + 1.6, ys_))
net(s2[0] + 1.6, ys_, "SENSE+  (→ R9/U3A, khối 4)", "right")
d += elm.Resistor().at((s2[0], ys_)).to((s2[0], ys_ - 2.0))
lbl(s2[0] + 0.3, ys_ - 1.0, "R7  0R15 / 1 W\n(2× 0R30 1206 song song, Kelvin)")
d += elm.Ground().at((s2[0], ys_ - 2.0)).label("GND_S", "right")
lbl(0.0, ys_ - 2.6, "Dòng LED = dòng CC của flyback, chia thời gian giữa CW và WW bằng PWM bù nhau (CW duty = 1 – WW duty, chồng lấn ~2 µs).\n"
    "Khi cả hai khoá ngắt (đèn tắt) dòng = 0 → vòng CV giữ V+ = 45 V. Cả hai FET chỉ thấy Vds ≤ 45 V. Dòng cấp cho buck/MCU không qua R7.", 8, "left")
d.save(OUT)
print("ok", OUT)

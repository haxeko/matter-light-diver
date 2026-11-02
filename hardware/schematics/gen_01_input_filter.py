#!/usr/bin/env python3
"""Khoi 1: dau vao AC, bao ve, loc EMI, chinh luu, tu bulk (phia so cap)."""
import schemdraw
import schemdraw.elements as elm

OUT = "hardware/schematics/01_input_filter.svg"
d = schemdraw.Drawing(file=OUT, show=False)
d.config(unit=2.0, fontsize=9, lw=1.3)

d += elm.Label().at((0, 6.2)).label("Khối 1 – Đầu vào AC, bảo vệ, lọc EMI, chỉnh lưu, tụ bulk (phía sơ cấp)", fontsize=12, halign="left")

# day L (y=4) va N (y=0)
d += elm.Dot(open=True).at((0, 4)).label("J1.1  L\n(176–264 VAC)", "left")
d += elm.Fuse().at((0, 4)).right().label("F1\nT2A / 250 V\n(chậm, 5×20)", "top")
d += elm.Dot().at((2, 4))
d += elm.Resistor().at((2, 4)).down().toy(0).label("RV1\nMOV 10D471\n(S10K275)", "left")
d += elm.Dot().at((2, 0))
d += elm.Dot(open=True).at((0, 0)).label("J1.2  N", "left")
d += elm.Line().at((0, 0)).to((2, 0))
d += elm.Inductor().at((2, 4)).right().label("L1a\nCM choke UU9.8\n2×10 mH / 0.5 A", "top")
d += elm.Inductor().at((2, 0)).right().label("L1b", "bottom")
d += elm.Dot().at((4, 4))
d += elm.Dot().at((4, 0))
d += elm.Capacitor().at((4, 4)).down().toy(0).label("CX1\n100 nF\nX2 275 VAC", "right")
# NTC han dong khoi dong (tuy chon)
d += elm.Thermistor().at((4, 4)).right().label("RT1 NTC 5D-9\n(hạn dòng khởi động)", "top")
d += elm.Line().at((6, 4)).to((8, 4))
d += elm.Line().at((4, 0)).to((8, 0))

# cau chinh luu: AC1 tren, AC2 duoi, + phai, - trai
AC1, AC2, PLUS, MINUS = (8, 3.4), (8, 0.6), (9.4, 2.0), (6.6, 2.0)
d += elm.Line().at((8, 4)).to(AC1)
d += elm.Line().at((8, 0)).to(AC2)
d += elm.Diode().at(MINUS).to(AC1).label("D1a", "left", fontsize=7)
d += elm.Diode().at(AC1).to(PLUS).label("D1b", "right", fontsize=7)
d += elm.Diode().at(MINUS).to(AC2).label("D1c", "left", fontsize=7)
d += elm.Diode().at(AC2).to(PLUS).label("D1d", "right", fontsize=7)
d += elm.Label().at((8, 2.0)).label("BR1\nMB10S\n1000 V / 0.8 A", fontsize=8)
d += elm.Dot().at(PLUS)
d += elm.Dot().at(MINUS)

# - -> GND_P
d += elm.Line().at(MINUS).to((6.6, -1.2))
d += elm.Line().at((6.6, -1.2)).to((12.5, -1.2))
d += elm.Ground().at((12.5, -1.2)).label("GND_P\n(đất sơ cấp)", "right")
# + -> bulk cap -> +HV
d += elm.Line().at(PLUS).to((11.5, 2.0))
d += elm.Dot().at((11.5, 2.0))
d += elm.Capacitor(polar=True).at((11.5, 2.0)).down().toy(-1.2).label("C1\n47 µF / 400 V\n(105 °C, 10×20)", "right")
d += elm.Line().at((11.5, 2.0)).to((13.5, 2.0))
d += elm.Dot(radius=0.06).at((13.5, 2.0))
d += elm.Label().at((13.5, 2.0)).label("+HV  (215–373 VDC)", "right", color="#1f4e9c")

d += elm.Label().at((0, -2.4)).label(
    "Ghi chú: khoảng cách L–N ≥ 2.5 mm; phần trước cầu chì ≥ 3 mm. MOV đặt sau cầu chì. "
    "Tụ CX1 có R xả 2×470 kΩ (R_X) song song nếu cần theo IEC 62368-1.",
    fontsize=8, halign="left")
d.save(OUT)
print("ok", OUT)

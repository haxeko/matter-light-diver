#!/usr/bin/env python3
"""Khoi 4 (thu cap): khuech dai sense dong, bo loi (CC), kep CV TL431, wired-OR -> opto, tham chieu PWM->DAC, ADC."""
import schemdraw
import schemdraw.elements as elm

OUT = "hardware/schematics/04_cc_cv_loop.svg"
d = schemdraw.Drawing(file=OUT, show=False)
d.config(unit=2.0, fontsize=9, lw=1.3)
BLUE = "#1f4e9c"

def net(x, y, name, loc="right"):
    d.add(elm.Dot(radius=0.06).at((x, y)))
    d.add(elm.Label().at((x, y)).label(name, loc=loc, color=BLUE))

def lbl(x, y, text, fs=8, ha="left"):
    d.add(elm.Label().at((x, y)).label(text, fontsize=fs, halign=ha))

d += elm.Label().at((0, 14.2)).label("Khối 4 – Thứ cấp: khuếch đại dòng (×5), bộ lỗi CC, kẹp CV TL431, wired-OR → opto, tham chiếu PWM→DAC, đo ADC", fontsize=12, halign="left")

# ---------- U3A: khuech dai khong dao x5
U3A = elm.Opamp(leads=True).at((4.0, 9.0)).anchor("in2")      # in2 = +
d += U3A
lbl(U3A.out[0] - 1.1, U3A.out[1] + 1.1, "U3A  TLV9002 / GS8552\n(zero-drift, RRIO, 5 V)", 8, "center")
d += elm.Line().at(U3A.in2).to((U3A.in2[0] - 1.0, U3A.in2[1]))
d += elm.Resistor().at((U3A.in2[0] - 1.0, U3A.in2[1])).to((U3A.in2[0] - 3.0, U3A.in2[1]))
lbl(U3A.in2[0] - 2.0, U3A.in2[1] + 0.35, "R9  1 kΩ", 8, "center")
net(U3A.in2[0] - 3.0, U3A.in2[1], "SENSE+  (← R7, khối 5)\n0–142 mV", "left")
d += elm.Line().at(U3A.in1).to((U3A.in1[0] - 1.0, U3A.in1[1]))
d += elm.Dot().at((U3A.in1[0] - 1.0, U3A.in1[1]))
d += elm.Line().at((U3A.in1[0] - 1.0, U3A.in1[1])).to((U3A.in1[0] - 1.8, U3A.in1[1]))
d += elm.Resistor().at((U3A.in1[0] - 1.8, U3A.in1[1])).to((U3A.in1[0] - 1.8, U3A.in1[1] + 2.0))
lbl(U3A.in1[0] - 2.1, U3A.in1[1] + 1.0, "R10\n10 kΩ 1 %", 8, "right")
d += elm.Ground().at((U3A.in1[0] - 1.8, U3A.in1[1] + 2.0)).flip()
yf = U3A.in1[1] + 1.3
d += elm.Line().at((U3A.in1[0] - 1.0, U3A.in1[1])).to((U3A.in1[0] - 1.0, yf))
d += elm.Resistor().at((U3A.in1[0] - 1.0, yf)).to((U3A.out[0] + 0.6, yf))
lbl((U3A.in1[0] - 1.0 + U3A.out[0] + 0.6) / 2, yf + 0.4, "R11  40.2 kΩ 1 %  (gain = 1 + R11/R10 = 5.02)", 8, "center")
d += elm.Line().at((U3A.out[0] + 0.6, yf)).to((U3A.out[0] + 0.6, U3A.out[1]))
d += elm.Dot().at((U3A.out[0] + 0.6, U3A.out[1]))
d += elm.Line().at(U3A.out).to((U3A.out[0] + 0.6, U3A.out[1]))
xo = U3A.out[0] + 0.6
d += elm.Line().at((xo, U3A.out[1])).to((xo + 1.6, U3A.out[1]))
net(xo + 1.6, U3A.out[1], "ISENSE_AMP  0.19–0.71 V (0.75 V = 1.0 A)", "right")
d += elm.Line().at((xo, U3A.out[1])).to((xo, U3A.out[1] - 1.4))
d += elm.Resistor().at((xo, U3A.out[1] - 1.4)).to((xo + 2.6, U3A.out[1] - 1.4))
lbl(xo + 1.3, U3A.out[1] - 1.05, "R19  10 kΩ", 8, "center")
d += elm.Dot().at((xo + 2.6, U3A.out[1] - 1.4))
d += elm.Capacitor().at((xo + 2.6, U3A.out[1] - 1.4)).to((xo + 2.6, U3A.out[1] - 2.8))
lbl(xo + 2.9, U3A.out[1] - 2.1, "C14 1 nF")
d += elm.Ground().at((xo + 2.6, U3A.out[1] - 2.8))
d += elm.Line().at((xo + 2.6, U3A.out[1] - 1.4)).to((xo + 4.0, U3A.out[1] - 1.4))
net(xo + 4.0, U3A.out[1] - 1.4, "ADC_ISENSE  (→ GPIO6)", "right")

# ---------- tham chieu PWM -> DAC
y0 = 3.2
net(0.5, y0, "PWM_DIM (GPIO2, 3.3 V, 19.5 kHz, 12 bit)", "left")
d += elm.Resistor().at((0.5, y0)).to((2.5, y0))
lbl(1.5, y0 + 0.35, "R12  33 kΩ", 8, "center")
d += elm.Dot().at((2.5, y0))
d += elm.Resistor().at((2.5, y0)).to((2.5, y0 - 1.6))
lbl(2.8, y0 - 0.8, "R13 9.76 kΩ\n(chia 0.228)")
d += elm.Ground().at((2.5, y0 - 1.6))
d += elm.Capacitor().at((2.5 - 0.0, y0)).to((2.5, y0 + 1.4))
lbl(2.8, y0 + 0.8, "C10 470 nF")
d += elm.Line().at((2.5, y0 + 1.4)).to((2.5, y0 + 1.9))
d += elm.Ground().at((2.5, y0 + 1.9)).flip()
d += elm.Resistor().at((2.5, y0)).to((4.5, y0))
lbl(3.5, y0 + 0.35, "R14  4.7 kΩ", 8, "center")
d += elm.Dot().at((4.5, y0))
d += elm.Capacitor().at((4.5, y0)).to((4.5, y0 - 1.6))
lbl(4.8, y0 - 0.8, "C11 470 nF")
d += elm.Ground().at((4.5, y0 - 1.6))
d += elm.Line().at((4.5, y0)).to((6.0, y0))
net(6.0, y0, "VREF  0–0.753 V\n(= duty × 0.753 V)", "top")

# ---------- U3B: bo loi CC (tich phan)
U3B = elm.Opamp(leads=True).at((8.5, y0)).anchor("in2")
d += U3B
lbl(U3B.out[0] - 1.1, U3B.out[1] + 1.1, "U3B  (nửa còn lại của U3)", 8, "center")
d += elm.Line().at((6.0, y0)).to(U3B.in2)
d += elm.Line().at(U3B.in1).to((U3B.in1[0] - 1.0, U3B.in1[1]))
d += elm.Dot().at((U3B.in1[0] - 1.0, U3B.in1[1]))
d += elm.Resistor().at((U3B.in1[0] - 1.0, U3B.in1[1])).to((U3B.in1[0] - 3.0, U3B.in1[1]))
lbl(U3B.in1[0] - 2.0, U3B.in1[1] + 0.35, "R15  10 kΩ", 8, "center")
net(U3B.in1[0] - 3.0, U3B.in1[1], "ISENSE_AMP", "left")
# bu: C12 + R16 noi tiep tu out ve in1
xb = U3B.out[0] + 0.6
d += elm.Line().at((U3B.in1[0] - 1.0, U3B.in1[1])).to((U3B.in1[0] - 1.0, U3B.in1[1] - 1.5))
d += elm.Resistor().at((U3B.in1[0] - 1.0, U3B.in1[1] - 1.5)).to((U3B.in1[0] + 1.2, U3B.in1[1] - 1.5))
lbl(U3B.in1[0] + 0.1, U3B.in1[1] - 1.9, "R16 10 kΩ", 8, "center")
d += elm.Capacitor().at((U3B.in1[0] + 1.2, U3B.in1[1] - 1.5)).to((xb, U3B.in1[1] - 1.5))
lbl((U3B.in1[0] + 1.2 + xb) / 2, U3B.in1[1] - 1.9, "C12 100 nF", 8, "center")
d += elm.Line().at((xb, U3B.in1[1] - 1.5)).to((xb, U3B.out[1]))
d += elm.Dot().at((xb, U3B.out[1]))
d += elm.Line().at(U3B.out).to((xb, U3B.out[1]))
lbl(U3B.in2[0] - 0.2, U3B.in2[1] - 1.1, "Bù type-II: fz ≈ 160 Hz; băng thông vòng CC ≈ 1 kHz\n(nhỏ hơn nhiều fs 75 kHz → ổn định với opto CTR thay đổi)", 8, "left")
# D4 -> OPTO_K
d += elm.Line().at((xb, U3B.out[1])).to((xb + 0.6, U3B.out[1]))
d += elm.Diode().at((xb + 3.0, U3B.out[1])).to((xb + 0.6, U3B.out[1]))
lbl(xb + 1.8, U3B.out[1] + 0.35, "D4  1N4148W", 8, "center")
d += elm.Dot().at((xb + 3.0, U3B.out[1]))
xk = xb + 3.0
lbl(xk - 1.2, U3B.out[1] - 0.9, "U3B kéo thấp khi I > Iref\n→ D4 dẫn → opto sáng → giảm công suất", 8, "left")

# ---------- opto LED + TL431
d += elm.Line().at((xk, U3B.out[1])).to((xk, U3B.out[1] + 3.0))
d += elm.Dot().at((xk, U3B.out[1] + 3.0))
yk = U3B.out[1] + 3.0
d += elm.Line().at((xk, yk)).to((xk + 1.4, yk))
net(xk + 1.4, yk, "OPTO_K  (→ U2 cathode, khối 3)", "right")
d += elm.Resistor().at((xk, yk)).to((xk, yk + 2.2))
lbl(xk + 0.3, yk + 1.1, "R17  1 kΩ\n(I_LED opto ≈ 3 mA)")
d += elm.Dot().at((xk, yk + 2.2))
d += elm.Line().at((xk, yk + 2.2)).to((xk, yk + 3.0))
d += elm.Vdd().at((xk, yk + 3.0)).label("+5 V")
d += elm.Line().at((xk, yk + 2.2)).to((xk + 1.4, yk + 2.2))
net(xk + 1.4, yk + 2.2, "OPTO_A  (→ U2 anode, khối 3)", "right")
# TL431
d += elm.Line().at((xk, yk)).to((xk, yk - 0.0))
d += elm.Line().at((xk, U3B.out[1])).to((xk, U3B.out[1] - 0.6))
U4 = elm.Zener().at((xk, U3B.out[1] - 0.6)).to((xk, U3B.out[1] - 2.6))
d += U4
lbl(xk + 0.3, U3B.out[1] - 1.6, "U4  TL431 (SOT-23)\nK ↑  A ↓  REF ←")
d += elm.Ground().at((xk, U3B.out[1] - 2.6))
d += elm.Dot().at((xk, U3B.out[1] - 1.6))
d += elm.Line().at((xk, U3B.out[1] - 1.6)).to((xk - 1.2, U3B.out[1] - 1.6))
d += elm.Dot().at((xk - 1.2, U3B.out[1] - 1.6))
lbl(xk - 1.5, U3B.out[1] - 1.3, "REF", 8, "right")
d += elm.Resistor().at((xk - 1.2, U3B.out[1] - 1.6)).to((xk - 1.2, U3B.out[1] - 3.6))
lbl(xk - 1.5, U3B.out[1] - 2.6, "R21\n10 kΩ 1 %", 8, "right")
d += elm.Ground().at((xk - 1.2, U3B.out[1] - 3.6))
d += elm.Line().at((xk - 1.2, U3B.out[1] - 1.6)).to((xk - 1.2, U3B.out[1] - 0.6))
d += elm.Resistor().at((xk - 1.2, U3B.out[1] - 0.6)).to((xk - 3.6, U3B.out[1] - 0.6))
lbl(xk - 2.4, U3B.out[1] - 1.0, "R20  170 kΩ 1 %\n(150k + 20k)", 8, "center")
net(xk - 3.6, U3B.out[1] - 0.6, "V+", "left")
lbl(xk + 0.3, U3B.out[1] - 3.4, "V_CV = 2.495 × (1 + R20/R21) = 44.9 V\nC13 10 nF giữa K và REF (bù)")

# ---------- chia ap do V+
yv = -1.2
net(0.5, yv, "V+", "left")
d += elm.Resistor().at((0.5, yv)).to((2.5, yv))
lbl(1.5, yv + 0.35, "R22  150 kΩ", 8, "center")
d += elm.Dot().at((2.5, yv))
d += elm.Resistor().at((2.5, yv)).to((2.5, yv - 1.6))
lbl(2.8, yv - 0.8, "R23 10 kΩ")
d += elm.Ground().at((2.5, yv - 1.6))
d += elm.Capacitor().at((4.0, yv)).to((4.0, yv - 1.6))
lbl(4.3, yv - 0.8, "C15 100 nF")
d += elm.Ground().at((4.0, yv - 1.6))
d += elm.Line().at((2.5, yv)).to((5.5, yv))
d += elm.Dot().at((4.0, yv))
net(5.5, yv, "ADC_VOUT  (→ GPIO3)   3.0 V @ 48 V", "right")
lbl(0.0, yv - 2.4, "Nguồn U3: +5 V (C 100 nF sát chân). Mọi GND là GND_S. Imax cứng = 0.753 V / (5 × 0.15 Ω) ≈ 1.0 A ngay cả khi PWM_DIM = 100 %.\nKhi đèn tắt (Q2, Q3 ngắt) I = 0 < Iref → U3B bão hoà cao, D4 khoá; TL431 giữ V+ = 45 V nuôi buck/MCU.", 8, "left")
d.save(OUT)
print("ok", OUT)

#!/usr/bin/env python3
"""Khoi 7 (thu cap): ESP32-C6-MINI-1, DIP 3 nut gat, nut nhan, LED, NTC, USB/UART, EN."""
import schemdraw
import schemdraw.elements as elm

OUT = "hardware/schematics/07_mcu.svg"
d = schemdraw.Drawing(file=OUT, show=False)
d.config(unit=2.0, fontsize=9, lw=1.3)
BLUE = "#1f4e9c"

def net(x, y, name, loc="right"):
    d.add(elm.Dot(radius=0.06).at((x, y)))
    d.add(elm.Label().at((x, y)).label(name, loc=loc, color=BLUE))

def lbl(x, y, text, fs=8, ha="left"):
    d.add(elm.Label().at((x, y)).label(text, fontsize=fs, halign=ha))

d += elm.Label().at((0, 13.0)).label("Khối 7 – MCU: U9 ESP32-C6-MINI-1 (Matter over Thread), 3 nút gạt DIP, nút nhấn, LED, NTC, nạp USB-JTAG / UART", fontsize=12, halign="left")

left = ["IO20 DIP3", "IO19 DIP2", "IO18 DIP1", "IO4  ADC_NTC", "IO6  ADC_ISENSE", "IO3  ADC_VOUT", "IO2  PWM_DIM", "IO1  PWM_WW", "IO0  PWM_CW", "EN", "3V3"]
right = ["GND", "IO17 RXD0", "IO16 TXD0", "IO13 USB_D+", "IO12 USB_D–", "IO10 LED", "IO9  BOOT/BTN", "IO15 (nc)", "IO5  (nc)", "IO7  (nc)", "IO8  (strap, nc)"]
pins = [elm.IcPin(name=n, side="left", anchorname=n.split()[0]) for n in left] + \
       [elm.IcPin(name=n, side="right", anchorname=n.split()[0] if n != "GND" else "GND") for n in right]
U9 = elm.Ic(pins=pins, size=(6.4, 12.0), pinspacing=1.0, edgepadH=0.5, lblsize=8, pinlblsize=0)
d += U9.right().at((10.0, 5.5)).anchor("center")
lbl(10.0, 12.0, "U9  ESP32-C6-MINI-1-N4  (RISC-V 160 MHz, 802.15.4 Thread + BLE 5, 4 MB flash)\nanten PCB hướng ra mép board; không đổ đồng dưới vùng anten", 8, "center")
A = U9.absanchors

def leftnet(pin, text):
    p = A[pin]
    d.add(elm.Line().at(p).to((p[0] - 1.0, p[1])))
    net(p[0] - 1.0, p[1], text, "left")

def rightnet(pin, text):
    p = A[pin]
    d.add(elm.Line().at(p).to((p[0] + 1.0, p[1])))
    net(p[0] + 1.0, p[1], text, "right")

leftnet("IO0", "PWM_CW  (→ U5, khối 5)")
leftnet("IO1", "PWM_WW  (→ U6, khối 5)")
leftnet("IO2", "PWM_DIM  (→ R12, khối 4)")
leftnet("IO3", "ADC_VOUT  (← R22/R23)")
leftnet("IO6", "ADC_ISENSE  (← R19/C14)")
# NTC: cau chia ve ngang de khong cat cac chan ADC khac
p = A["IO4"]
d += elm.Line().at(p).to((p[0] - 1.2, p[1]))
d += elm.Dot().at((p[0] - 1.2, p[1]))
d += elm.Thermistor().at((p[0] - 1.2, p[1])).to((p[0] - 3.4, p[1]))
lbl(p[0] - 2.3, p[1] - 0.45, "RT2  NTC 10 kΩ B3950\n(dán cạnh Q2/Q3, D2)", 8, "center")
d += elm.Ground().at((p[0] - 3.4, p[1]))
d += elm.Line().at((p[0] - 1.2, p[1])).to((p[0] - 1.2, p[1] + 0.5))
d += elm.Resistor().at((p[0] - 1.2, p[1] + 0.5)).to((p[0] - 3.4, p[1] + 0.5))
lbl(p[0] - 2.3, p[1] + 0.75, "R31 10 kΩ", 7, "center")
net(p[0] - 3.4, p[1] + 0.5, "+3V3", "left")
# DIP: 3 nut gat ve GND, pull-up noi
S = elm.SwitchDIP(n=3).right().at((A["IO18"][0] - 4.4, A["IO20"][1] - 1.6))
d += S
B = S.absanchors
lbl(A["IO18"][0] - 3.6, A["IO20"][1] + 1.2, "SW1–SW3  DIP 3 vị trí (chọn công suất)\nON = nối GND; pull-up nội 45 kΩ + R 100 kΩ", 8, "center")
for k, pin in (("1", "IO18"), ("2", "IO19"), ("3", "IO20")):
    b = B["b" + k]; a = B["a" + k]; p = A[pin]
    d += elm.Line().at(b).to((b[0], p[1]))
    d += elm.Line().at((b[0], p[1])).to(p)
    d += elm.Line().at(a).to((a[0], a[1] - 0.4))
gy = B["a1"][1] - 0.4
d += elm.Line().at((B["a1"][0], gy)).to((B["a3"][0], gy))
d += elm.Ground().at((B["a2"][0], gy))
# EN
p = A["EN"]
y33 = A["3V3"][1]
d += elm.Line().at(p).to((p[0] - 1.2, p[1]))
d += elm.Dot().at((p[0] - 1.2, p[1]))
d += elm.Resistor().at((p[0] - 1.2, p[1])).to((p[0] - 1.2, y33))
lbl(p[0] - 0.9, (p[1] + y33) / 2, "R32\n10 kΩ", 7, "left")
d += elm.Dot().at((p[0] - 1.2, y33))
d += elm.Line().at((p[0] - 1.2, p[1])).to((p[0] - 2.0, p[1]))
d += elm.Dot().at((p[0] - 2.0, p[1]))
d += elm.Capacitor().at((p[0] - 2.0, p[1])).to((p[0] - 2.0, p[1] - 0.9))
lbl(p[0] - 2.5, p[1] - 0.45, "C21 1 µF", 7, "right")
d += elm.Ground().at((p[0] - 2.0, p[1] - 0.9))
d += elm.Line().at((p[0] - 2.0, p[1])).to((p[0] - 3.2, p[1]))
d += elm.Dot(open=True).at((p[0] - 3.2, p[1])).label("TP_EN", "left")
# 3V3
p = A["3V3"]
d += elm.Line().at(p).to((p[0] - 2.6, p[1]))
d += elm.Dot().at((p[0] - 2.6, p[1]))
d += elm.Capacitor().at((p[0] - 2.6, p[1])).to((p[0] - 2.6, p[1] - 1.2))
lbl(p[0] - 2.9, p[1] - 0.6, "C22 10 µF\n+ C23 100 nF", 8, "right")
d += elm.Ground().at((p[0] - 2.6, p[1] - 1.2))
d += elm.Line().at((p[0] - 2.6, p[1])).to((p[0] - 4.0, p[1]))
net(p[0] - 4.0, p[1], "+3V3  (← U8)", "left")
# GND
p = A["GND"]
d += elm.Line().at(p).to((p[0] + 0.8, p[1]))
d += elm.Ground().at((p[0] + 0.8, p[1])).label("GND_S", "right")
# UART / USB
rightnet("IO17", "RXD0  → J4 (header 1×3: TX RX GND)")
rightnet("IO16", "TXD0  → J4")
rightnet("IO13", "USB D+  → J3 pad (USB-JTAG, nạp và debug)")
rightnet("IO12", "USB D–  → J3 pad")
# LED
p = A["IO10"]
d += elm.Resistor().at(p).to((p[0] + 2.0, p[1]))
lbl(p[0] + 1.0, p[1] + 0.35, "R33 1 kΩ", 8, "center")
d += elm.LED().at((p[0] + 2.0, p[1])).to((p[0] + 4.0, p[1]))
lbl(p[0] + 3.0, p[1] - 0.45, "D10 LED xanh (mức thấp = sáng)", 8, "center")
d += elm.Line().at((p[0] + 4.0, p[1])).to((p[0] + 4.8, p[1]))
net(p[0] + 4.8, p[1], "+3V3", "right")
# Button
p = A["IO9"]
d += elm.Line().at(p).to((p[0] + 1.0, p[1]))
d += elm.Dot().at((p[0] + 1.0, p[1]))
d += elm.Resistor().at((p[0] + 1.0, p[1])).to((p[0] + 1.0, p[1] + 1.2))
d += elm.Vdd().at((p[0] + 1.0, p[1] + 1.2)).label("+3V3")
lbl(p[0] + 1.3, p[1] + 0.6, "R34 10 kΩ")
d += elm.Button().at((p[0] + 1.0, p[1])).to((p[0] + 3.2, p[1]))
lbl(p[0] + 3.5, p[1] + 0.6, "SW4: nhấn ngắn = toggle/identify; giữ 5 s = factory reset\n(cũng là BOOT khi giữ lúc cấp nguồn); C24 100 nF song song SW4", 8, "left")
d += elm.Ground().at((p[0] + 3.2, p[1]))
lbl(0.0, -1.6, "Chân strapping ESP32-C6: IO8, IO9, IO15 (và IO4/IO5 chỉnh timing SDIO – không ảnh hưởng). IO9 có pull-up → boot bình thường; giữ SW4 khi cấp nguồn → chế độ nạp.\n"
    "IO8 để trống (pull-up nội). Nguồn: 3V3 ≤ 350 mA đỉnh khi phát BLE/802.15.4. Tất cả GND là GND_S. Module đặt sát mép, anten không có đồng/linh kiện dưới và trong 5 mm xung quanh.", 8, "left")
d.save(OUT)
print("ok", OUT)

#!/usr/bin/env python3
"""
secondary_calc.py - Tinh toan phan thu cap: bang dong DIP, mach sense dong,
tham chieu PWM->DAC, kep CV (TL431), ton hao MOSFET kenh CW/WW, nguon phu.

Chay: python3 secondary_calc.py
"""
import math

# ------------------------------------------------------------ bang DIP
I_BASE_MA = 250
STEP_MA = {1: 100, 2: 200, 3: 400}          # SW1, SW2, SW3 (nhi phan)
V_LED_TYP = 36.0                            # V - dien ap chuoi LED dien hinh

# ------------------------------------------------------------ vong CC
R_SENSE = 0.15          # ohm (2 x 0R30 1206 song song)
GAIN = 5.0              # khuech dai khong dao cua U_CS (1 + 40k/10k)
V_REF_FULL = 0.75       # V tham chieu khi PWM 100 % -> Imax_hw = 0.75/(5*0.15) = 1.0 A
V_PWM = 3.3
R_REF_TOP = 33.0e3      # cau chia 3.3 V -> 0.75 V : 33k / 9.76k ~ 0.228
R_REF_BOT = 9.76e3
PWM_RES_BITS = 12
PWM_FREQ = 19531.0      # 80 MHz / 2^12
RC_R = 4.7e3
RC_C = 470e-9

# ------------------------------------------------------------ kep CV
V_CV = 45.0
TL431_VREF = 2.495
R_CV_BOT = 10.0e3

# ------------------------------------------------------------ MOSFET kenh
RDS_ON = 0.25           # ohm @ Vgs = 4.5..5 V (IRLML0060 / AO3160)
I_MAX = 0.95

# ------------------------------------------------------------ nguon phu
V_OUT_MIN, V_OUT_MAX = 20.0, 45.0
I_5V = 0.18             # A dinh (ESP32-C6 TX + LED + opto)
I_5V_IDLE = 0.07        # A trung binh khi den tat (Thread RX, CPU idle)
I_3V3 = 0.15
EFF_BUCK = 0.85


def dip_table():
    print("| SW3 | SW2 | SW1 | I_out (mA) | P @36 V (W) |")
    print("|---|---|---|---|---|")
    for code in range(8):
        s1, s2, s3 = code & 1, (code >> 1) & 1, (code >> 2) & 1
        i = I_BASE_MA + s1 * STEP_MA[1] + s2 * STEP_MA[2] + s3 * STEP_MA[3]
        print(f"| {'ON' if s3 else 'off'} | {'ON' if s2 else 'off'} | {'ON' if s1 else 'off'} | {i} | {i*V_LED_TYP/1000:.1f} |")


def cc_loop():
    i_hw = V_REF_FULL / (GAIN * R_SENSE)
    ratio = R_REF_BOT / (R_REF_TOP + R_REF_BOT)
    v_ref_max = V_PWM * ratio
    print(f"Rsense = {R_SENSE} ohm, Psense @0.95 A = {0.95**2*R_SENSE*1000:.0f} mW")
    print(f"Vsense @250 mA = {0.25*R_SENSE*1000:.1f} mV ; @950 mA = {0.95*R_SENSE*1000:.1f} mV")
    print(f"Gain = {GAIN} -> Vcs_amp = {0.25*R_SENSE*GAIN:.3f} .. {0.95*R_SENSE*GAIN:.3f} V")
    print(f"Cau chia tham chieu: {R_REF_TOP/1e3:.2f}k/{R_REF_BOT/1e3:.2f}k = {ratio:.4f} -> Vref max = {v_ref_max:.3f} V")
    print(f"Imax phan cung (PWM 100 %) = {v_ref_max/(GAIN*R_SENSE)*1000:.0f} mA  (thiet ke: {i_hw*1000:.0f} mA)")
    lsb = v_ref_max / (2 ** PWM_RES_BITS) / (GAIN * R_SENSE) * 1000
    print(f"Do phan giai dong: {lsb:.3f} mA/LSB ({PWM_RES_BITS} bit)")
    fc = 1 / (2 * math.pi * RC_R * RC_C)
    att = (fc / PWM_FREQ) ** 2                      # 2 tang RC
    print(f"Loc RC 2 tang {RC_R/1e3:.1f}k/{RC_C*1e9:.0f}nF: fc = {fc:.0f} Hz, ripple @ {PWM_FREQ/1e3:.1f} kHz ~ {att*V_PWM*1000:.2f} mV, t_settle ~ {5*RC_R*RC_C*2*1000:.0f} ms")
    for code in range(8):
        pass
    print("Duty PWM can cho tung muc DIP (100 % sang):")
    for code in range(8):
        s1, s2, s3 = code & 1, (code >> 1) & 1, (code >> 2) & 1
        i = (I_BASE_MA + s1 * STEP_MA[1] + s2 * STEP_MA[2] + s3 * STEP_MA[3]) / 1000
        duty = i * GAIN * R_SENSE / v_ref_max
        print(f"  DIP={s3}{s2}{s1}: I={i*1000:.0f} mA -> duty={duty*100:.1f} % ({round(duty*(2**PWM_RES_BITS))} / 4096)")


def cv_clamp():
    r_top = R_CV_BOT * (V_CV / TL431_VREF - 1)
    print(f"TL431 kep CV {V_CV} V: R_top = {r_top/1e3:.1f}k (chon 170k = 150k+20k), R_bot = {R_CV_BOT/1e3:.0f}k")
    r_top_sel = 170e3
    print(f"  -> V_CV thuc = {TL431_VREF*(1+r_top_sel/R_CV_BOT):.1f} V")


def mosfet():
    p = I_MAX ** 2 * RDS_ON
    print(f"MOSFET kenh: I={I_MAX} A, Rds(on)={RDS_ON} ohm -> P = {p*1000:.0f} mW (SOT-23 + dong 1 cm2 OK, Tj ~ +{p*250:.0f} C)")


def aux_power():
    p5 = 5.0 * I_5V
    for v in (V_OUT_MIN, V_OUT_MAX):
        iin = p5 / EFF_BUCK / v
        print(f"Buck 5 V: Vin={v:.0f} V -> Iin = {iin*1000:.0f} mA, Pin = {p5/EFF_BUCK:.2f} W")
    print(f"LDO 3V3: P = {(5-3.3)*I_3V3*1000:.0f} mW @ {I_3V3*1000:.0f} mA")
    p_idle = 5.0 * I_5V_IDLE / EFF_BUCK + 0.10      # + opto/TL431/op-amp
    print(f"Cong suat standby (den tat, Thread RX) uoc tinh: ~{p_idle/0.7:.2f} W (flyback burst ~70 %)")


if __name__ == "__main__":
    print("## Bang chon cong suat bang 3 nut gat (DIP)\n")
    dip_table()
    print("\n## Vong dieu khien dong (CC)\n")
    cc_loop()
    print("\n## Kep dien ap (CV)\n")
    cv_clamp()
    print("\n## MOSFET kenh CW/WW\n")
    mosfet()
    print("\n## Nguon phu\n")
    aux_power()

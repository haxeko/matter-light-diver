#!/usr/bin/env python3
"""
flyback_calc.py - Tinh toan thiet ke nguon flyback cach ly cho driver den CCT 3 day.

Chay:  python3 flyback_calc.py            (in bang ket qua, Markdown)
       python3 flyback_calc.py --json     (xuat JSON de dung trong tai lieu khac)

Phuong phap: flyback DCM/ranh gioi (transition mode) tai Vin_min, tai lon nhat.
Cong thuc theo quy trinh thiet ke cua UCC28740 / tai lieu TI SLUA (flyback
design) - co the thay bang bo dieu khien tuong duong (OB2263, NCP1250...).
"""
import json
import math
import sys

# ----------------------------------------------------------------- Yeu cau
SPEC = dict(
    vac_min=176.0,      # VAC  (220 V -20 %)
    vac_nom=230.0,
    vac_max=264.0,      # VAC  (240 V +10 %)
    f_line=50.0,        # Hz
    vout_max=45.0,      # V   dien ap kep CV (khong tai / den tat)
    vout_led_max=42.0,  # V   dien ap chuoi LED cao nhat khi co tai
    vout_min=20.0,      # V   dien ap chuoi LED thap nhat
    iout_max=0.95,      # A   dong ra lon nhat theo bang DIP (SW1+SW2+SW3)
    iout_hw_limit=1.0,  # A   gioi han cung cua vong CC thu cap
    vd_out=1.2,         # V   sut ap diode ra (ES3J ultrafast)
    eff=0.86,           # hieu suat du kien (flyback 40 W)
    fs=75e3,            # Hz  tan so dong dien chon tai tai lon nhat
    vor=80.0,           # V   dien ap phan xa (reflected) ve so cap
    t_hold_ratio=0.8,   # ty le thoi gian dan cua tu loc (1 - thoi gian nap)
    v_bulk_min=200.0,   # V   dien ap DC bulk thap nhat cho phep
    bmax=0.30,          # T   mat do tu cam cuc dai (ferrite PC40/PC95 @100C)
    core="PQ20/20",     # loi bien ap (thay the: EF25, RM8)
    ae_mm2=62.0,        # mm2 tiet dien loi PQ20/20
    aw_mm2=30.0,        # mm2 cua so quan day kha dung (co bobbin)
    vaux=12.0,          # V   dien ap cuon phu nuoi IC khi Vout = vout_min
    j_a_mm2=6.0,        # A/mm2 mat do dong trong day
    kw=0.45,            # he so lap day cua so
    leak_ratio=0.015,   # dien cam ro / Lp (quan xen ke sandwich)
    clamp_ratio=1.7,    # Vclamp / VOR
    vds_rating=650.0,   # V   MOSFET chinh
)


def design(s=SPEC):
    r = {}
    pout = s["vout_led_max"] * s["iout_max"]      # cong suat ra lon nhat co tai
    pin = pout / s["eff"]
    r["pout_W"] = pout
    r["pin_W"] = pin

    # --- Tu loc bulk -----------------------------------------------------
    vpk_min = s["vac_min"] * math.sqrt(2)
    t_disc = s["t_hold_ratio"] / (2 * s["f_line"])
    c_bulk = 2 * pin * t_disc / (vpk_min ** 2 - s["v_bulk_min"] ** 2)
    r["vpk_min_V"] = vpk_min
    r["c_bulk_uF_calc"] = c_bulk * 1e6
    c_bulk_sel = 47e-6
    # dien ap bulk min thuc te voi tu da chon
    v_bulk_min_real = math.sqrt(vpk_min ** 2 - 2 * pin * t_disc / c_bulk_sel)
    r["c_bulk_uF_sel"] = c_bulk_sel * 1e6
    r["v_bulk_min_V"] = v_bulk_min_real
    v_bulk_max = s["vac_max"] * math.sqrt(2)
    r["v_bulk_max_V"] = v_bulk_max

    # --- Ty so vong, duty, dong dinh -----------------------------------
    n = s["vor"] / (s["vout_max"] + s["vd_out"])     # Np/Ns
    r["n_turns_ratio"] = n
    dmax = s["vor"] / (s["vor"] + v_bulk_min_real)
    r["dmax"] = dmax
    ipk = 2 * pin / (v_bulk_min_real * dmax)        # DCM/BCM: Pin = 0.5*Lp*Ipk^2*fs
    r["ipk_pri_A"] = ipk
    lp = v_bulk_min_real * dmax / (ipk * s["fs"])
    r["lp_uH"] = lp * 1e6
    irms_pri = ipk * math.sqrt(dmax / 3)
    r["irms_pri_A"] = irms_pri
    ipk_sec = ipk * n
    d2 = 1 - dmax                                     # thoi gian xa (BCM)
    irms_sec = ipk_sec * math.sqrt(d2 / 3)
    r["ipk_sec_A"] = ipk_sec
    r["irms_sec_A"] = irms_sec

    # --- Bien ap ----------------------------------------------------------
    ae = s["ae_mm2"] * 1e-6
    np_min = lp * ipk / (s["bmax"] * ae)
    np_sel = math.ceil(np_min)
    ns_sel = max(1, round(np_sel / n))
    n_real = np_sel / ns_sel
    vor_real = n_real * (s["vout_max"] + s["vd_out"])
    naux = round(ns_sel * (s["vaux"] + 0.7) / (s["vout_min"] + s["vd_out"]))
    vaux_max = naux / ns_sel * (s["vout_max"] + s["vd_out"]) - 0.7
    r.update(np=np_sel, ns=ns_sel, naux=naux, n_real=n_real, vor_real_V=vor_real,
             vaux_at_vout_min_V=naux / ns_sel * (s["vout_min"] + s["vd_out"]) - 0.7,
             vaux_at_vout_max_V=vaux_max)
    al = lp / np_sel ** 2
    r["AL_nH"] = al * 1e9
    # khe ho khong khi (gan dung, bo qua tu thong ro)
    mu0 = 4e-7 * math.pi
    lg = mu0 * np_sel ** 2 * ae / lp
    r["gap_mm"] = lg * 1e3
    # day quan
    a_pri = irms_pri / s["j_a_mm2"]
    a_sec = irms_sec / s["j_a_mm2"]
    d_pri = 2 * math.sqrt(a_pri / math.pi)
    d_sec = 2 * math.sqrt(a_sec / math.pi)
    r["wire_pri_mm"] = d_pri
    r["wire_sec_mm"] = d_sec
    # dien tich cua so: so cap day emay (+25 %), thu cap day TIW (+60 %)
    aw_used = 1.25 * np_sel * a_pri + 1.6 * ns_sel * a_sec + 1.25 * naux * 0.03
    r["window_fill"] = aw_used / (s["aw_mm2"] * s["kw"])

    # --- Ung suat linh kien ---------------------------------------------
    v_clamp = s["clamp_ratio"] * vor_real             # dien ap clamp RCD/TVS
    v_spike = v_clamp - vor_real
    vds = v_bulk_max + v_clamp
    r["vds_max_V"] = vds
    r["vds_margin"] = 1 - vds / s["vds_rating"]
    vrrm_sec = s["vout_max"] + v_bulk_max / n_real
    r["vrrm_sec_V"] = vrrm_sec
    # dien tro sense so cap cho UCC28740: Vcs = 0.75 V -> Ipk
    r_cs = 0.75 / (ipk * 1.1)
    r["r_cs_ohm"] = r_cs
    r["p_rcs_W"] = irms_pri ** 2 * r_cs
    # clamp RCD: P = 0.5*Lleak*Ipk^2*fs * Vclamp/(Vclamp-VOR)
    e_leak = 0.5 * s["leak_ratio"] * lp * ipk ** 2
    p_clamp = e_leak * s["fs"] * v_clamp / v_spike
    r["v_clamp_V"] = v_clamp
    r["p_clamp_W"] = p_clamp
    r_clamp = v_clamp ** 2 / p_clamp
    r["r_clamp_kohm"] = r_clamp / 1e3
    r["c_clamp_nF"] = 1 / (0.1 * r_clamp * s["fs"]) * 1e9   # ripple 10 %
    # ton hao diode ra
    r["p_diode_out_W"] = s["vd_out"] * s["iout_max"]
    # tu ra: dong ripple
    r["irms_cout_A"] = math.sqrt(irms_sec ** 2 - s["iout_max"] ** 2)
    return r


ROWS = [
    ("pout_W", "Cong suat ra lon nhat co tai (42 V x 0,95 A)", "W", 1),
    ("pin_W", "Cong suat vao uoc tinh", "W", 1),
    ("vpk_min_V", "Dinh dien ap chinh luu tai Vac_min", "V", 0),
    ("c_bulk_uF_calc", "Tu bulk tinh toan", "uF", 1),
    ("c_bulk_uF_sel", "Tu bulk chon", "uF", 0),
    ("v_bulk_min_V", "V_bulk thap nhat thuc te", "V", 0),
    ("v_bulk_max_V", "V_bulk cao nhat", "V", 0),
    ("n_turns_ratio", "Ty so vong yeu cau Np/Ns", "", 2),
    ("dmax", "Duty cuc dai tai Vin_min", "", 3),
    ("ipk_pri_A", "Dong dinh so cap", "A", 2),
    ("irms_pri_A", "Dong RMS so cap", "A", 2),
    ("lp_uH", "Dien cam so cap Lp", "uH", 0),
    ("ipk_sec_A", "Dong dinh thu cap", "A", 2),
    ("irms_sec_A", "Dong RMS thu cap", "A", 2),
    ("np", "So vong so cap Np", "vong", 0),
    ("ns", "So vong thu cap Ns", "vong", 0),
    ("naux", "So vong cuon phu Naux", "vong", 0),
    ("n_real", "Ty so vong thuc te", "", 2),
    ("vor_real_V", "VOR thuc te", "V", 0),
    ("vaux_at_vout_min_V", "Vaux khi Vout = 20 V", "V", 1),
    ("vaux_at_vout_max_V", "Vaux khi Vout = 45 V", "V", 1),
    ("AL_nH", "AL can dat (gap)", "nH", 0),
    ("gap_mm", "Khe ho loi uoc tinh", "mm", 2),
    ("wire_pri_mm", "Duong kinh day so cap (J=6 A/mm2)", "mm", 2),
    ("wire_sec_mm", "Duong kinh day thu cap", "mm", 2),
    ("window_fill", "Ty le lap day cua so (<=1 la OK)", "", 2),
    ("v_clamp_V", "Dien ap clamp RCD/TVS", "V", 0),
    ("vds_max_V", "Vds MOSFET lon nhat (co spike)", "V", 0),
    ("vds_margin", "Du phong MOSFET 650 V", "", 2),
    ("vrrm_sec_V", "Dien ap nguoc diode ra", "V", 0),
    ("r_cs_ohm", "Dien tro sense so cap (Vcs=0.75 V)", "ohm", 3),
    ("p_rcs_W", "Ton hao Rcs", "W", 2),
    ("p_clamp_W", "Ton hao clamp RCD", "W", 2),
    ("r_clamp_kohm", "R clamp", "kohm", 0),
    ("c_clamp_nF", "C clamp", "nF", 1),
    ("p_diode_out_W", "Ton hao diode ra", "W", 2),
    ("irms_cout_A", "Dong ripple RMS qua tu ra", "A", 2),
]


def main():
    r = design()
    if "--json" in sys.argv:
        print(json.dumps(r, indent=2))
        return
    print("| Dai luong | Gia tri | Don vi |")
    print("|---|---|---|")
    for key, label, unit, nd in ROWS:
        v = r[key]
        print(f"| {label} | {v:.{nd}f} | {unit} |")


if __name__ == "__main__":
    main()

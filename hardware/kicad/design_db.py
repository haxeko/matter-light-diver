#!/usr/bin/env python3
"""
design_db.py - Nguon du lieu duy nhat cho du an KiCad: linh kien, footprint, net, vi tri dat.

Moi linh kien: ref, value, footprint "Lib:Name", pins {ten_pad: ten_net}, pos (x, y, rot) tinh bang mm
tren board 90 x 30 mm (goc toa do: goc tren-trai cua board, truc y huong xuong nhu KiCad).
Cac script gen_kicad_pcb.py / gen_kicad_sch.py doc file nay.
"""

BOARD_W, BOARD_H = 95.0, 30.0
BOARD_RADIUS = 2.0

# --------------------------------------------------------------------- net classes (mm)
NET_CLASSES = {
    # name: (track_width, clearance, via_dia, via_drill)
    "Default":   (0.25, 0.2, 0.6, 0.3),
    "HV":        (0.8,  0.6, 0.8, 0.4),    # so cap sau chinh luu (400 V)
    "SIG_P":     (0.3,  0.25, 0.6, 0.3),   # tin hieu dieu khien phia so cap (U1, Q1 gate, CS)
    "AC":        (0.8,  1.0, 0.8, 0.4),    # L/N truoc chinh luu
    "PWR_S":     (1.0,  0.3, 0.8, 0.4),    # V+, dong LED
    "PWR_L":     (0.5,  0.2, 0.6, 0.3),    # +5V, +3V3, SW7
    "SIG":       (0.25, 0.2, 0.6, 0.3),
}

PRIMARY_NETS = {"L_IN", "N_IN", "L_F", "L_CM", "N_CM", "L_BR", "HV", "GND_P", "DRAIN", "CLAMP", "CS_SRC", "CS",
                "GATE", "DRV", "AUX", "VDD", "VS", "FB", "HV_START"}
AC_NETS = {"L_IN", "N_IN", "L_F", "L_CM", "N_CM", "L_BR"}
HV_NETS = {"HV", "DRAIN", "CLAMP", "HV_START"}
PWR_S_NETS = {"VPLUS", "GND_S", "SEC", "SENSE_P", "CW_N", "WW_N"}
PWR_L_NETS = {"+5V", "SW7", "+3V3"}

def net_class(net):
    if net in AC_NETS:
        return "AC"
    if net in HV_NETS:
        return "HV"
    if net in PRIMARY_NETS:
        return "SIG_P"
    if net in PWR_S_NETS:
        return "PWR_S"
    if net in PWR_L_NETS:
        return "PWR_L"
    return "SIG"

# --------------------------------------------------------------------- footprints
FP = {
    "0603": "Resistor_SMD:R_0603_1608Metric",
    "0402": "Resistor_SMD:R_0402_1005Metric",
    "C0402": "Capacitor_SMD:C_0402_1005Metric",
    "C0603": "Capacitor_SMD:C_0603_1608Metric",
    "0805": "Resistor_SMD:R_0805_2012Metric",
    "C0805": "Capacitor_SMD:C_0805_2012Metric",
    "1206": "Resistor_SMD:R_1206_3216Metric",
    "C1210": "Capacitor_SMD:C_1210_3225Metric",
    "C1812": "Capacitor_SMD:C_1812_4532Metric",
    "SMB": "Diode_SMD:D_SMB",
    "C1206": "Capacitor_SMD:C_1206_3216Metric",
    "2512": "Resistor_SMD:R_2512_6332Metric",
    "SMA": "Diode_SMD:D_SMA",
    "SMC": "Diode_SMD:D_SMC",
    "SOD123": "Diode_SMD:D_SOD-123",
    "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "SOT23-5": "Package_TO_SOT_SMD:SOT-23-5",
    "SOT23-6": "Package_TO_SOT_SMD:SOT-23-6",
    "SC70-5": "Package_TO_SOT_SMD:SOT-353_SC-70-5",
    "SOIC8": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "DPAK": "Package_TO_SOT_SMD:TO-252-2",
    "LED0805": "LED_SMD:LED_0805_2012Metric",
    "FUSE2410": "driver:Fuse_2410_6032Metric",
    "IND5x5": "Inductor_SMD:L_Bourns_SRN6045TA",   # thay bang CD54 neu can
    "CP5x11": "Capacitor_THT:CP_Radial_D5.0mm_P2.00mm",
    "CP8x12": "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
    "TB2_508": "driver:WirePads_1x02_P5.08mm",
    "TB3_350": "driver:WirePads_1x03_P3.81mm",
    "DIP3": "Button_Switch_SMD:SW_DIP_SPSTx03_Slide_6.7x9.18mm_W8.61mm_P2.54mm_LowProfile",
    "BTN": "Button_Switch_SMD:SW_SPST_SKQG_WithoutStem",
    "ESP32C6": "driver:ESP32-C6-MINI-1",
    "PQ2020": "driver:Transformer_PQ20-20_5+5",
    "UU98": "driver:CM_Choke_UU9.8",
    "DISC10_P75": "Capacitor_THT:C_Disc_D10.5mm_W5.0mm_P7.50mm",
    "DISC9_P75": "Capacitor_THT:C_Disc_D9.0mm_W5.0mm_P5.00mm",
    "X2_13x5_P10": "Capacitor_THT:C_Rect_L13.0mm_W5.0mm_P10.00mm_FKS3_FKP3_MKS4",
    "Y1_P10": "Capacitor_THT:C_Disc_D8.0mm_W5.0mm_P10.00mm",
    "CP10x13": "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
    "SOP4LC": "Package_SO:SO-4_7.6x3.6mm_P2.54mm",
    "SOIC4": "Diode_SMD:Diode_Bridge_Vishay_MBLS",
    "TP": "TestPoint:TestPoint_Pad_1.5x1.5mm",
    "PAD4": "driver:Pads_1x04_P2.54mm",
    "HDR3": "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
}

# --------------------------------------------------------------------- vung dat tu dong (shelf packing)
# name: (x0, y0, x1, y1, layer, gap, mode)  mode "row": xep theo hang trai->phai; "col": xep theo cot tren->duoi
# name: (x0, y0, x1, y1, layer, gap_x, mode, gap_y)  - gap_y lon de chua kenh via giua cac hang
REGIONS = {
    "PRI_B_A":      (11.0, 5.0, 34.0, 9.9, "B", 0.95, "row", 1.6),   # D3 R8 D14
    "PRI_B_D":      (10.9, 13.3, 34.1, 18.1, "B", 0.95, "row", 1.6), # D11 D13 D12
    "PRI_B_E":      (10.5, 21.0, 36.2, 29.4, "B", 0.95, "row", 1.6), # U1 R2 R35 C3 R4 / C8 C6 C7 R6 R5 R3
    "PRI_B_CLAMP1": (39.0, 0.6, 44.3, 7.9, "B", 0.95, "col", 0.95),  # D1 (rot 90)
    "PRI_B_CLAMP2": (39.0, 14.6, 44.3, 25.2, "B", 0.95, "col", 0.95),# TVS1 (rot 90)
    "SEC_S1":       (46.0, 0.6, 51.0, 8.0, "B", 0.95, "row", 1.4),   # D4 / R19 / C14
    "SEC_S2":       (46.0, 14.6, 51.0, 24.0, "B", 0.95, "row", 1.6), # R20 R21 / C13 C21
    "SEC_S3":       (54.2, 0.6, 65.7, 9.5, "B", 1.2, "row", 2.0),    # C5 R22 R23 / C15 R17 R28 / C17 R29 R30
    "SEC_S4":       (54.2, 15.0, 77.0, 29.4, "B", 1.2, "row", 2.0),  # U3 U4 U8 / 0402 x 15
    "SEC_S5A":      (66.0, 0.5, 77.6, 6.7, "B", 1.2, "row", 1.6),    # C16 C19 C23
    "SEC_S5B":      (79.8, 0.5, 94.5, 6.7, "B", 1.2, "row", 1.6),    # C18 C26 C20 / C22
    "SEC_S6":       (66.0, 8.3, 77.0, 13.0, "B", 1.2, "row", 1.6),   # R33 R34 C24 RT2
    "SEC_S7":       (78.5, 7.4, 89.0, 19.9, "B", 1.6, "col", 1.2),   # (rot 90) Q2 Q3 | U5 U6 R26 | R25 R27 C25
    "SEC_S8":       (81.4, 21.3, 94.5, 24.4, "B", 1.2, "row", 1.6),  # R7 R36
    "SEC_T1":       (65.5, 7.5, 78.0, 18.0, "F", 1.2, "row", 1.6),   # mat tren: D6 D7
}

# --------------------------------------------------------------------- components
# (ref, value, fp_key, {pad: net}, pos=(x, y, rot) | region="NAME", layer)
C = []
def add(ref, value, fp, pins, pos=None, layer="F", block=0, region=None, rot=0):
    C.append(dict(ref=ref, value=value, fp=FP[fp], pins=pins, pos=pos, layer=layer, block=block, region=region, rot=rot))

# ---- khoi 1: dau vao (mat tren: THT)
add("J1", "AC_IN pads", "TB2_508", {"1": "L_IN", "2": "N_IN"}, (5.6, 2.85, 0), block=1)
add("F1", "T2A/250V 2410", "FUSE2410", {"1": "L_IN", "2": "L_F"}, (15.55, 2.5, 0), block=1)
add("RV1", "MOV 10D471", "DISC10_P75", {"1": "L_F", "2": "N_IN"}, (21.8, 3.3, 0), block=1)
add("RT1", "NTC 5D-9", "DISC9_P75", {"1": "L_CM", "2": "L_BR"}, (3.0, 24.5, 0), block=1)
add("L1", "CM 2x10mH UU9.8", "UU98", {"1": "L_F", "2": "L_CM", "3": "N_IN", "4": "N_CM"}, (6.3, 13.1, 270), block=1)
add("CX1", "100nF X2", "X2_13x5_P10", {"1": "L_CM", "2": "N_CM"}, (14.1, 19.8, 0), block=1)
add("C1", "22uF/400V", "CP10x13", {"1": "HV", "2": "GND_P"}, (14.9, 11.6, 0), block=1)
add("C27", "22uF/400V", "CP10x13", {"1": "HV", "2": "GND_P"}, (25.6, 11.6, 0), block=1)
# cau chinh luu 4 diode M7 (mat duoi): D11/D12 nhanh +, D13/D14 nhanh -
add("D11", "M7", "SMA", {"1": "HV", "2": "L_BR"}, layer="B", block=1, region="PRI_B_D")
add("D13", "M7", "SMA", {"1": "L_BR", "2": "GND_P"}, layer="B", block=1, region="PRI_B_D")
add("D12", "M7", "SMA", {"1": "HV", "2": "N_CM"}, layer="B", block=1, region="PRI_B_D")
add("D14", "M7", "SMA", {"1": "N_CM", "2": "GND_P"}, layer="B", block=1, region="PRI_B_A")

# ---- khoi 2: flyback
add("T1", "PQ20/20 42:24:14", "PQ2020",
    {"1": "HV", "2": "NC", "3": "DRAIN", "4": "AUX", "5": "GND_P",
     "6": "SEC", "7": "SEC", "8": "NC", "9": "GND_S", "10": "GND_S"}, (45.0, 12.2, 0), block=2)
add("Q1", "MOSFET 650V DPAK", "DPAK", {"1": "GATE", "2": "DRAIN", "3": "CS_SRC"}, (28.5, 26.2, 0), block=2)
add("D1", "ES1J", "SMA", {"1": "CLAMP", "2": "DRAIN"}, layer="B", block=2, region="PRI_B_CLAMP1", rot=90)
add("TVS1", "SMBJ150A / P6SMB150A", "SMB", {"1": "HV", "2": "CLAMP"}, layer="B", block=2, region="PRI_B_CLAMP2", rot=90)
add("R2", "0R82 1206", "1206", {"1": "CS_SRC", "2": "GND_P"}, layer="B", block=2, region="PRI_B_E", rot=90)
add("R35", "0R82 1206", "1206", {"1": "CS_SRC", "2": "GND_P"}, layer="B", block=2, region="PRI_B_E", rot=90)
add("R4", "1k", "0402", {"1": "CS_SRC", "2": "CS"}, layer="B", block=2, region="PRI_B_E")
add("R3", "10R", "0402", {"1": "DRV", "2": "GATE"}, layer="B", block=2, region="PRI_B_E")
add("D3", "US1J", "SMA", {"1": "VDD", "2": "AUX"}, layer="B", block=2, region="PRI_B_A")
add("C3", "10uF/50V X7R", "C1206", {"1": "VDD", "2": "GND_P"}, layer="B", block=2, region="PRI_B_E")
add("D2", "ES3J", "SMC", {"1": "VPLUS", "2": "SEC"}, (60.7, 4.0, 180), block=2)
add("C4", "100uF/63V", "CP8x12", {"1": "VPLUS", "2": "GND_S"}, (58.5, 12.5, 0), block=2)
add("C5", "100nF/100V", "C0805", {"1": "VPLUS", "2": "GND_S"}, layer="B", block=2, region="SEC_S3")

# ---- khoi 3: dieu khien (mat duoi)
add("U1", "UCC28740", "SOIC8", {"1": "VDD", "2": "VS", "3": "FB", "4": "GND_P", "5": "CS", "6": "DRV", "7": "HV_START", "8": "NC"},
    layer="B", block=3, region="PRI_B_E")
add("C8", "100nF", "C0402", {"1": "VDD", "2": "GND_P"}, layer="B", block=3, region="PRI_B_E")
add("C6", "1nF", "C0402", {"1": "FB", "2": "GND_P"}, layer="B", block=3, region="PRI_B_E")
add("C7", "220pF", "C0402", {"1": "CS", "2": "GND_P"}, layer="B", block=3, region="PRI_B_E")
add("R6", "20k", "0402", {"1": "VS", "2": "GND_P"}, layer="B", block=3, region="PRI_B_E")
add("R5", "150k", "0402", {"1": "AUX", "2": "VS"}, layer="B", block=3, region="PRI_B_E")
add("R8", "1k 1206", "1206", {"1": "HV", "2": "HV_START"}, layer="B", block=3, region="PRI_B_A")
add("U2", "PC817 SO4-wide", "SOP4LC", {"1": "OPTO_A", "2": "OPTO_K", "3": "GND_P", "4": "FB"}, (45.0, 11.0, 180), layer="B", block=3)
add("CY1", "2.2nF Y1", "Y1_P10", {"1": "GND_P", "2": "GND_S"}, (40.0, 26.8, 0), block=3)

# ---- khoi 4: vong CC/CV (mat duoi)
add("U3", "TLV9002", "SOIC8",
    {"1": "ISENSE_AMP", "2": "FB_A", "3": "SENSE_F", "4": "GND_S", "5": "VREF", "6": "ERR_IN", "7": "ERR_OUT", "8": "+5V"},
    layer="B", block=4, region="SEC_S4")
add("C9", "100nF", "C0402", {"1": "+5V", "2": "GND_S"}, layer="B", block=4, region="SEC_S4")
add("R9", "1k", "0402", {"1": "SENSE_P", "2": "SENSE_F"}, layer="B", block=4, region="SEC_S4")
add("R10", "10k", "0402", {"1": "FB_A", "2": "GND_S"}, layer="B", block=4, region="SEC_S4")
add("R11", "40.2k", "0402", {"1": "FB_A", "2": "ISENSE_AMP"}, layer="B", block=4, region="SEC_S4")
add("R15", "10k", "0402", {"1": "ISENSE_AMP", "2": "ERR_IN"}, layer="B", block=4, region="SEC_S4")
add("R16", "10k", "0402", {"1": "ERR_IN", "2": "COMP_MID"}, layer="B", block=4, region="SEC_S4")
add("C12", "100nF", "C0402", {"1": "COMP_MID", "2": "ERR_OUT"}, layer="B", block=4, region="SEC_S4")
add("D4", "1N4148W", "SOD123", {"1": "ERR_OUT", "2": "OPTO_K"}, layer="B", block=4, region="SEC_S1")
add("R12", "33k", "0402", {"1": "PWM_DIM", "2": "VREF_1"}, layer="B", block=4, region="SEC_S4")
add("R13", "9.76k", "0402", {"1": "VREF_1", "2": "GND_S"}, layer="B", block=4, region="SEC_S4")
add("C10", "470nF", "C0402", {"1": "VREF_1", "2": "GND_S"}, layer="B", block=4, region="SEC_S4")
add("R14", "4.7k", "0402", {"1": "VREF_1", "2": "VREF"}, layer="B", block=4, region="SEC_S4")
add("C11", "470nF", "C0402", {"1": "VREF", "2": "GND_S"}, layer="B", block=4, region="SEC_S4")
add("R17", "1k", "0402", {"1": "+5V", "2": "OPTO_A"}, layer="B", block=4, region="SEC_S3")
add("U4", "TL431", "SOT23", {"1": "CV_REF", "2": "GND_S", "3": "OPTO_K"}, layer="B", block=4, region="SEC_S4")
add("R20", "169k 1%", "0402", {"1": "VPLUS", "2": "CV_REF"}, layer="B", block=4, region="SEC_S2")
add("R21", "10k", "0402", {"1": "CV_REF", "2": "GND_S"}, layer="B", block=4, region="SEC_S2")
add("C13", "10nF", "C0402", {"1": "CV_REF", "2": "OPTO_K"}, layer="B", block=4, region="SEC_S2")
add("R19", "10k", "0402", {"1": "ISENSE_AMP", "2": "ADC_ISENSE"}, layer="B", block=4, region="SEC_S1")
add("C14", "1nF", "C0402", {"1": "ADC_ISENSE", "2": "GND_S"}, layer="B", block=4, region="SEC_S1")
add("R22", "150k", "0402", {"1": "VPLUS", "2": "ADC_VOUT"}, layer="B", block=4, region="SEC_S3")
add("R23", "10k", "0402", {"1": "ADC_VOUT", "2": "GND_S"}, layer="B", block=4, region="SEC_S3")
add("C15", "100nF", "C0402", {"1": "ADC_VOUT", "2": "GND_S"}, layer="B", block=4, region="SEC_S3")

# ---- khoi 5: chuyen kenh (mat duoi, phia tren module)
add("Q2", "IRLML0060", "SOT23", {"1": "G_CW", "2": "SENSE_P", "3": "CW_N"}, layer="B", block=5, region="SEC_S7", rot=90)
add("Q3", "IRLML0060", "SOT23", {"1": "G_WW", "2": "SENSE_P", "3": "WW_N"}, layer="B", block=5, region="SEC_S7", rot=90)
add("R7", "0R30 1206", "1206", {"1": "SENSE_P", "2": "GND_S"}, layer="B", block=5, region="SEC_S8")
add("R36", "0R30 1206", "1206", {"1": "SENSE_P", "2": "GND_S"}, layer="B", block=5, region="SEC_S8")
add("U5", "74AHCT1G125", "SC70-5", {"1": "GND_S", "2": "PWM_CW", "3": "GND_S", "4": "G_CW_R", "5": "+5V"}, layer="B", block=5, region="SEC_S7", rot=90)
add("U6", "74AHCT1G125", "SC70-5", {"1": "GND_S", "2": "PWM_WW", "3": "GND_S", "4": "G_WW_R", "5": "+5V"}, layer="B", block=5, region="SEC_S7", rot=90)
add("R24", "47R", "0402", {"1": "G_CW_R", "2": "G_CW"}, layer="B", block=5, region="SEC_S4")
add("R26", "47R", "0402", {"1": "G_WW_R", "2": "G_WW"}, layer="B", block=5, region="SEC_S7", rot=90)
add("R25", "100k", "0402", {"1": "G_CW", "2": "GND_S"}, layer="B", block=5, region="SEC_S7", rot=90)
add("R27", "100k", "0402", {"1": "G_WW", "2": "GND_S"}, layer="B", block=5, region="SEC_S7", rot=90)
add("C25", "100nF", "C0402", {"1": "+5V", "2": "GND_S"}, layer="B", block=5, region="SEC_S7", rot=90)
add("C22", "10uF", "C0805", {"1": "+3V3", "2": "GND_S"}, layer="B", block=7, region="SEC_S5B")
add("C23", "100nF", "C0402", {"1": "+3V3", "2": "GND_S"}, layer="B", block=7, region="SEC_S5A")
add("J2", "OUT V+ CW- WW- pads", "TB3_350", {"1": "VPLUS", "2": "CW_N", "3": "WW_N"}, (88.0, 27.0, 0), block=5)

# ---- khoi 6: nguon phu
add("U7", "LMR16006Y", "SOT23-6", {"1": "GND_S", "2": "VPLUS", "3": "EN7", "4": "FB7", "5": "SW7", "6": "BOOT7"}, (81.5, 3.5, 0), block=6)
add("L2", "22uH", "IND5x5", {"1": "SW7", "2": "+5V"}, (74.4, 3.5, 0), block=6)
add("C16", "4.7uF/100V", "C1210", {"1": "VPLUS", "2": "GND_S"}, layer="B", block=6, region="SEC_S5A")
add("R28", "100k", "0402", {"1": "VPLUS", "2": "EN7"}, layer="B", block=6, region="SEC_S3")
add("C17", "100nF", "C0402", {"1": "BOOT7", "2": "SW7"}, layer="B", block=6, region="SEC_S3")
add("R29", "56k", "0402", {"1": "+5V", "2": "FB7"}, layer="B", block=6, region="SEC_S3")
add("R30", "10k", "0402", {"1": "FB7", "2": "GND_S"}, layer="B", block=6, region="SEC_S3")
add("D6", "SS16", "SMA", {"1": "SW7", "2": "GND_S"}, layer="F", block=6, region="SEC_T1")
add("C18", "22uF", "C0805", {"1": "+5V", "2": "GND_S"}, layer="B", block=6, region="SEC_S5B")
add("C26", "22uF", "C0805", {"1": "+5V", "2": "GND_S"}, layer="B", block=6, region="SEC_S5B")
add("U8", "ME6211C33", "SOT23-5", {"1": "+5V", "2": "GND_S", "3": "+5V", "4": "NC", "5": "+3V3"}, layer="B", block=6, region="SEC_S4")
add("C19", "1uF", "C0402", {"1": "+5V", "2": "GND_S"}, layer="B", block=6, region="SEC_S5A")
add("C20", "10uF", "C0805", {"1": "+3V3", "2": "GND_S"}, layer="B", block=6, region="SEC_S5B")
add("D7", "SS14", "SMA", {"1": "+5V", "2": "USB_5V"}, layer="F", block=7, region="SEC_T1")

# ---- khoi 7: MCU
# ESP32-C6-MINI-1 pin table (datasheet v1.5, Table 3-1): GND 1,2,11,14,36-53; 3V3 3; EN 8; IO2 5; IO3 6; IO4 9; IO5 10;
# IO0 12; IO1 13; IO6 15; IO7 16; IO12 17; IO13 18; IO14 19; IO15 20; IO8 22; IO9 23; IO18 24; IO19 25; IO20 26;
# IO21 27; IO22 28; IO23 29; RXD0(IO17) 30; TXD0(IO16) 31; NC 4,7,21,32-35.  IO10/IO11 KHONG co tren module -> LED dung IO7.
ESP_GND_PINS = [1, 2, 11, 14] + list(range(36, 54))
U9_PINS = {str(n): "GND_S" for n in ESP_GND_PINS}
U9_PINS.update({
    "3": "+3V3", "8": "EN",
    "12": "PWM_CW", "13": "PWM_WW", "5": "PWM_DIM",
    "6": "ADC_VOUT", "9": "NTC_N", "15": "ADC_ISENSE",
    "23": "BTN", "16": "LED_IO",
    "17": "USB_DM", "18": "USB_DP", "30": "RXD0", "31": "TXD0",
    "24": "DIP1", "25": "DIP2", "26": "DIP3",
})
add("U9", "ESP32-C6-MINI-1", "ESP32C6", U9_PINS, (83.9, 13.9, -90), block=7)    # anten huong mep phai
add("SW1", "DIP x3 power", "DIP3", {"1": "DIP1", "2": "DIP2", "3": "DIP3", "4": "GND_S", "5": "GND_S", "6": "GND_S"}, (71.3, 24.5, 0), block=7)
add("SW4", "BTN", "BTN", {"1": "BTN", "2": "GND_S"}, (89.5, 3.5, 0), block=7)   # SKQG: pad 1 x2, pad 2 x2
add("D10", "LED", "LED0805", {"1": "LED_K", "2": "+3V3"}, (53.2, 26.0, 90), block=7)
add("R33", "1k", "0402", {"1": "LED_K", "2": "LED_IO"}, layer="B", block=7, region="SEC_S6")
add("R34", "10k", "0402", {"1": "+3V3", "2": "BTN"}, layer="B", block=7, region="SEC_S6")
add("C24", "100nF", "C0402", {"1": "BTN", "2": "GND_S"}, layer="B", block=7, region="SEC_S6")
add("RT2", "NTC 10k", "0402", {"1": "NTC_N", "2": "GND_S"}, layer="B", block=7, region="SEC_S6")
add("R31", "10k", "0402", {"1": "+3V3", "2": "NTC_N"}, layer="B", block=7, region="SEC_S4")
add("R32", "10k", "0402", {"1": "+3V3", "2": "EN"}, layer="B", block=7, region="SEC_S4")
add("C21", "1uF", "C0402", {"1": "EN", "2": "GND_S"}, layer="B", block=7, region="SEC_S2")
add("J3", "USB pads 5V D- D+ GND", "PAD4", {"1": "USB_5V", "2": "USB_DM", "3": "USB_DP", "4": "GND_S"}, (57.5, 24.0, 90), block=7)
add("J4", "UART TX RX GND", "HDR3", {"1": "TXD0", "2": "RXD0", "3": "GND_S"}, (79.6, 22.9, 0), block=7)

# --------------------------------------------------------------------- vung / rang buoc
BARRIER_X = 45.0                                # hang rao cach ly thang dung
ISO_SLOTS = [(44.5, 23.8, 45.5, 29.0)]          # ranh phay giua hai chan CY1
ANTENNA_KEEPOUT = (89.3, 6.8, 95.0, 21.0)
MODULE_TRACK_KEEPOUT_F = (79.7, 8.7, 88.1, 19.1)   # khong di track/via lop tren duoi loi module (giua cac hang pad)       # phan anten cua module: khong dong, khong linh kien


def nets():
    s = {}
    for c in C:
        for pad, n in c["pins"].items():
            if n == "NC":
                continue
            s.setdefault(n, []).append((c["ref"], pad))
    return s


if __name__ == "__main__":
    ns = nets()
    print(len(C), "linh kien,", len(ns), "net")
    for n, pins in sorted(ns.items()):
        print(f"{n:12s} {len(pins):2d}  {' '.join(r + '.' + p for r, p in pins)}")


# thu tu dat trong vung (shelf packing theo danh sach nay)
REGION_ORDER = {'PRI_B_A': ['D3', 'R8', 'D14'], 'PRI_B_D': ['D11', 'D13', 'D12'], 'PRI_B_E': ['U1', 'R2', 'R35', 'C3', 'R4', 'C8', 'C6', 'C7', 'R6', 'R5', 'R3'], 'PRI_B_CLAMP1': ['D1'], 'PRI_B_CLAMP2': ['TVS1'], 'SEC_S1': ['D4', 'R19', 'C14'], 'SEC_S2': ['R20', 'R21', 'C13', 'C21'], 'SEC_S3': ['C5', 'R22', 'R23', 'C15', 'R17', 'R28', 'C17', 'R29', 'R30'], 'SEC_S4': ['U3', 'U4', 'U8', 'R9', 'R10', 'R11', 'R15', 'R16', 'C12', 'R12', 'R13', 'C10', 'R14', 'C11', 'C9', 'R24', 'R31', 'R32'], 'SEC_S5A': ['C16', 'C19', 'C23'], 'SEC_S5B': ['C18', 'C26', 'C20', 'C22'], 'SEC_S6': ['R33', 'R34', 'C24', 'RT2'], 'SEC_S7': ['Q2', 'Q3', 'U5', 'U6', 'R26', 'R25', 'R27', 'C25'], 'SEC_S8': ['R7', 'R36'], 'SEC_T1': ['D6', 'D7']}
def region_items(name):
    byref = {c["ref"]: c for c in C}
    lst = [byref[r] for r in REGION_ORDER.get(name, []) if r in byref and byref[r]["region"] == name]
    lst += [c for c in C if c["region"] == name and c not in lst]
    return lst

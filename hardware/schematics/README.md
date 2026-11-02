# Sơ đồ nguyên lý – 7 khối

Mỗi khối là một tệp SVG sinh bởi script `gen_0X_*.py` (Python + [schemdraw](https://schemdraw.readthedocs.io)).
Chạy `python3 gen_0X_*.py` từ thư mục gốc kho để sinh lại.

| # | Tệp | Nội dung | Phía |
|---|---|---|---|
| 1 | `01_input_filter.svg` | J1, F1, RV1, RT1, L1, CX1, BR1, C1 | sơ cấp |
| 2 | `02_flyback_stage.svg` | T1, Q1, R2, clamp D1/R1/C2, cuộn phụ D3/C3, D2, C4, C5 | sơ cấp + thứ cấp |
| 3 | `03_controller.svg` | U1 UCC28740, R5/R6, R8, C6–C8, U2 opto (phía transistor), CY1 | sơ cấp |
| 4 | `04_cc_cv_loop.svg` | U3A/U3B, R9–R19, C10–C14, D4, R17, U4 TL431, R20–R23, C15 | thứ cấp |
| 5 | `05_output_switch.svg` | U5/U6 74AHCT1G125, Q2/Q3, R24–R27, R7 shunt, J2 | thứ cấp |
| 6 | `06_aux_supply.svg` | U7 LMR16006 buck 5 V, U8 LDO 3.3 V, L2, D6, C16–C20, R28–R30 | thứ cấp |
| 7 | `07_mcu.svg` | U9 ESP32‑C6‑MINI‑1, SW1‑3 DIP, SW4, D10, RT2, R31–R34, C21–C24, J3/J4 | thứ cấp |

## Net liên khối

| Net | Nguồn (khối) | Đích (khối) | Mô tả |
|---|---|---|---|
| +HV | 1 | 2, 3 | DC bus 215–373 V |
| GND_P | 1 | 2, 3 | đất sơ cấp (cực âm C1) |
| AUX | 2 | 3 | đầu cuộn phụ (trước D3) → chia áp VS |
| VDD | 2 | 3 | nguồn U1 12–26 V |
| DRV | 3 | 2 | lái cổng Q1 qua R3 |
| CS | 2 | 3 | sense dòng sơ cấp (R2 qua R4) |
| OPTO_A / OPTO_K | 4 | 3 | LED opto (thứ cấp) – bắc qua hàng rào trong U2 |
| V+ | 2 | 4, 5, 6 | đầu ra 20–45 V |
| GND_S | 2 | 4, 5, 6, 7 | đất thứ cấp (SELV) |
| SENSE+ | 5 | 4 | điện áp trên shunt R7 (0–142 mV) |
| ISENSE_AMP | 4 | 4, 7 | dòng LED khuếch đại ×5 (0.753 V = 1 A) → ADC_ISENSE |
| VREF | 4 | 4 | tham chiếu dòng đã lọc |
| PWM_DIM | 7 | 4 | GPIO2 |
| PWM_CW / PWM_WW | 7 | 5 | GPIO0 / GPIO1 |
| ADC_VOUT / ADC_ISENSE / ADC_NTC | 4 / 4 / 7 | 7 | GPIO3 / GPIO6 / GPIO4 |
| +5 V | 6 | 4, 5, 6 | opto, U3, U5/U6, LDO |
| +3V3 | 6 | 7 | ESP32‑C6, pull‑up |
| CW– / WW– / V+ | 5 | J2 | đầu ra 3 dây tới đèn |

Quy ước: ký hiệu đất ở khối 1–3 là **GND_P**, ở khối 4–7 là **GND_S**; hai đất chỉ nối với nhau qua tụ CY1 (Y1).

# 07 – Kế hoạch kiểm thử, an toàn và EMC

## 1. Trình tự bring‑up (an toàn)

1. **Thứ cấp độc lập**: chưa lắp T1/Q1/U1. Cấp 24–45 V DC vào V+/GND_S từ nguồn phòng thí nghiệm (giới hạn 0.3 A). Kiểm tra 5 V, 3.3 V, ESP32 boot, log UART, PWM_DIM → Vref, DIP, nút, LED.
2. **Vòng CC/CV trên bàn**: dùng nguồn CC/CV ngoài làm giả flyback: nối đèn, kiểm tra ISENSE_AMP = 5 × Vsense, TL431 kẹp 45 V, OPTO_K kéo xuống khi I > Iref.
3. **Sơ cấp qua biến áp cách ly + variac**, đầu ra tải điện tử CC/CV hoặc đèn 36 V. Tăng dần từ 100 VAC; quan sát Vds Q1 (đầu đo ≥ 1 kV), Vclamp, nhiệt độ. Kiểm tra giới hạn CC sơ cấp bằng cách ngắt opto.
4. **Toàn bộ**: 220 VAC, đèn thật, đo dòng từng mức DIP, điều sáng 1–100 %, CCT, đo nhấp nháy (flicker meter: Pst‑LM ≤ 1, SVM ≤ 0.4), nhiệt độ sau 2 h trong vỏ.

## 2. Bảng kiểm tra điện

| Phép đo | Điều kiện | Giới hạn |
|---|---|---|
| Dòng ra từng mức DIP | 220 VAC, đèn 36 V, 100 % | ±5 % bảng DIP |
| Ổn định dòng theo Vac | 176–264 VAC | ±2 % |
| Ổn định dòng theo Vf | 20–42 V | ±3 % |
| Dim thấp nhất | level 1 | 10 mA ± 5 mA, không nhấp nháy, không tắt |
| Ripple dòng LED | 100 % | ≤ 10 % p‑p (100 Hz), ≤ 20 % (75 kHz) |
| V+ khi không tải / đèn tắt | | 45 ± 1.5 V |
| Điện áp ra khi bật từ tắt | | không xung dòng > 1.5 × I_set (soft‑connect) |
| Hiệu suất | 40 W | ≥ 86 % |
| Công suất chờ | đèn tắt, Thread kết nối | ≤ 0.8 W |
| Hệ số công suất | 40 W | ≥ 0.5 (không PFC); nếu cần PF > 0.9 thêm tầng PFC (> 25 W bắt buộc theo IEC 61000‑3‑2 lớp C – xem ghi chú) |
| Khởi động | 220 VAC, 25 °C | sáng ≤ 1.5 s |
| Ngắn mạch đầu ra | liên tục 1 h | không hỏng, tự phục hồi |
| Hở tải | | V+ 45 V, không hỏng |
| Nhiệt độ | 40 W, 50 °C môi trường, trong vỏ | Q1 ≤ 100 °C, D2 ≤ 110 °C, C1/C4 ≤ 95 °C, T1 ≤ 100 °C, tc ≤ 85 °C |

> IEC 61000‑3‑2 lớp C: thiết bị chiếu sáng > 25 W cần giới hạn hài (PF ≈ > 0.9). Bản 40 W muốn bán thương mại ở EU/VN theo QCVN cần thêm PFC (ví dụ boost PFC đơn tầng hoặc flyback PFC "single‑stage" dùng controller như **L6562/UCC28810/BP3122** thay cho UCC28740 – kích thước PCB tăng ~10 mm). Bản ≤ 25 W không bắt buộc.

## 3. An toàn (IEC 61347‑1 / 61347‑2‑13, IEC 62368‑1)

* Hipot: 3.75 kVAC 1 phút sơ cấp ↔ thứ cấp (dòng rò < 5 mA); 1.5 kVAC sơ cấp ↔ vỏ kim loại nếu có.
* Điện trở cách điện ≥ 10 MΩ @500 VDC.
* Dòng rò chạm (touch current) ≤ 0.25 mA (tụ Y1 2.2 nF → ≈ 0.17 mA @ 240 V 50 Hz – không tăng CY1 quá 3.3 nF).
* Creepage/clearance theo bảng ở `05‑pcb-layout.md`; kiểm tra bằng DRC KiCad với lớp rule riêng cho net class HV.
* Thử lỗi linh kiện (single fault): ngắn D1, hở R2, ngắn Q1 → cầu chì F1 ngắt, không cháy.
* Nhiệt bất thường: chặn quạt/đặt trong hộp 60 °C → không vượt 125 °C trên vật liệu nhựa.
* Nhãn: tc, ta, SELV, điện áp/dòng ra, cảnh báo cách ly.

## 4. EMC

| Tiêu chuẩn | Yêu cầu | Biện pháp |
|---|---|---|
| EN 55015 / CISPR 15 (dẫn 150 kHz–30 MHz, bức xạ 30 MHz–300 MHz) | lớp B dân dụng | CM choke 2 × 10 mH, X2 100 nF, Y1 2.2 nF, RC snubber D2 (10 Ω + 1 nF nếu cần), vòng dòng nhỏ, bù tần số QR giúp trải phổ |
| EN 61547 / IEC 61000‑4‑x | ESD 8 kV khí/4 kV tiếp xúc, surge 1 kV L‑N (2 kV nếu ngoài trời), EFT 1 kV | MOV 10D471, cầu chì, 100 nF trên nút nhấn/DIP, TVS trên dây dài nếu đèn cách > 1 m |
| ETSI EN 300 328 | 2.4 GHz | module ESP32‑C6 đã chứng nhận RF; không thay anten |
| IEEE 1789 (nhấp nháy) | Mod % < 0.08 × f (f = 100 Hz → < 8 %) | ripple dòng LED ≤ 10 %; PWM kênh 4 kHz > 3 kHz "no‑effect" |

## 5. Kiểm thử Matter/Thread

1. Commissioning với 3 hệ sinh thái (Apple Home, Google Home, Home Assistant) – thời gian ≤ 60 s.
2. Lệnh On/Off, MoveToLevel (transition 0/1/10 s), MoveToColorTemperature, Scenes, Groups multicast.
3. Mất điện 10 lần: trạng thái khôi phục đúng; vào lại mạng Thread ≤ 10 s.
4. Mất border router 1 h → tự nối lại.
5. Chứng nhận Matter: chạy `chip-tool` + Test Harness (TC‑OO, TC‑LVL, TC‑CC) – cần VID/PID CSA và DAC thật.
6. OTA: cập nhật qua controller, rollback khi ảnh hỏng.

## 6. Dụng cụ cần có

Variac + biến áp cách ly, tải điện tử 60 V/2 A (CC/CV), đồng hồ công suất (PF, hài), dao động ký 4 kênh + đầu đo cao áp vi sai, flicker meter hoặc photodiode + scope, buồng nhiệt, máy hipot, thiết bị LISN cho đo dẫn (tùy chọn), Thread border router + chip‑tool.

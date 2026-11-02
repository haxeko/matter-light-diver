# 06 – Firmware: ESP‑IDF + esp‑matter, Matter over Thread

Thư mục `firmware/` là dự án ESP‑IDF theo bố cục của `esp-matter/examples/light`.

| Tệp | Vai trò |
|---|---|
| `main/app_main.cpp` | Tạo node Matter, endpoint *Color Temperature Light* (0x010C), cấu hình OpenThread, callback thuộc tính/identify/sự kiện |
| `main/app_driver.cpp/.h` | LEDC, ADC, GPIO, nút nhấn, LED trạng thái, tick 10 ms, bảo vệ |
| `main/light_engine.c/.h` | Toán học thuần C: level → dòng, mired → tỉ lệ CW/WW, chồng lấn, fader (kiểm thử trên máy tính) |
| `main/board_config.h` | Bản đồ GPIO, tần số PWM, bảng DIP, hằng số bảo vệ |
| `test_host/test_light_engine.c` | Unit test chạy bằng gcc |
| `sdkconfig.defaults*`, `partitions.csv` | Cấu hình Thread/BLE, phân vùng OTA 4 MB |

## 1. Môi trường build

```bash
# ESP-IDF v5.2.x + esp-matter v1.3/v1.4 (https://docs.espressif.com/projects/esp-matter)
. $IDF_PATH/export.sh
. $ESP_MATTER_PATH/export.sh
cd firmware
idf.py set-target esp32c6
idf.py build
idf.py -p /dev/ttyACM0 flash monitor        # qua USB-Serial-JTAG (pad J3) – board KHÔNG cắm điện lưới
```

Kiểm thử logic điều sáng không cần phần cứng:

```bash
cd firmware/test_host
cc -std=c11 -Wall -I../main test_light_engine.c ../main/light_engine.c -lm -o test && ./test
```

> Lưu ý: mã nguồn viết theo API esp‑matter v1.3/v1.4 và ESP‑IDF 5.2; dự án này chưa được biên dịch trong môi trường có ESP‑IDF (môi trường tạo tài liệu không có toolchain). Khi build lần đầu, đối chiếu tên trường `color_temperature_light::config_t` với bản esp‑matter đang dùng (xem `examples/light/main/app_main.cpp` của bản đó).

## 2. Mô hình dữ liệu Matter

* Device type **Color Temperature Light 0x010C**: Identify, Groups, Scenes, On/Off (feature Lighting), Level Control (feature OnOff + Lighting), Color Control (feature **CT**, `ColorTempPhysicalMinMireds` 153, `ColorTempPhysicalMaxMireds` 370), Descriptor. esp‑matter tạo đủ các cluster bắt buộc khác (Basic Information, General Diagnostics, Thread Network Diagnostics, OTA Requestor…).
* `StartUpOnOff`, `StartUpCurrentLevel`, `StartUpColorTemperatureMireds` để `null` → khôi phục trạng thái trước khi mất điện (lưu NVS bởi stack).
* Mọi ghi thuộc tính đi qua `app_attribute_update_cb(PRE_UPDATE)` → `app_driver_attribute_update()` → `set_targets()`; transition time của lệnh `MoveToLevel`/`MoveToColorTemperature` do cluster server xử lý (cập nhật thuộc tính nhiều bước), driver làm mượt thêm 250 ms.
* Nút nhấn tại chỗ cập nhật `OnOff` qua `attribute::update()` nên controller luôn đồng bộ.

## 3. Thuật toán điều sáng và CCT (`light_engine.c`)

1. **Độ sáng** `f = (level/254)²` (luật bình phương ~ cảm nhận mắt), sàn `I_MIN = 10 mA`.
2. **Dòng mục tiêu** `I = I_max(DIP) × f × derate`, kẹp ≤ 1000 mA.
3. **PWM_DIM duty** `= I / 1000 mA × 4096` (vì Vref 100 % = 0.753 V ↔ 1.0 A).
4. **Tỉ lệ ấm** `w = (mired − 153)/(370 − 153)`; `cw = (1 − w)·s·8192`, `ww = w·s·8192`, `ww_hpoint = cw`, `cw += overlap` (2 µs = 66 count) khi cả hai kênh hoạt động. `s` là hệ số soft‑connect 0 → 1 trong 40 ms sau khi bật.
5. **Fader** nội suy tuyến tính level/mired mỗi 10 ms (mặc định 250 ms).
6. **Identify**: nhấp nháy 10 % / 100 % ở 2 Hz trong thời gian identify.

Kiểm thử trên máy (`test_light_engine.c`): đơn điệu theo level, sàn 10 mA, kẹp 1 A, chồng lấn, soft‑connect, bảng DIP, fader – tất cả qua.

## 4. Chu trình 10 ms trong `app_driver.cpp`

```
tick ─┬─ fader_tick()
      ├─ mỗi 100 ms: dip_poll() (đổi I_max sau 500 ms ổn định), measure() (ADC V+, I, NTC), protections_tick()
      ├─ led_tick() (mẫu nháy theo trạng thái)
      ├─ soft-connect: connect_pct += 25 %/tick khi vừa bật
      └─ le_compute() → ledc_apply()
```

Bảo vệ:

| Điều kiện | Hành động | LED |
|---|---|---|
| T > 85 °C | giảm dòng tuyến tính tới 20 % ở 100 °C | – |
| T ≥ 100 °C | tắt, thử lại sau 5 s khi T < 85 °C | 3 nháy |
| ON, V+ > 44 V và I < 20 % mục tiêu sau 500 ms | hở tải (không có đèn) → tắt kênh, thử lại 5 s | 2 nháy |
| ON, V+ < 8 V | ngắn mạch → tắt kênh, thử lại 5 s | 5 nháy |

## 5. Commissioning (Thread)

1. Cấp nguồn → LED nháy 1 Hz, thiết bị quảng bá BLE (discriminator/passcode trong dữ liệu factory; bản dev: 3840 / 20202021, QR `MT:Y.K9042C00KA0648G00`).
2. Dùng Apple Home / Google Home / SmartThings / Home Assistant (có Thread Border Router) quét mã QR → controller đẩy thông tin mạng Thread qua BLE → ESP32‑C6 vào mạng Thread (FTD, có thể làm router).
3. `kCommissioningComplete` → LED sáng 2 s rồi tắt. Thiết bị xuất hiện là đèn có điều chỉnh độ sáng + nhiệt độ màu.
4. Factory reset: giữ nút 5 s hoặc lệnh `RemoveFabric` từ controller; khi không còn fabric, firmware tự mở lại cửa sổ pairing.

Sản xuất: tạo DAC/PAI + QR riêng bằng `esp-matter-mfg-tool`, nạp vào phân vùng `fctry`, bật `CONFIG_ENABLE_ESP32_FACTORY_DATA_PROVIDER=y`; đăng ký VID/PID với CSA để qua chứng nhận.

## 6. OTA

Hai phân vùng `ota_0/ota_1` 1.9 MB; OTA Requestor Matter bật (`CONFIG_ENABLE_OTA_REQUESTOR=y`). Ảnh OTA tạo bằng `esp-matter` `ota_image_tool.py`.

## 7. Tuỳ biến nhanh

| Muốn | Sửa |
|---|---|
| Bảng công suất DIP khác | `DIP_CURRENT_TABLE_MA` trong `board_config.h` |
| Dải CCT đèn khác (vd 3000–5700 K) | `CCT_MIN_MIREDS` / `CCT_MAX_MIREDS` |
| Đường cong dim | `le_level_to_fraction()` |
| Tần số chuyển kênh | `CH_PWM_FREQ_HZ` (≤ 9.7 kHz với 13 bit) |
| Thời gian soft‑connect / fade | `SOFT_CONNECT_MS`, `FADE_DEFAULT_MS` |
| Thêm cluster (vd. Occupancy, Power Source) | `app_main.cpp` sau khi tạo endpoint |

# Dự án KiCad – driver đèn CCT 3 dây (ESP32‑C6, Matter over Thread)

Thư mục này là dự án **KiCad 7** (mở được bằng KiCad 7/8/9) được **sinh hoàn toàn bằng script** từ một cơ sở dữ liệu thiết kế duy nhất (`design_db.py`), vì vậy schematic, PCB, BOM luôn nhất quán.

| Tệp | Nội dung |
|---|---|
| `matter_cct_driver.kicad_pro` | Project (net class: AC 0.8 mm/1.0 mm; HV 0.8/0.6; PWR_S 1.0/0.3; PWR_L 0.5/0.2; SIG 0.25/0.2) |
| `matter_cct_driver.kicad_pcb` | PCB 30 × 95 mm, 2 lớp, 99 footprint, 64 net, đã đặt linh kiện + đi dây tự động (xem trạng thái bên dưới) |
| `matter_cct_driver.kicad_sch` | Schematic kiểu "kết nối" (mỗi chân gắn global label) – dùng để kiểm tra ERC/netlist và cập nhật PCB; sơ đồ nguyên lý dễ đọc ở `../schematics/*.svg` |
| `lib/driver.pretty`, `lib/driver.kicad_sym` | Footprint/symbol riêng: ESP32‑C6‑MINI‑1 (chuyển từ thư viện KiCad mới), biến áp PQ20/20, cuộn UU9.8, pad hàn dây, fuse 2410… |
| `design_db.py` | **Nguồn sự thật**: linh kiện, footprint, net, vị trí/vùng đặt, lớp net, keepout |
| `gen_kicad_pcb.py` | Sinh PCB bằng API `pcbnew`: nạp footprint, gán net, đặt (cố định + đóng gói tự động theo vùng), viền, rãnh phay, rule area, vùng đồng GND, đi dây, DRC |
| `router.py` | Router lưới 2 lớp tự viết (A*, 0.125 mm, neck‑down tại pad, via stub GND, thu hẹp bề rộng khi nghẽn) |
| `gen_kicad_sch.py` | Sinh schematic + thư viện symbol (netlist đã đối chiếu trùng với PCB) |
| `fix_gnd_stubs.py` | Sau khi đi dây: thử đặt via stub cho các pad GND còn hở, giữ lại khi DRC sạch và số kết nối thiếu giảm |
| `make_footprints.py`, `inspect_footprints.py` | Tạo footprint riêng, in kích thước courtyard |
| `output/` | Gerber + drill, PDF/SVG hai mặt, `schematic.pdf`, `netlist.xml`, `matter_cct_driver.dsn` (Specctra, cho Freerouting), `drc_report.txt` |

## Trạng thái thiết kế

* Bố trí: THT lớn (J1, L1, RV1, RT1, CX1, C1/C27, T1, C4, CY1, J2/J4, module ESP32‑C6) ở **mặt trên**; SMD nhỏ (0402, SOT, SMA, UCC28740, op‑amp…) ở **mặt dưới** – đúng kiểu driver thương mại.
* Cách ly: hàng rào thẳng x = 45 mm giữa biến áp, rule area cấm đồng ±0.6 mm; opto SO‑4 thân rộng (10.3 mm) ở mặt dưới ngay dưới biến áp; tụ Y1 pitch 10 mm + rãnh phay 1 mm; vùng đồng GND_P / GND_S tách biệt hai bên; keepout anten (không đồng dưới phần anten module, phần lõi module không đi track lớp trên).
* Đi dây: router tự động + via stub GND nối được **160/230 kết nối (≈ 70 %)** – 1 316 đoạn, 119 via; phần đã đi **không có vi phạm DRC** (clearance, keepout, lỗ–lỗ, cạnh board) – chỉ còn cảnh báo silk và 70 cặp chân chưa nối (`output/drc_report.txt`, mục *unconnected*). Chưa nối chủ yếu là GND_S ở vùng SMD dày (22 – cần via stitching/thu hẹp vùng đồng), nguồn thứ cấp (VPLUS, SENSE_P, CW_N/WW_N, +5V/+3V3) và vài tín hiệu quanh module – nên **hoàn thiện bằng tay trong KiCad** (ratsnest đã có) hoặc dùng Freerouting: *File → Export → Specctra DSN* (hoặc dùng `output/matter_cct_driver.dsn`), chạy `java -jar freerouting-x.jar -de board.dsn -do board.ses`, rồi *File → Import → Specctra Session*. (Môi trường tạo thiết kế này không được phép chạy Freerouting nên bước đó để lại cho người dùng.)
* Chưa làm: mô hình 3D, tối ưu nhiệt (đổ đồng tản nhiệt Q1/D2 đã có qua vùng GND nhưng cần thêm via nhiệt), kiểm tra creepage bằng rule tuỳ chỉnh của KiCad 8 (`(rule ... (condition "A.NetClass == 'HV'"))`).

## Sinh lại

```bash
sudo apt install kicad kicad-symbols kicad-footprints     # KiCad 7 (hoặc 8/9 – chỉnh API pcbnew nếu cần)
pip install kiutils numpy
cd hardware/kicad
python3 make_footprints.py            # lib/driver.pretty
python3 gen_kicad_pcb.py --route      # PCB + DRC (bỏ --route để chỉ đặt linh kiện)
python3 fix_gnd_stubs.py              # via stub cho pad GND còn hở (tuỳ chọn)
python3 gen_kicad_sch.py              # schematic
kicad-cli sch export netlist --format kicadxml -o output/netlist.xml matter_cct_driver.kicad_sch
kicad-cli pcb export gerbers -o output/gerber/ matter_cct_driver.kicad_pcb
```

Thay đổi thiết kế (giá trị, footprint, vị trí, vùng, net class) chỉ cần sửa `design_db.py` rồi chạy lại.

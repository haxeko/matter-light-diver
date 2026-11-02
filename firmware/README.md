# Firmware – ESP32-C6 Matter over Thread CCT driver

See `../docs/06-firmware.md` (Vietnamese) for the full description.

```bash
. $IDF_PATH/export.sh && . $ESP_MATTER_PATH/export.sh
idf.py set-target esp32c6
idf.py build
idf.py -p /dev/ttyACM0 flash monitor
```

Host unit test of the dimming / CCT maths:

```bash
cd test_host && cc -std=c11 -Wall -I../main test_light_engine.c ../main/light_engine.c -lm -o test && ./test
```

Pin map and tunables: `main/board_config.h`. Matter data model: `main/app_main.cpp`.
Written against esp-matter v1.3/v1.4 + ESP-IDF v5.2; not yet compiled in this repository's CI.

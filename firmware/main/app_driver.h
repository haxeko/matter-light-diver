/*
 * app_driver.h - hardware driver API for the 3-wire CCT LED driver (ESP32-C6).
 */
#pragma once
#include <esp_err.h>
#include <esp_matter.h>
#include <stdint.h>

typedef void *app_driver_handle_t;

/* default Matter state at first boot */
#define DEFAULT_POWER       true
#define DEFAULT_BRIGHTNESS  128      /* 1..254 */
#define DEFAULT_MIREDS      250      /* 4000 K */

/* Initialise LEDC, ADC, GPIO, button, timers. Call before esp_matter::start(). */
app_driver_handle_t app_driver_light_init(void);

/* Register the light endpoint id so local actions (button) can update Matter attributes. */
void app_driver_set_endpoint(uint16_t endpoint_id);

/* Called from app_attribute_update_cb (PRE_UPDATE) for every Matter attribute write. */
esp_err_t app_driver_attribute_update(app_driver_handle_t driver_handle, uint16_t endpoint_id,
                                      uint32_t cluster_id, uint32_t attribute_id, esp_matter_attr_val_t *val);

/* Push the attribute values stored in the data model to the hardware (after esp_matter::start). */
esp_err_t app_driver_light_set_defaults(uint16_t endpoint_id);

/* Identify effect (called from app_identification_cb) */
void app_driver_identify_start(void);
void app_driver_identify_stop(void);

/* Status LED patterns driven from Matter events */
typedef enum {
    LED_PATTERN_OFF = 0,
    LED_PATTERN_COMMISSIONING,     /* 1 Hz blink   */
    LED_PATTERN_CONNECTED,         /* on 2 s then off */
    LED_PATTERN_FACTORY_RESET,     /* fast blink   */
    LED_PATTERN_FAULT_OPEN,        /* 2 blinks     */
    LED_PATTERN_FAULT_OVERTEMP,    /* 3 blinks     */
    LED_PATTERN_FAULT_SHORT,       /* 5 blinks     */
} app_led_pattern_t;
void app_driver_set_led_pattern(app_led_pattern_t pattern);

/* Telemetry for logging / diagnostics */
typedef struct {
    float    vout_v;
    float    iout_ma;
    float    temp_c;
    uint16_t i_max_ma;      /* DIP selection */
    uint8_t  dip_code;
    uint8_t  fault;         /* 0 = none, see app_fault_t */
} app_driver_status_t;
void app_driver_get_status(app_driver_status_t *out);

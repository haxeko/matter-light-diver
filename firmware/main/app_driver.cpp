/*
 * app_driver.cpp - hardware driver for the 3-wire CCT LED driver (ESP32-C6).
 *
 *  - LEDC: current reference (PWM_DIM) + complementary CW/WW channel switches
 *  - ADC : V+, LED current, NTC temperature  (protection + diagnostics)
 *  - GPIO: 3 DIP switches (power selection), status LED
 *  - Button (iot_button): short press = toggle, long press (5 s) = factory reset
 *  - 10 ms engine tick (esp_timer): fading, soft-connect, protections, LED patterns
 *
 * All Matter <-> hardware glue lives here; the maths is in light_engine.c (host-testable).
 */
#include <math.h>
#include <string.h>

#include <esp_log.h>
#include <esp_timer.h>
#include <driver/gpio.h>
#include <driver/ledc.h>
#include <esp_adc/adc_oneshot.h>
#include <esp_adc/adc_cali.h>
#include <esp_adc/adc_cali_scheme.h>
#include <iot_button.h>

#include <esp_matter.h>

#include "app_driver.h"
#include "board_config.h"
#include "light_engine.h"

using namespace esp_matter;
using namespace chip::app::Clusters;

static const char *TAG = "app_driver";

/* ------------------------------------------------------------------ state */
typedef enum { FAULT_NONE = 0, FAULT_OPEN_LOAD, FAULT_SHORT, FAULT_OVERTEMP } app_fault_t;

static struct {
    /* Matter targets (written from the Matter task) */
    volatile bool     on;
    volatile uint8_t  level;
    volatile uint16_t mireds;
    /* engine */
    le_fader_t fader;
    uint8_t    connect_pct;         /* soft-connect ramp 0..100 */
    bool       was_on;
    uint16_t   derate_pct;
    uint16_t   i_max_ma;
    uint8_t    dip_code;
    uint8_t    dip_candidate;
    uint8_t    dip_stable_ticks;
    /* measurements */
    float vout_v, iout_ma, temp_c;
    /* faults */
    app_fault_t fault;
    uint32_t    fault_ticks;
    uint32_t    on_ticks;
    /* identify */
    volatile bool identify;
    /* led */
    app_led_pattern_t led_pattern;
    uint32_t          led_ticks;
    /* matter */
    uint16_t endpoint_id;
} s = {};

static adc_oneshot_unit_handle_t s_adc = nullptr;
static adc_cali_handle_t s_adc_cali = nullptr;
static esp_timer_handle_t s_tick_timer = nullptr;
static uint32_t s_tick = 0;

/* ------------------------------------------------------------------ LEDC */
static void ledc_init(void)
{
    ledc_timer_config_t t_dim = {};
    t_dim.speed_mode = LEDC_LOW_SPEED_MODE;
    t_dim.duty_resolution = (ledc_timer_bit_t)DIM_PWM_RES_BITS;
    t_dim.timer_num = LEDC_TIMER_0;
    t_dim.freq_hz = DIM_PWM_FREQ_HZ;
    t_dim.clk_cfg = LEDC_AUTO_CLK;
    ESP_ERROR_CHECK(ledc_timer_config(&t_dim));

    ledc_timer_config_t t_ch = {};
    t_ch.speed_mode = LEDC_LOW_SPEED_MODE;
    t_ch.duty_resolution = (ledc_timer_bit_t)CH_PWM_RES_BITS;
    t_ch.timer_num = LEDC_TIMER_1;
    t_ch.freq_hz = CH_PWM_FREQ_HZ;
    t_ch.clk_cfg = LEDC_AUTO_CLK;
    ESP_ERROR_CHECK(ledc_timer_config(&t_ch));

    const struct { int gpio; ledc_channel_t ch; ledc_timer_t timer; } chans[] = {
        { PIN_PWM_DIM, LEDC_CHANNEL_0, LEDC_TIMER_0 },
        { PIN_PWM_CW,  LEDC_CHANNEL_1, LEDC_TIMER_1 },
        { PIN_PWM_WW,  LEDC_CHANNEL_2, LEDC_TIMER_1 },
    };
    for (auto &c : chans) {
        ledc_channel_config_t cfg = {};
        cfg.gpio_num = c.gpio;
        cfg.speed_mode = LEDC_LOW_SPEED_MODE;
        cfg.channel = c.ch;
        cfg.intr_type = LEDC_INTR_DISABLE;
        cfg.timer_sel = c.timer;
        cfg.duty = 0;
        cfg.hpoint = 0;
        ESP_ERROR_CHECK(ledc_channel_config(&cfg));
    }
}

static void ledc_apply(const le_output_t *o)
{
    ledc_set_duty_with_hpoint(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, o->dim_duty, 0);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
    ledc_set_duty_with_hpoint(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1, o->cw_on ? o->cw_duty : 0, o->cw_hpoint);
    ledc_set_duty_with_hpoint(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_2, o->ww_on ? o->ww_duty : 0, o->ww_hpoint);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_1);
    ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_2);
}

static void outputs_off(void)
{
    le_output_t o = {};
    ledc_apply(&o);
}

/* ------------------------------------------------------------------ ADC */
static void adc_init(void)
{
    adc_oneshot_unit_init_cfg_t init_cfg = {};
    init_cfg.unit_id = ADC_UNIT_1;
    init_cfg.ulp_mode = ADC_ULP_MODE_DISABLE;
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&init_cfg, &s_adc));

    adc_oneshot_chan_cfg_t ch_cfg = {};
    ch_cfg.atten = ADC_ATTEN_DB_12;           /* 0 .. ~3.1 V */
    ch_cfg.bitwidth = ADC_BITWIDTH_DEFAULT;
    for (int ch : { ADC_CH_VOUT, ADC_CH_NTC, ADC_CH_ISENSE }) {
        ESP_ERROR_CHECK(adc_oneshot_config_channel(s_adc, (adc_channel_t)ch, &ch_cfg));
    }

    adc_cali_curve_fitting_config_t cali_cfg = {};
    cali_cfg.unit_id = ADC_UNIT_1;
    cali_cfg.atten = ADC_ATTEN_DB_12;
    cali_cfg.bitwidth = ADC_BITWIDTH_DEFAULT;
    if (adc_cali_create_scheme_curve_fitting(&cali_cfg, &s_adc_cali) != ESP_OK) {
        ESP_LOGW(TAG, "ADC calibration not available, using nominal scale");
        s_adc_cali = nullptr;
    }
}

/* averaged channel voltage in volts */
static float adc_read_v(int ch, int samples = 16)
{
    int acc = 0;
    for (int i = 0; i < samples; i++) {
        int raw = 0;
        if (adc_oneshot_read(s_adc, (adc_channel_t)ch, &raw) == ESP_OK) {
            acc += raw;
        }
    }
    int raw_avg = acc / samples;
    int mv = 0;
    if (s_adc_cali && adc_cali_raw_to_voltage(s_adc_cali, raw_avg, &mv) == ESP_OK) {
        return mv / 1000.0f;
    }
    return raw_avg * (3.1f / 4095.0f);
}

static float ntc_to_celsius(float v)
{
    if (v <= 0.01f || v >= 3.29f) {
        return 25.0f;                               /* open / short sensor -> ignore */
    }
    float r = v * NTC_PULLUP_OHM / (3.3f - v);
    float inv_t = 1.0f / 298.15f + logf(r / NTC_R25_OHM) / NTC_BETA;
    return 1.0f / inv_t - 273.15f;
}

static void measure(void)
{
    s.vout_v = adc_read_v(ADC_CH_VOUT) * VOUT_DIVIDER_RATIO;
    s.iout_ma = adc_read_v(ADC_CH_ISENSE) / 0.753f * 1000.0f;   /* 0.753 V = 1.0 A */
    s.temp_c = ntc_to_celsius(adc_read_v(ADC_CH_NTC, 4));
}

/* ------------------------------------------------------------------ DIP switches */
static uint8_t dip_read(void)
{
    uint8_t code = 0;
    if (gpio_get_level((gpio_num_t)PIN_DIP1) == 0) code |= 1;
    if (gpio_get_level((gpio_num_t)PIN_DIP2) == 0) code |= 2;
    if (gpio_get_level((gpio_num_t)PIN_DIP3) == 0) code |= 4;
    return code;
}

static void dip_poll(void)
{
    uint8_t now = dip_read();
    if (now != s.dip_candidate) {
        s.dip_candidate = now;
        s.dip_stable_ticks = 0;
        return;
    }
    if (s.dip_stable_ticks < 255) {
        s.dip_stable_ticks++;
    }
    if (s.dip_stable_ticks == DIP_DEBOUNCE_TICKS && now != s.dip_code) {
        s.dip_code = now;
        s.i_max_ma = le_dip_to_current_ma(now);
        ESP_LOGI(TAG, "DIP changed: S3S2S1=%d%d%d -> I_max = %u mA", (now >> 2) & 1, (now >> 1) & 1, now & 1, s.i_max_ma);
    }
}

/* ------------------------------------------------------------------ status LED */
static inline void led_write(bool on)
{
    gpio_set_level((gpio_num_t)PIN_STATUS_LED, on ? 0 : 1);        /* active low */
}

void app_driver_set_led_pattern(app_led_pattern_t pattern)
{
    s.led_pattern = pattern;
    s.led_ticks = 0;
}

static void led_tick(void)
{
    uint32_t t = s.led_ticks++;          /* 10 ms units */
    switch (s.led_pattern) {
    case LED_PATTERN_COMMISSIONING: led_write((t % 100) < 50); break;                       /* 1 Hz */
    case LED_PATTERN_CONNECTED:     led_write(t < 200); if (t >= 200) s.led_pattern = LED_PATTERN_OFF; break;
    case LED_PATTERN_FACTORY_RESET: led_write((t % 10) < 5); break;                         /* 10 Hz */
    case LED_PATTERN_FAULT_OPEN:
    case LED_PATTERN_FAULT_OVERTEMP:
    case LED_PATTERN_FAULT_SHORT: {
        uint32_t n = (s.led_pattern == LED_PATTERN_FAULT_OPEN) ? 2 : (s.led_pattern == LED_PATTERN_FAULT_OVERTEMP) ? 3 : 5;
        uint32_t period = n * 40 + 100;                                                    /* blinks + pause */
        uint32_t p = t % period;
        led_write(p < n * 40 && (p % 40) < 20);
        break;
    }
    default: led_write(false); break;
    }
}

/* ------------------------------------------------------------------ protections */
static void protections_tick(void)
{
    /* thermal derating 100 % at NTC_DERATE_C -> 20 % at NTC_SHUTDOWN_C, off above */
    if (s.temp_c >= NTC_SHUTDOWN_C) {
        s.derate_pct = 0;
        if (s.fault == FAULT_NONE) {
            s.fault = FAULT_OVERTEMP;
            s.fault_ticks = 0;
            app_driver_set_led_pattern(LED_PATTERN_FAULT_OVERTEMP);
            ESP_LOGE(TAG, "Over-temperature %.1f C -> output off", s.temp_c);
        }
    } else if (s.temp_c > NTC_DERATE_C) {
        float k = (s.temp_c - NTC_DERATE_C) / (float)(NTC_SHUTDOWN_C - NTC_DERATE_C);
        s.derate_pct = (uint16_t)(100.0f - 80.0f * k);
    } else {
        s.derate_pct = 100;
    }

    if (s.fault != FAULT_NONE) {
        s.fault_ticks++;
        if (s.fault_ticks * ENGINE_TICK_MS >= FAULT_RETRY_MS && s.temp_c < NTC_DERATE_C) {
            ESP_LOGW(TAG, "Fault %d cleared, retrying", s.fault);
            s.fault = FAULT_NONE;
            s.connect_pct = 0;              /* restart with soft-connect */
            s.on_ticks = 0;
            app_driver_set_led_pattern(LED_PATTERN_OFF);
        }
        return;
    }

    /* open load / short circuit are only meaningful when fully on for a while */
    if (s.on && s.connect_pct == 100 && s.derate_pct > 0) {
        s.on_ticks++;
        if (s.on_ticks > 50) {                                        /* 500 ms after connect */
            if (s.vout_v > VOUT_OPEN_LOAD_V && s.iout_ma < 0.2f * s.i_max_ma) {
                s.fault = FAULT_OPEN_LOAD;
                s.fault_ticks = 0;
                app_driver_set_led_pattern(LED_PATTERN_FAULT_OPEN);
                ESP_LOGE(TAG, "Open load: V+=%.1f V I=%.0f mA", s.vout_v, s.iout_ma);
            } else if (s.vout_v < VOUT_SHORT_V) {
                s.fault = FAULT_SHORT;
                s.fault_ticks = 0;
                app_driver_set_led_pattern(LED_PATTERN_FAULT_SHORT);
                ESP_LOGE(TAG, "Short circuit: V+=%.1f V", s.vout_v);
            }
        }
    } else {
        s.on_ticks = 0;
    }
}

/* ------------------------------------------------------------------ engine tick (10 ms) */
static void engine_tick(void *arg)
{
    s_tick++;
    le_fader_tick(&s.fader);

    if ((s_tick % (DIP_POLL_MS / ENGINE_TICK_MS)) == 0) {
        dip_poll();
        measure();
        protections_tick();
    }
    led_tick();

    bool on = s.on && s.fault == FAULT_NONE;
    /* soft-connect: ramp the channel duty when turning on from the CV (45 V) state */
    if (on && !s.was_on) {
        s.connect_pct = 0;
    }
    s.was_on = on;
    if (on && s.connect_pct < 100) {
        uint32_t step = 100 * ENGINE_TICK_MS / SOFT_CONNECT_MS;
        s.connect_pct = (uint8_t)((s.connect_pct + step > 100) ? 100 : s.connect_pct + step);
    }

    le_input_t in = {};
    in.on = on;
    in.level = (uint8_t)(s.fader.cur_level + 0.5f);
    in.mireds = (uint16_t)(s.fader.cur_mireds + 0.5f);
    in.i_max_ma = s.i_max_ma;
    in.derate_pct = s.derate_pct;
    in.connect_pct = on ? s.connect_pct : 0;
    if (s.identify && on) {
        in.level = ((s_tick / 25) & 1) ? 254 : 26;                    /* 2 Hz blink 10 %/100 % */
    }
    le_output_t out;
    le_compute(&in, &out);
    ledc_apply(&out);
}

/* ------------------------------------------------------------------ button */
static void button_single_click_cb(void *arg, void *usr_data)
{
    if (s.endpoint_id == 0) {
        return;
    }
    attribute_t *attribute = attribute::get(s.endpoint_id, OnOff::Id, OnOff::Attributes::OnOff::Id);
    esp_matter_attr_val_t val = esp_matter_invalid(NULL);
    attribute::get_val(attribute, &val);
    val.val.b = !val.val.b;
    attribute::update(s.endpoint_id, OnOff::Id, OnOff::Attributes::OnOff::Id, &val);
    ESP_LOGI(TAG, "Button: toggle -> %s", val.val.b ? "ON" : "OFF");
}

static void button_long_press_cb(void *arg, void *usr_data)
{
    ESP_LOGW(TAG, "Button held 5 s -> factory reset");
    app_driver_set_led_pattern(LED_PATTERN_FACTORY_RESET);
    esp_matter::factory_reset();
}

static void button_init(void)
{
    button_config_t cfg = {};
    cfg.type = BUTTON_TYPE_GPIO;
    cfg.long_press_time = 5000;
    cfg.short_press_time = 50;
    cfg.gpio_button_config.gpio_num = PIN_BUTTON;
    cfg.gpio_button_config.active_level = 0;
    button_handle_t h = iot_button_create(&cfg);
    if (h) {
        iot_button_register_cb(h, BUTTON_SINGLE_CLICK, button_single_click_cb, NULL);
        iot_button_register_cb(h, BUTTON_LONG_PRESS_START, button_long_press_cb, NULL);
    }
}

/* ------------------------------------------------------------------ public API */
app_driver_handle_t app_driver_light_init(void)
{
    /* GPIO: DIP inputs with pull-ups, LED output */
    gpio_config_t in_cfg = {};
    in_cfg.pin_bit_mask = (1ULL << PIN_DIP1) | (1ULL << PIN_DIP2) | (1ULL << PIN_DIP3);
    in_cfg.mode = GPIO_MODE_INPUT;
    in_cfg.pull_up_en = GPIO_PULLUP_ENABLE;
    ESP_ERROR_CHECK(gpio_config(&in_cfg));
    gpio_config_t out_cfg = {};
    out_cfg.pin_bit_mask = (1ULL << PIN_STATUS_LED);
    out_cfg.mode = GPIO_MODE_OUTPUT;
    ESP_ERROR_CHECK(gpio_config(&out_cfg));
    led_write(false);

    ledc_init();
    outputs_off();
    adc_init();

    s.dip_code = s.dip_candidate = dip_read();
    s.dip_stable_ticks = DIP_DEBOUNCE_TICKS;
    s.i_max_ma = le_dip_to_current_ma(s.dip_code);
    s.derate_pct = 100;
    s.on = false;
    s.level = DEFAULT_BRIGHTNESS;
    s.mireds = DEFAULT_MIREDS;
    le_fader_init(&s.fader, DEFAULT_BRIGHTNESS, DEFAULT_MIREDS);
    measure();
    ESP_LOGI(TAG, "DIP S3S2S1=%d%d%d -> I_max=%u mA | V+=%.1f V T=%.1f C",
             (s.dip_code >> 2) & 1, (s.dip_code >> 1) & 1, s.dip_code & 1, s.i_max_ma, s.vout_v, s.temp_c);

    button_init();

    esp_timer_create_args_t targs = {};
    targs.callback = engine_tick;
    targs.name = "light_engine";
    targs.dispatch_method = ESP_TIMER_TASK;
    ESP_ERROR_CHECK(esp_timer_create(&targs, &s_tick_timer));
    ESP_ERROR_CHECK(esp_timer_start_periodic(s_tick_timer, ENGINE_TICK_MS * 1000ULL));
    return (app_driver_handle_t)&s;
}

void app_driver_set_endpoint(uint16_t endpoint_id)
{
    s.endpoint_id = endpoint_id;
}

static void set_targets(bool on, uint8_t level, uint16_t mireds)
{
    s.on = on;
    s.level = level;
    s.mireds = mireds;
    le_fader_set_target(&s.fader, level, mireds, FADE_DEFAULT_MS, ENGINE_TICK_MS);
}

esp_err_t app_driver_attribute_update(app_driver_handle_t driver_handle, uint16_t endpoint_id,
                                      uint32_t cluster_id, uint32_t attribute_id, esp_matter_attr_val_t *val)
{
    if (endpoint_id != s.endpoint_id) {
        return ESP_OK;
    }
    if (cluster_id == OnOff::Id && attribute_id == OnOff::Attributes::OnOff::Id) {
        ESP_LOGI(TAG, "OnOff -> %d", val->val.b);
        set_targets(val->val.b, s.level, s.mireds);
    } else if (cluster_id == LevelControl::Id && attribute_id == LevelControl::Attributes::CurrentLevel::Id) {
        uint8_t lv = val->val.u8;
        if (lv < 1) lv = 1;
        if (lv > 254) lv = 254;
        ESP_LOGD(TAG, "Level -> %u", lv);
        set_targets(s.on, lv, s.mireds);
    } else if (cluster_id == ColorControl::Id && attribute_id == ColorControl::Attributes::ColorTemperatureMireds::Id) {
        uint16_t m = val->val.u16;
        if (m < CCT_MIN_MIREDS) m = CCT_MIN_MIREDS;
        if (m > CCT_MAX_MIREDS) m = CCT_MAX_MIREDS;
        ESP_LOGD(TAG, "Mireds -> %u (%u K)", m, 1000000 / m);
        set_targets(s.on, s.level, m);
    }
    return ESP_OK;
}

esp_err_t app_driver_light_set_defaults(uint16_t endpoint_id)
{
    esp_matter_attr_val_t val = esp_matter_invalid(NULL);
    attribute_t *a;
    bool on = DEFAULT_POWER;
    uint8_t level = DEFAULT_BRIGHTNESS;
    uint16_t mireds = DEFAULT_MIREDS;

    a = attribute::get(endpoint_id, OnOff::Id, OnOff::Attributes::OnOff::Id);
    if (a && attribute::get_val(a, &val) == ESP_OK) on = val.val.b;
    a = attribute::get(endpoint_id, LevelControl::Id, LevelControl::Attributes::CurrentLevel::Id);
    if (a && attribute::get_val(a, &val) == ESP_OK && val.val.u8 >= 1) level = val.val.u8;
    a = attribute::get(endpoint_id, ColorControl::Id, ColorControl::Attributes::ColorTemperatureMireds::Id);
    if (a && attribute::get_val(a, &val) == ESP_OK && val.val.u16 >= CCT_MIN_MIREDS && val.val.u16 <= CCT_MAX_MIREDS) mireds = val.val.u16;

    le_fader_init(&s.fader, level, mireds);
    set_targets(on, level, mireds);
    ESP_LOGI(TAG, "Defaults applied: on=%d level=%u mireds=%u", on, level, mireds);
    return ESP_OK;
}

void app_driver_identify_start(void) { s.identify = true; }
void app_driver_identify_stop(void)  { s.identify = false; }

void app_driver_get_status(app_driver_status_t *out)
{
    out->vout_v = s.vout_v;
    out->iout_ma = s.iout_ma;
    out->temp_c = s.temp_c;
    out->i_max_ma = s.i_max_ma;
    out->dip_code = s.dip_code;
    out->fault = (uint8_t)s.fault;
}

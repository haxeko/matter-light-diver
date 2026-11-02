/*
 * app_main.cpp - Matter over Thread "Color Temperature Light" (device type 0x010C)
 * for the 3-wire CCT LED driver.  Structure follows esp-matter/examples/light.
 *
 * Tested API level: esp-matter v1.3 / v1.4 with ESP-IDF v5.2.x.
 */
#include <esp_err.h>
#include <esp_log.h>
#include <nvs_flash.h>

#include <esp_matter.h>
#include <esp_matter_console.h>
#include <esp_matter_ota.h>
#include <common_macros.h>

#include "app_driver.h"
#include "board_config.h"

#if CHIP_DEVICE_CONFIG_ENABLE_THREAD
#include <platform/ESP32/OpenthreadLauncher.h>
#endif

static const char *TAG = "app_main";
uint16_t light_endpoint_id = 0;

using namespace esp_matter;
using namespace esp_matter::attribute;
using namespace esp_matter::endpoint;
using namespace chip::app::Clusters;

/* ------------------------------------------------------------------ Matter events */
static void app_event_cb(const ChipDeviceEvent *event, intptr_t arg)
{
    switch (event->Type) {
    case chip::DeviceLayer::DeviceEventType::kInterfaceIpAddressChanged:
        ESP_LOGI(TAG, "Interface IP address changed");
        break;
    case chip::DeviceLayer::DeviceEventType::kCommissioningComplete:
        ESP_LOGI(TAG, "Commissioning complete");
        app_driver_set_led_pattern(LED_PATTERN_CONNECTED);
        break;
    case chip::DeviceLayer::DeviceEventType::kFailSafeTimerExpired:
        ESP_LOGW(TAG, "Commissioning failed, fail-safe timer expired");
        break;
    case chip::DeviceLayer::DeviceEventType::kCommissioningSessionStarted:
        ESP_LOGI(TAG, "Commissioning session started");
        app_driver_set_led_pattern(LED_PATTERN_COMMISSIONING);
        break;
    case chip::DeviceLayer::DeviceEventType::kCommissioningSessionStopped:
        ESP_LOGI(TAG, "Commissioning session stopped");
        break;
    case chip::DeviceLayer::DeviceEventType::kCommissioningWindowOpened:
        ESP_LOGI(TAG, "Commissioning window opened");
        app_driver_set_led_pattern(LED_PATTERN_COMMISSIONING);
        break;
    case chip::DeviceLayer::DeviceEventType::kCommissioningWindowClosed:
        ESP_LOGI(TAG, "Commissioning window closed");
        break;
    case chip::DeviceLayer::DeviceEventType::kFabricRemoved: {
        ESP_LOGI(TAG, "Fabric removed successfully");
        if (chip::Server::GetInstance().GetFabricTable().FabricCount() == 0) {
            chip::CommissioningWindowManager &mgr = chip::Server::GetInstance().GetCommissioningWindowManager();
            constexpr auto kTimeoutSeconds = chip::System::Clock::Seconds16(k_timeout_seconds);
            if (!mgr.IsCommissioningWindowOpen()) {
                /* re-open the pairing window so the driver can be re-commissioned */
                CHIP_ERROR err = mgr.OpenBasicCommissioningWindow(kTimeoutSeconds,
                                        chip::CommissioningWindowAdvertisement::kDnssdOnly);
                if (err != CHIP_NO_ERROR) {
                    ESP_LOGE(TAG, "Failed to open commissioning window, err:%" CHIP_ERROR_FORMAT, err.Format());
                }
            }
            app_driver_set_led_pattern(LED_PATTERN_COMMISSIONING);
        }
        break;
    }
    case chip::DeviceLayer::DeviceEventType::kThreadConnectivityChange:
        ESP_LOGI(TAG, "Thread connectivity changed");
        break;
    default:
        break;
    }
}

/* ------------------------------------------------------------------ identify */
static esp_err_t app_identification_cb(identification::callback_type_t type, uint16_t endpoint_id,
                                       uint8_t effect_id, uint8_t effect_variant, void *priv_data)
{
    ESP_LOGI(TAG, "Identification callback: type: %u, effect: %u, variant: %u", type, effect_id, effect_variant);
    if (type == identification::START) {
        app_driver_identify_start();
    } else if (type == identification::STOP) {
        app_driver_identify_stop();
    }
    return ESP_OK;
}

/* ------------------------------------------------------------------ attribute writes */
static esp_err_t app_attribute_update_cb(attribute::callback_type_t type, uint16_t endpoint_id, uint32_t cluster_id,
                                         uint32_t attribute_id, esp_matter_attr_val_t *val, void *priv_data)
{
    esp_err_t err = ESP_OK;
    if (type == PRE_UPDATE) {
        app_driver_handle_t driver_handle = (app_driver_handle_t)priv_data;
        err = app_driver_attribute_update(driver_handle, endpoint_id, cluster_id, attribute_id, val);
    }
    return err;
}

extern "C" void app_main()
{
    esp_err_t err = ESP_OK;

    /* NVS: Matter stack + our calibration data */
    nvs_flash_init();

    /* Hardware first, so the lamp is in a safe state (switches off) before the stack starts */
    app_driver_handle_t light_handle = app_driver_light_init();

    /* Matter node */
    node::config_t node_config;
    node_t *node = node::create(&node_config, app_attribute_update_cb, app_identification_cb);
    ABORT_APP_ON_FAILURE(node != nullptr, ESP_LOGE(TAG, "Failed to create Matter node"));

    /* Color Temperature Light endpoint: OnOff + LevelControl + ColorControl(CT) + Identify + Groups + Scenes */
    color_temperature_light::config_t light_config;
    light_config.on_off.on_off = DEFAULT_POWER;
    light_config.on_off.lighting.start_up_on_off = nullptr;              /* restore previous state   */
    light_config.level_control.current_level = DEFAULT_BRIGHTNESS;
    light_config.level_control.on_level = DEFAULT_BRIGHTNESS;
    light_config.level_control.lighting.start_up_current_level = DEFAULT_BRIGHTNESS;
    light_config.color_control.color_mode = (uint8_t)ColorControl::ColorMode::kColorTemperature;
    light_config.color_control.enhanced_color_mode = (uint8_t)ColorControl::ColorMode::kColorTemperature;
    light_config.color_control.color_temperature.color_temperature_mireds = DEFAULT_MIREDS;
    light_config.color_control.color_temperature.color_temp_physical_min_mireds = CCT_MIN_MIREDS;
    light_config.color_control.color_temperature.color_temp_physical_max_mireds = CCT_MAX_MIREDS;
    light_config.color_control.color_temperature.couple_color_temp_to_level_min_mireds = CCT_MIN_MIREDS;
    light_config.color_control.color_temperature.startup_color_temperature_mireds = DEFAULT_MIREDS;

    endpoint_t *endpoint = color_temperature_light::create(node, &light_config, ENDPOINT_FLAG_NONE, light_handle);
    ABORT_APP_ON_FAILURE(endpoint != nullptr, ESP_LOGE(TAG, "Failed to create color temperature light endpoint"));

    light_endpoint_id = endpoint::get_id(endpoint);
    app_driver_set_endpoint(light_endpoint_id);
    ESP_LOGI(TAG, "Light created with endpoint_id %d", light_endpoint_id);

#if CHIP_DEVICE_CONFIG_ENABLE_THREAD
    /* OpenThread platform (native 802.15.4 radio of the ESP32-C6) */
    esp_openthread_platform_config_t config = {
        .radio_config = ESP_OPENTHREAD_DEFAULT_RADIO_CONFIG(),
        .host_config = ESP_OPENTHREAD_DEFAULT_HOST_CONFIG(),
        .port_config = ESP_OPENTHREAD_DEFAULT_PORT_CONFIG(),
    };
    set_openthread_platform_config(&config);
#endif

    /* Start Matter (BLE commissioning advertising begins if not yet commissioned) */
    err = esp_matter::start(app_event_cb);
    ABORT_APP_ON_FAILURE(err == ESP_OK, ESP_LOGE(TAG, "Failed to start Matter, err:%d", err));

    /* Apply the persisted attribute values to the hardware */
    app_driver_light_set_defaults(light_endpoint_id);

#if CONFIG_ENABLE_CHIP_SHELL
    esp_matter::console::diagnostics_register_commands();
    esp_matter::console::wifi_register_commands();
    esp_matter::console::init();
#endif
}

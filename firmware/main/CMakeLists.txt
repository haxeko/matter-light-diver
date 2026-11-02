idf_component_register(
    SRCS "app_main.cpp" "app_driver.cpp" "light_engine.c"
    INCLUDE_DIRS "."
    PRIV_REQUIRES esp_matter esp_adc driver esp_timer nvs_flash button
)
set_property(TARGET ${COMPONENT_LIB} PROPERTY CXX_STANDARD 17)
target_compile_options(${COMPONENT_LIB} PRIVATE "-DCHIP_HAVE_CONFIG_H")

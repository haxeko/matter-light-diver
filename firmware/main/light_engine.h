/*
 * light_engine.h - Pure-C maths for the 3-wire CCT driver (no ESP-IDF dependency, host-testable).
 *
 * Inputs : Matter state (on/off, level 1..254, colour temperature in mireds),
 *          DIP power selection (max current), thermal derating, soft-connect factor.
 * Outputs: LEDC duty values for the current reference (12 bit) and the two channel
 *          switches (13 bit, complementary with overlap).
 */
#pragma once
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    bool     on;
    uint8_t  level;          /* 1..254 (Matter LevelControl CurrentLevel)        */
    uint16_t mireds;         /* 153..370                                         */
    uint16_t i_max_ma;       /* from DIP table, <= I_HW_MAX_MA                   */
    uint16_t derate_pct;     /* 100 = no derating, 0 = off (thermal)             */
    uint16_t connect_pct;    /* soft-connect factor 0..100 (channel duty scale)  */
} le_input_t;

typedef struct {
    uint16_t i_target_ma;    /* current demanded from the CC loop                */
    uint32_t dim_duty;       /* 0..2^DIM_PWM_RES_BITS                             */
    uint32_t cw_duty;        /* 0..2^CH_PWM_RES_BITS (includes overlap)           */
    uint32_t cw_hpoint;      /* always 0                                         */
    uint32_t ww_duty;        /* 0..2^CH_PWM_RES_BITS                              */
    uint32_t ww_hpoint;      /* phase of the WW pulse (starts when CW ends)      */
    bool     cw_on;          /* false -> keep the switch hard off                */
    bool     ww_on;
} le_output_t;

/* perceptual (square-law) brightness fraction, floored at I_MIN_MA / i_max */
float    le_level_to_fraction(uint8_t level, uint16_t i_max_ma);
/* 0.0 = cool only, 1.0 = warm only, clamped to CCT limits */
float    le_mireds_to_warm_fraction(uint16_t mireds);
/* overlap in counts for the given period frequency / resolution */
uint32_t le_overlap_counts(uint32_t freq_hz, uint32_t res_bits, uint32_t overlap_us);
/* main computation */
void     le_compute(const le_input_t *in, le_output_t *out);

/* ------------------------------------------------------------ fader (linear, per tick) */
typedef struct {
    float cur_level, tgt_level, step_level;
    float cur_mireds, tgt_mireds, step_mireds;
    bool  active;
} le_fader_t;

void le_fader_init(le_fader_t *f, uint8_t level, uint16_t mireds);
void le_fader_set_target(le_fader_t *f, uint8_t level, uint16_t mireds, uint32_t fade_ms, uint32_t tick_ms);
/* returns true while still moving */
bool le_fader_tick(le_fader_t *f);

/* DIP code (bit0 = SW1 ... bit2 = SW3, 1 = ON) -> max current */
uint16_t le_dip_to_current_ma(uint8_t dip_code);

#ifdef __cplusplus
}
#endif

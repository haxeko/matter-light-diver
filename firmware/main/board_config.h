/*
 * board_config.h - Hardware mapping for the 3-wire CCT LED driver (ESP32-C6, Matter over Thread).
 *
 * Every number here mirrors the hardware documented in docs/03 and docs/04.
 * Change the DIP table / scaling constants here if the shunt, gain or divider change.
 */
#pragma once

/* ---------------------------------------------------------------- GPIO map */
#define PIN_PWM_CW        0     /* LEDC ch0  -> U5 -> Q2 (cool white low-side switch)  */
#define PIN_PWM_WW        1     /* LEDC ch1  -> U6 -> Q3 (warm white low-side switch)  */
#define PIN_PWM_DIM       2     /* LEDC ch2  -> RC filter -> current reference (VREF)  */
#define PIN_ADC_VOUT      3     /* ADC1_CH3  <- V+ via 150k/10k                        */
#define PIN_ADC_NTC       4     /* ADC1_CH4  <- 10k / NTC 10k B3950                    */
#define PIN_ADC_ISENSE    6     /* ADC1_CH6  <- ISENSE_AMP (0.753 V = 1.0 A)           */
#define PIN_BUTTON        9     /* active low, 10k pull-up, also BOOT strapping pin    */
#define PIN_STATUS_LED    7     /* active low (IO10 is not bonded out on ESP32-C6-MINI-1) */
#define PIN_DIP1          18    /* active low (switch to GND), internal pull-up        */
#define PIN_DIP2          19
#define PIN_DIP3          20

#define ADC_CH_VOUT       3
#define ADC_CH_NTC        4
#define ADC_CH_ISENSE     6

/* ---------------------------------------------------------------- LEDC */
#define DIM_PWM_FREQ_HZ   19531   /* 80 MHz / 2^12                                     */
#define DIM_PWM_RES_BITS  12
#define CH_PWM_FREQ_HZ    4000    /* CW/WW complementary switching                     */
#define CH_PWM_RES_BITS   13      /* 8192 counts per period (80 MHz / 8192 = 9.7 kHz max) */
#define CH_OVERLAP_US     2       /* make-before-break overlap at the CW->WW edge      */

/* ---------------------------------------------------------------- current scaling
 * VREF(100 % duty) = 3.3 V * 9.76k/(33k+9.76k) = 0.753 V
 * I = VREF / (gain * Rsense) = 0.753 / (5.02 * 0.15) = 1.000 A  -> duty = I_mA / 1000
 */
#define I_HW_MAX_MA       1000    /* hardware clamp, do not raise without changing R12/R13 */
#define I_MIN_MA          10      /* lowest controllable current (1 %)                 */
#define DIP_CURRENT_TABLE_MA { 250, 350, 450, 550, 650, 750, 850, 950 }  /* index = S3S2S1 */

/* ---------------------------------------------------------------- colour */
#define CCT_MIN_MIREDS    153     /* 6500 K */
#define CCT_MAX_MIREDS    370     /* 2700 K */
#define CCT_DEFAULT_MIREDS 250    /* 4000 K */

/* ---------------------------------------------------------------- behaviour */
#define SOFT_CONNECT_MS   40      /* ramp of the channel duty when switching on from CV mode */
#define FADE_DEFAULT_MS   250     /* local smoothing of level / colour steps            */
#define ENGINE_TICK_MS    10
#define DIP_POLL_MS       100
#define DIP_DEBOUNCE_TICKS 5      /* 500 ms stable before applying a new power setting */

/* ---------------------------------------------------------------- protection */
#define VOUT_DIVIDER_RATIO 16.0f  /* (150k + 10k) / 10k                                 */
#define VOUT_OPEN_LOAD_V   44.0f  /* V+ still at CV clamp while ON  -> no lamp         */
#define VOUT_SHORT_V       8.0f   /* V+ collapsed while current flows -> short circuit */
#define FAULT_RETRY_MS     5000
#define NTC_DERATE_C       85
#define NTC_SHUTDOWN_C     100
#define NTC_R25_OHM        10000.0f
#define NTC_BETA           3950.0f
#define NTC_PULLUP_OHM     10000.0f

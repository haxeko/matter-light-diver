/* Host unit test for light_engine.c:  cc -I../main test_light_engine.c ../main/light_engine.c -lm */
#include "light_engine.h"
#include "board_config.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
    le_input_t in = { .on = true, .level = 254, .mireds = CCT_MIN_MIREDS, .i_max_ma = 950, .derate_pct = 100, .connect_pct = 100 };
    le_output_t out;
    const uint32_t n_ch = 1u << CH_PWM_RES_BITS, n_dim = 1u << DIM_PWM_RES_BITS;

    /* full brightness, cool only */
    le_compute(&in, &out);
    assert(out.i_target_ma == 950);
    assert(out.dim_duty == (uint32_t)(0.95 * n_dim + 0.5));
    assert(out.cw_on && !out.ww_on && out.cw_duty == n_ch && out.ww_duty == 0);

    /* warm only */
    in.mireds = CCT_MAX_MIREDS;
    le_compute(&in, &out);
    assert(!out.cw_on && out.ww_on && out.ww_duty == n_ch && out.ww_hpoint == 0);

    /* 50/50 mix: WW starts where CW ends, CW extended by the overlap */
    in.mireds = (CCT_MIN_MIREDS + CCT_MAX_MIREDS) / 2;
    le_compute(&in, &out);
    uint32_t ovl = le_overlap_counts(CH_PWM_FREQ_HZ, CH_PWM_RES_BITS, CH_OVERLAP_US);
    assert(ovl > 0 && ovl < 200);
    assert(out.ww_hpoint + out.ww_duty == n_ch || out.ww_hpoint + out.ww_duty == n_ch + 1);
    assert(out.cw_duty == out.ww_hpoint + ovl);

    /* soft-connect 50 %: both channels scaled, sum = half period */
    in.connect_pct = 50;
    le_compute(&in, &out);
    assert(out.ww_hpoint + out.ww_duty <= n_ch / 2 + 1);
    in.connect_pct = 100;

    /* level 1 must give I_MIN_MA, never zero; monotonic in level */
    uint16_t last = 0;
    for (int lv = 1; lv <= 254; lv++) {
        in.level = (uint8_t)lv;
        le_compute(&in, &out);
        assert(out.i_target_ma >= I_MIN_MA);
        assert(out.i_target_ma >= last);
        assert(out.dim_duty <= n_dim);
        last = out.i_target_ma;
    }
    assert(last == 950);

    /* hardware clamp cannot be exceeded */
    in.i_max_ma = 5000;
    in.level = 254;
    le_compute(&in, &out);
    assert(out.i_target_ma == I_HW_MAX_MA && out.dim_duty == n_dim);

    /* derating and off */
    in.i_max_ma = 950;
    in.derate_pct = 50;
    le_compute(&in, &out);
    assert(out.i_target_ma == 475);
    in.on = false;
    le_compute(&in, &out);
    assert(out.dim_duty == 0 && !out.cw_on && !out.ww_on);

    /* DIP table */
    assert(le_dip_to_current_ma(0) == 250 && le_dip_to_current_ma(7) == 950 && le_dip_to_current_ma(5) == 750);

    /* fader reaches the target */
    le_fader_t f;
    le_fader_init(&f, 10, 200);
    le_fader_set_target(&f, 254, 370, 250, 10);
    int ticks = 0;
    while (le_fader_tick(&f)) {
        ticks++;
    }
    assert(ticks >= 24 && ticks <= 26 && f.cur_level == 254.0f && f.cur_mireds == 370.0f);

    printf("light_engine: all tests passed (overlap=%u counts)\n", (unsigned)ovl);
    return 0;
}

#include "light_engine.h"
#include "board_config.h"
#include <math.h>

static const uint16_t s_dip_table[8] = DIP_CURRENT_TABLE_MA;

uint16_t le_dip_to_current_ma(uint8_t dip_code)
{
    uint16_t i = s_dip_table[dip_code & 0x07];
    return i > I_HW_MAX_MA ? I_HW_MAX_MA : i;
}

float le_level_to_fraction(uint8_t level, uint16_t i_max_ma)
{
    if (level == 0) {
        return 0.0f;
    }
    if (level > 254) {
        level = 254;
    }
    float x = (float)level / 254.0f;
    float f = x * x;                                   /* square law ~ perceptual */
    float f_min = (i_max_ma > 0) ? (float)I_MIN_MA / (float)i_max_ma : 0.0f;
    if (f < f_min) {
        f = f_min;
    }
    return f > 1.0f ? 1.0f : f;
}

float le_mireds_to_warm_fraction(uint16_t mireds)
{
    if (mireds <= CCT_MIN_MIREDS) {
        return 0.0f;
    }
    if (mireds >= CCT_MAX_MIREDS) {
        return 1.0f;
    }
    return (float)(mireds - CCT_MIN_MIREDS) / (float)(CCT_MAX_MIREDS - CCT_MIN_MIREDS);
}

uint32_t le_overlap_counts(uint32_t freq_hz, uint32_t res_bits, uint32_t overlap_us)
{
    uint32_t n = 1u << res_bits;
    /* counts = overlap_us * 1e-6 * freq * n */
    uint64_t c = ((uint64_t)overlap_us * freq_hz * n + 500000ULL) / 1000000ULL;
    return (uint32_t)c;
}

void le_compute(const le_input_t *in, le_output_t *out)
{
    const uint32_t n_dim = 1u << DIM_PWM_RES_BITS;
    const uint32_t n_ch  = 1u << CH_PWM_RES_BITS;
    const uint32_t ovl   = le_overlap_counts(CH_PWM_FREQ_HZ, CH_PWM_RES_BITS, CH_OVERLAP_US);

    out->cw_hpoint = 0;
    if (!in->on || in->level == 0 || in->derate_pct == 0 || in->connect_pct == 0) {
        out->i_target_ma = 0;
        out->dim_duty = 0;
        out->cw_duty = out->ww_duty = 0;
        out->ww_hpoint = 0;
        out->cw_on = out->ww_on = false;
        return;
    }

    uint16_t i_max = in->i_max_ma > I_HW_MAX_MA ? I_HW_MAX_MA : in->i_max_ma;
    float frac = le_level_to_fraction(in->level, i_max);
    float derate = (in->derate_pct > 100 ? 100 : in->derate_pct) / 100.0f;
    float i_ma = (float)i_max * frac * derate;
    if (i_ma < (float)I_MIN_MA) {
        i_ma = (float)I_MIN_MA;
    }
    if (i_ma > (float)I_HW_MAX_MA) {
        i_ma = (float)I_HW_MAX_MA;
    }
    out->i_target_ma = (uint16_t)(i_ma + 0.5f);
    /* duty = I / I_HW_MAX exactly, see board_config.h */
    out->dim_duty = (uint32_t)((i_ma / (float)I_HW_MAX_MA) * (float)n_dim + 0.5f);
    if (out->dim_duty > n_dim) {
        out->dim_duty = n_dim;
    }

    float w = le_mireds_to_warm_fraction(in->mireds);
    float s = (in->connect_pct > 100 ? 100 : in->connect_pct) / 100.0f;
    uint32_t cw = (uint32_t)((1.0f - w) * s * (float)n_ch + 0.5f);
    uint32_t ww = (uint32_t)(w * s * (float)n_ch + 0.5f);
    if (cw + ww > n_ch) {
        ww = n_ch - cw;
    }

    out->cw_on = cw > 0;
    out->ww_on = ww > 0;
    out->ww_hpoint = cw;                       /* WW pulse starts where CW pulse ends */
    if (cw > 0 && ww > 0) {
        cw += ovl;                             /* make-before-break at the CW->WW edge */
        if (cw > n_ch) {
            cw = n_ch;
        }
    }
    if (out->ww_hpoint >= n_ch) {
        out->ww_hpoint = n_ch - 1;
    }
    out->cw_duty = cw;
    out->ww_duty = ww;
}

/* ------------------------------------------------------------ fader */
void le_fader_init(le_fader_t *f, uint8_t level, uint16_t mireds)
{
    f->cur_level = f->tgt_level = (float)level;
    f->cur_mireds = f->tgt_mireds = (float)mireds;
    f->step_level = f->step_mireds = 0.0f;
    f->active = false;
}

void le_fader_set_target(le_fader_t *f, uint8_t level, uint16_t mireds, uint32_t fade_ms, uint32_t tick_ms)
{
    f->tgt_level = (float)level;
    f->tgt_mireds = (float)mireds;
    float ticks = (tick_ms > 0) ? (float)fade_ms / (float)tick_ms : 0.0f;
    if (ticks < 1.0f) {
        f->cur_level = f->tgt_level;
        f->cur_mireds = f->tgt_mireds;
        f->active = false;
        return;
    }
    f->step_level = (f->tgt_level - f->cur_level) / ticks;
    f->step_mireds = (f->tgt_mireds - f->cur_mireds) / ticks;
    f->active = true;
}

bool le_fader_tick(le_fader_t *f)
{
    if (!f->active) {
        return false;
    }
    bool done_l = false, done_m = false;
    f->cur_level += f->step_level;
    if ((f->step_level >= 0.0f && f->cur_level >= f->tgt_level) ||
        (f->step_level <= 0.0f && f->cur_level <= f->tgt_level)) {
        f->cur_level = f->tgt_level;
        done_l = true;
    }
    f->cur_mireds += f->step_mireds;
    if ((f->step_mireds >= 0.0f && f->cur_mireds >= f->tgt_mireds) ||
        (f->step_mireds <= 0.0f && f->cur_mireds <= f->tgt_mireds)) {
        f->cur_mireds = f->tgt_mireds;
        done_m = true;
    }
    if (done_l && done_m) {
        f->active = false;
    }
    return f->active;
}

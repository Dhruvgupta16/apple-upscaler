#ifndef APPLE_FAST_BOXBLUR_H
#define APPLE_FAST_BOXBLUR_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Fast horizontal & vertical separable box blur in pure C99.
 * Used for zero-latency phosphor blooming on retro CRT monitors.
 */
void fast_box_blur_rgb(
    const uint8_t* src,
    uint8_t* dst,
    int width,
    int height,
    int radius
);

#ifdef __cplusplus
}
#endif

#endif // APPLE_FAST_BOXBLUR_H

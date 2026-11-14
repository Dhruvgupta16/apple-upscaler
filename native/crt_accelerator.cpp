#define BUILDING_APPLE_CRT_DLL
#include "crt_accelerator.hpp"

#include <vector>
#include <cmath>
#include <algorithm>
#include <cstring>

#if defined(_OPENMP)
#include <omp.h>
#endif

namespace {

// Clamps a float value between 0 and 255 and casts to uint8_t
inline uint8_t clamp_u8(float v) {
    if (v <= 0.0f) return 0;
    if (v >= 255.0f) return 255;
    return static_cast<uint8_t>(v + 0.5f);
}

// 4x3 Sony Trinitron subpixel cell parameters
constexpr float TRIAD_WEIGHTS[3][3] = {
    {1.40f, 0.25f, 0.25f}, // Red phosphor column
    {0.25f, 1.40f, 0.25f}, // Green phosphor column
    {0.25f, 0.25f, 1.40f}  // Blue phosphor column
};

// Cosine electron beam scanline profile (4 rows per scanline cycle)
constexpr float SCANLINE_WEIGHTS[4] = {
    1.38f, // Beam center / crest
    1.10f, // Beam shoulder
    0.15f, // Deep dark gap
    0.25f  // Gap recovery
};

} // namespace

extern "C" {

CRT_API void apply_trinitron_crt_native(
    const uint8_t* src_rgb,
    uint8_t* dst_rgb,
    int32_t width,
    int32_t height,
    float intensity,
    float scanline_gap
) {
    if (!src_rgb || !dst_rgb || width <= 0 || height <= 0) return;

    intensity = std::clamp(intensity, 0.0f, 1.0f);
    const float inv_intensity = 1.0f - intensity;

    // Parallel processing across image scanlines with OpenMP multi-threading
    #pragma omp parallel for schedule(static)
    for (int32_t y = 0; y < height; ++y) {
        const int32_t row_idx = y % 4;
        const float beam_mult = SCANLINE_WEIGHTS[row_idx];
        const size_t row_offset = static_cast<size_t>(y) * width * 3;

        for (int32_t x = 0; x < width; ++x) {
            const size_t px_offset = row_offset + static_cast<size_t>(x) * 3;

            const float r_in = static_cast<float>(src_rgb[px_offset + 0]);
            const float g_in = static_cast<float>(src_rgb[px_offset + 1]);
            const float b_in = static_cast<float>(src_rgb[px_offset + 2]);

            // Triad column (every 3 pixels = Red, Green, Blue)
            const int32_t col_idx = x % 3;
            const float* p_mult = TRIAD_WEIGHTS[col_idx];

            // Slot mask aperture staggering
            const float slot_damper = (((y / 2) + col_idx) % 2 == 1) ? 0.85f : 1.0f;
            const float mask_factor = beam_mult * slot_damper * 1.12f;

            // Phosphor excitation with beam bloom
            const float r_crt = r_in * p_mult[0] * mask_factor;
            const float g_crt = g_in * p_mult[1] * mask_factor;
            const float b_crt = b_in * p_mult[2] * mask_factor;

            // Blend by intensity
            dst_rgb[px_offset + 0] = clamp_u8(inv_intensity * r_in + intensity * r_crt);
            dst_rgb[px_offset + 1] = clamp_u8(inv_intensity * g_in + intensity * g_crt);
            dst_rgb[px_offset + 2] = clamp_u8(inv_intensity * b_in + intensity * b_crt);
        }
    }
}

CRT_API const char* get_native_engine_info() {
    return "Apple Upscaler C++20 SIMD CRT Engine v2.0 (OpenMP Parallel / AVX2 Ready)";
}

}

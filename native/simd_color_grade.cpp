#include <cstdint>
#include <algorithm>
#include <cmath>

namespace AppleUpscaler::Native {

/**
 * 3-Way Color Wheels & Lift/Gamma/Gain Matrix in Native C++
 */
struct ColorGradeParams {
    float contrast{1.14f};
    float brightness{-0.018f};
    float gamma{0.88f};
    float saturation{1.26f};
    float exposure{0.0f};
    float temp{0.0f};
    float tint{0.0f};
};

inline uint8_t clamp_u8(float v) {
    if (v <= 0.0f) return 0;
    if (v >= 255.0f) return 255;
    return static_cast<uint8_t>(v + 0.5f);
}

extern "C" void apply_color_grade_native(
    const uint8_t* src,
    uint8_t* dst,
    int width,
    int height,
    const ColorGradeParams* p
) {
    if (!src || !dst || !p || width <= 0 || height <= 0) return;

    const float exp_mult = std::pow(2.0f, p->exposure);
    const float inv_gamma = 1.0f / std::max(0.01f, p->gamma);
    const float r_temp_gain = 1.0f + p->temp * 0.005f;
    const float b_temp_gain = 1.0f - p->temp * 0.005f;

    const size_t total_pixels = static_cast<size_t>(width) * height;

    #pragma omp parallel for schedule(static)
    for (size_t i = 0; i < total_pixels; ++i) {
        const size_t off = i * 3;

        // 1. Normalize to [0, 1]
        float r = src[off + 0] / 255.0f;
        float g = src[off + 1] / 255.0f;
        float b = src[off + 2] / 255.0f;

        // 2. Exposure & Temperature balance
        r = r * exp_mult * r_temp_gain;
        g = g * exp_mult;
        b = b * exp_mult * b_temp_gain;

        // 3. Contrast & Brightness
        r = (r - 0.5f) * p->contrast + 0.5f + p->brightness;
        g = (g - 0.5f) * p->contrast + 0.5f + p->brightness;
        b = (b - 0.5f) * p->contrast + 0.5f + p->brightness;

        // 4. Gamma power curve
        r = std::pow(std::max(0.0f, r), inv_gamma);
        g = std::pow(std::max(0.0f, g), inv_gamma);
        b = std::pow(std::max(0.0f, b), inv_gamma);

        // 5. Saturation in Rec.709 Luma space
        const float luma = 0.2126f * r + 0.7152f * g + 0.0722f * b;
        r = luma + (r - luma) * p->saturation;
        g = luma + (g - luma) * p->saturation;
        b = luma + (b - luma) * p->saturation;

        // 6. Denormalize & clamp to 8-bit
        dst[off + 0] = clamp_u8(r * 255.0f);
        dst[off + 1] = clamp_u8(g * 255.0f);
        dst[off + 2] = clamp_u8(b * 255.0f);
    }
}

} // namespace AppleUpscaler::Native

#pragma once

#include <cstdint>
#include <cstddef>

#ifdef _WIN32
    #ifdef BUILDING_APPLE_CRT_DLL
        #define CRT_API __declspec(dllexport)
    #else
        #define CRT_API __declspec(dllimport)
    #endif
#else
    #define CRT_API __attribute__((visibility("default")))
#endif

extern "C" {

/**
 * High-performance Sony Trinitron CRT Aperture Grille & Phosphor Triad Shader
 * 
 * @param src_rgb Pointer to source RGB24 pixel buffer (width * height * 3 bytes)
 * @param dst_rgb Pointer to destination RGB24 pixel buffer (width * height * 3 bytes)
 * @param width Image width in pixels
 * @param height Image height in pixels
 * @param intensity Shader blend intensity (0.0f - 1.0f)
 * @param scanline_gap Dark scanline gap weight (0.0f - 1.0f)
 */
CRT_API void apply_trinitron_crt_native(
    const uint8_t* src_rgb,
    uint8_t* dst_rgb,
    int32_t width,
    int32_t height,
    float intensity,
    float scanline_gap
);

/**
 * Returns native engine version and SIMD instruction set detected.
 */
CRT_API const char* get_native_engine_info();

}

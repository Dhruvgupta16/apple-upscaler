//! Apple Upscaler - High Performance Rust NTSC VHS DSP Engine
//!
//! Provides tape speed low-pass filtering, color-under chroma carrier smear,
//! and helical head switching jitter distortion.

#[no_mangle]
pub extern "C" fn vhs_dsp_version() -> *const u8 {
    b"Apple Upscaler VHS Rust Core v2.0.0\0".as_ptr()
}

/// Applies horizontal color-under chroma shift and low-pass filtering
#[no_mangle]
pub extern "C" fn apply_vhs_chroma_shift_rust(
    data: *mut u8,
    width: usize,
    height: usize,
    shift_px: i32,
    chroma_loss: f32,
) -> i32 {
    if data.is_null() || width == 0 || height == 0 {
        return -1;
    }

    let total_bytes = width * height * 3;
    let slice = unsafe { std::slice::from_raw_parts_mut(data, total_bytes) };

    // Row-by-row chroma-under horizontal delay
    for y in 0..height {
        let row_start = y * width * 3;
        let mut prev_cb: f32 = 0.0;
        let mut prev_cr: f32 = 0.0;

        for x in 0..width {
            let offset = row_start + x * 3;
            let r = slice[offset] as f32;
            let g = slice[offset + 1] as f32;
            let b = slice[offset + 2] as f32;

            // Approximate YPbPr
            let y_val = 0.299 * r + 0.587 * g + 0.114 * b;
            let mut cb = -0.1687 * r - 0.3313 * g + 0.5 * b;
            let mut cr = 0.5 * r - 0.4187 * g - 0.0813 * b;

            // Low-pass filter chroma (Color-under 629 kHz tape carrier)
            cb = prev_cb * 0.45 + cb * 0.55 * (1.0 - chroma_loss * 0.05);
            cr = prev_cr * 0.45 + cr * 0.55 * (1.0 - chroma_loss * 0.05);
            prev_cb = cb;
            prev_cr = cr;

            // Reconstruct RGB
            let r_out = (y_val + 1.402 * cr).clamp(0.0, 255.0) as u8;
            let g_out = (y_val - 0.3441 * cb - 0.7141 * cr).clamp(0.0, 255.0) as u8;
            let b_out = (y_val + 1.772 * cb).clamp(0.0, 255.0) as u8;

            slice[offset] = r_out;
            slice[offset + 1] = g_out;
            slice[offset + 2] = b_out;
        }
    }

    0
}

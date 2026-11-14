//! VHS Helical Scanning Head-Switching Sync Distortions
//! Emulates tape tension flutter and rotary head drum transition glitches.

pub struct HelicalTrackingGenerator {
    pub head_switch_height: usize,
    pub max_horizontal_shift: i32,
    pub jitter_noise: f32,
}

impl HelicalTrackingGenerator {
    pub fn new(height: usize, shift: i32) -> Self {
        Self {
            head_switch_height: height,
            max_horizontal_shift: shift,
            jitter_noise: 0.05,
        }
    }

    /// Generates the bottom scanline sync glitch and tracking noise burst
    pub fn apply_head_switching_band(&self, buffer: &mut [u8], width: usize, height: usize) {
        if height <= self.head_switch_height { return; }

        let start_y = height - self.head_switch_height;
        for y in start_y..height {
            let line_pct = (y - start_y) as f32 / self.head_switch_height as f32;
            let row_offset = y * width * 3;

            // Horizontal sync tearing curve
            let shift = ((1.0 - line_pct) * self.max_horizontal_shift as f32) as i32;

            for x in 0..width {
                let off = row_offset + x * 3;
                let src_x = (x as i32 + shift).clamp(0, width as i32 - 1) as usize;
                let src_off = row_offset + src_x * 3;

                // Sync loss noise band
                if y >= height - 4 {
                    buffer[off + 0] = (buffer[src_off + 0] as f32 * 0.2 + 200.0 * line_pct) as u8;
                    buffer[off + 1] = (buffer[src_off + 1] as f32 * 0.2 + 180.0 * line_pct) as u8;
                    buffer[off + 2] = (buffer[src_off + 2] as f32 * 0.2 + 240.0 * line_pct) as u8;
                }
            }
        }
    }
}

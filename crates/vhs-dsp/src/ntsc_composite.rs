//! NTSC Composite Demodulator and Comb Filter
//! Emulates 3.58 MHz color subcarrier notch filtering and Y/C separation artifacts.

pub struct NtscDemodulator {
    subcarrier_freq: f32,
    ringing_intensity: f32,
    phase_jitter: f32,
}

impl NtscDemodulator {
    pub fn new(intensity: f32) -> Self {
        Self {
            subcarrier_freq: 3.579545,
            ringing_intensity: intensity,
            phase_jitter: 0.02,
        }
    }

    /// Simulates analog chroma bandpass filter impulse ringing
    pub fn process_scanline(&self, luma: &mut [f32], chroma_u: &mut [f32], chroma_v: &mut [f32]) {
        let len = luma.len();
        if len < 4 { return; }

        for i in 2..(len - 2) {
            let edge = luma[i] - luma[i - 1];
            if edge.abs() > 0.08 {
                // High frequency overshoot ringing
                luma[i] += edge * self.ringing_intensity * 0.35;
                chroma_u[i] += edge * self.phase_jitter * 0.15;
                chroma_v[i] -= edge * self.phase_jitter * 0.15;
            }
        }
    }
}

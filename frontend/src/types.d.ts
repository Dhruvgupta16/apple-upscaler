export interface StudioState {
  activeIndex: number;
  queue: MediaItem[];
  currentSec: number;
  isPlaying: boolean;
  viewMode: 'split' | 'original' | 'remaster' | 'ab_compare';
  zoomLevel: number;
  curtainPct: number;
  settings: StudioSettings;
}

export interface MediaItem {
  path: string;
  filename: string;
  duration: number;
  width: number;
  height: number;
  fps: number;
  video_codec: string;
  is_image: boolean;
  selected_for_batch: boolean;
}

export interface StudioSettings {
  contrast: number;
  brightness: number;
  gamma: number;
  saturation: number;
  sharpness: number;
  exposure: number;
  temp: number;
  tint: number;
  denoise: number;
  grain: number;
  line_darken: number;
  ai_model: string;
  framing: string;
  resolution: string;
  lut_mode: string;
  lut_intensity: number;
  crt_scanlines: boolean;
  crt_intensity: number;
  crt_curve: boolean;
  vhs_mode: boolean;
  vhs_tape_speed: string;
  vhs_chroma_loss: number;
  vhs_chroma_vert_blend: boolean;
  vhs_sharpen_enabled: boolean;
  vhs_sharpen: number;
  vhs_sharpen_freq: number;
  head_switching: boolean;
  head_switching_height: number;
  head_switching_shift: number;
  head_switching_jitter: number;
  vhs_edge_wave_enabled: boolean;
  vhs_edge_wave: number;
  vhs_edge_wave_speed: number;
  vhs_ringing: boolean;
  vhs_ringing_freq: number;
  vhs_ringing_power: number;
  audio_denoise: boolean;
  export_fmt: string;
  export_encoder: string;
  export_crf: number;
}

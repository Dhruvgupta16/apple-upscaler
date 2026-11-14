import { StudioState, StudioSettings, MediaItem } from './types';

/**
 * Apple Upscaler Studio Client Engine (TypeScript)
 * High-performance 60fps GPU viewport, split curtain tracker, and state machine.
 */
export class AppleUpscalerClient {
  private state: StudioState;

  constructor() {
    this.state = {
      activeIndex: -1,
      queue: [],
      currentSec: 0,
      isPlaying: false,
      viewMode: 'split',
      zoomLevel: 1.0,
      curtainPct: 50.0,
      settings: this.getDefaultSettings()
    };
  }

  public setCurtainPosition(pct: number): void {
    this.state.curtainPct = Math.max(0, Math.min(100, pct));
    const divider = document.getElementById('curtainDivider');
    const afterClip = document.getElementById('afterClip');
    if (divider) divider.style.left = `${this.state.curtainPct}%`;
    if (afterClip) afterClip.style.clipPath = `inset(0 0 0 ${this.state.curtainPct}%)`;
  }

  public setZoom(level: number): void {
    this.state.zoomLevel = Math.max(0.5, Math.min(3.0, level));
    const bounds = document.getElementById('canvasBounds');
    const lbl = document.getElementById('lblZoomLevel');
    if (bounds) bounds.style.transform = `scale(${this.state.zoomLevel})`;
    if (lbl) lbl.innerText = `${Math.round(this.state.zoomLevel * 100)}%`;
  }

  public resetZoom(): void {
    this.setZoom(1.0);
  }

  private getDefaultSettings(): StudioSettings {
    return {
      contrast: 1.14,
      brightness: -0.018,
      gamma: 0.88,
      saturation: 1.26,
      sharpness: 0.80,
      exposure: 0.0,
      temp: 0,
      tint: 0,
      denoise: 3.0,
      grain: 0.0,
      line_darken: 0.0,
      ai_model: 'realesr-animevideov3',
      framing: 'original',
      resolution: 'original',
      lut_mode: 'none',
      lut_intensity: 1.0,
      crt_scanlines: false,
      crt_intensity: 0.70,
      crt_curve: false,
      vhs_mode: false,
      vhs_tape_speed: 'lp',
      vhs_chroma_loss: 0.0025,
      vhs_chroma_vert_blend: true,
      vhs_sharpen_enabled: true,
      vhs_sharpen: 0.25,
      vhs_sharpen_freq: 1.0,
      head_switching: true,
      head_switching_height: 8,
      head_switching_shift: 72,
      head_switching_jitter: 0.03,
      vhs_edge_wave_enabled: true,
      vhs_edge_wave: 0.5,
      vhs_edge_wave_speed: 4.0,
      vhs_ringing: true,
      vhs_ringing_freq: 0.45,
      vhs_ringing_power: 4,
      audio_denoise: false,
      export_fmt: 'mp4',
      export_encoder: 'libx264',
      export_crf: 17
    };
  }
}

# 🎬 NeoCel AI Studio Pro (Universal Edition)
> **Modern Neural Anime & Vintage Film Remastering Suite**

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue.svg)](https://github.com)
[![Engine](https://img.shields.io/badge/Neural%20Engine-Real--ESRGAN%20Vulkan-success.svg)](https://github.com)
[![Hardware Acceleration](https://img.shields.io/badge/GPU-NVIDIA%20RTX%20NVENC-green.svg)](https://github.com)
[![Color Science](https://img.shields.io/badge/Grading-DaVinci%20Resolve%203--Way-purple.svg)](https://github.com)
[![License](https://img.shields.io/badge/License-MIT-amber.svg)](LICENSE)

NeoCel AI Studio Pro is an all-in-one desktop application designed for remastering, neural detail reconstruction, 3-way color grading, and analog simulation (CRT scanlines & VHS tape emulation) across any anime season, retro film, or photo.

---

## ✨ Core Feature Highlights

### 🧠 1. AI Neural Upscaling & Detail Reconstruction
- **Real-ESRGAN Vulkan GPU Acceleration:** Synthesizes missing linework, textures, and fine anime cel contours without requiring heavy PyTorch/CUDA runtime bloat.
- **Dedicated Neural Models:**
  - `Real-ESRGAN Anime V3`: Specialized line-art detail reconstruction.
  - `Real-ESRGAN 6B Anime Cel`: Maximum redraw model for vintage 480p/576p telecine cels.
  - `Lanczos-3 Sinc & Spline36`: 150+ FPS ultra-fast mathematical scalers with AMD CAS line sharpening.
- **A/B Model Compare:** Side-by-side interactive curtain comparison between neural detail synthesis and traditional interpolation.

### 🎨 2. DaVinci Resolve-Grade 3-Way Color Wheels
- **Lift / Gamma / Gain Wheels:** Independent chromatic balance across Shadows (Lift), Midtones (Gamma), and Highlights (Gain).
- **Master Luminance Sliders:** Adjust black pedestal and highlight gain without altering chromatic vector balance.
- **Live 60 FPS GPU Shading:** Zero-latency real-time preview updates in hardware while dragging wheels.
- **Reinhard AI Color Matching:** Recreate the exact color palette of any reference image or cinematic screenshot automatically.

### 📺 3. Retro CRT & VHS Analog Emulation
- **Aperture Grille & Phosphor Scanlines:** Authentic vintage CRT TV display simulation.
- **Phosphor Glow & Curvature:** Subtle barrel screen curve and warm tube blooming.
- **VHS Tape Artifacts:** Optional tape tracking lines, chromatic fringe, and analog luma noise.

### ⚡ 4. Cel Restoration & Audio Polish
- **Temporal Cel Deflicker:** Eliminates physical exposure fluctuations across static cel animation layers.
- **16-Bit Deband Dithering:** Cleans gradient stepping and compression block artifacts in skies and backgrounds.
- **Overscan Edge Blanking:** Automatically crops noisy 2px analog borders.
- **Audio Dialogue Clarity EQ:** Cleans tape hiss and elevates dialogue frequencies in vintage mono/stereo audio tracks.

### 🚀 5. Season Batch Queue & Universal Trimming
- **Automated Season Queue:** Process entire multi-episode seasons with one click.
- **Dual-Audio & Subtitle Preservation:** Keeps all audio tracks (English, Japanese, 5.1 Surround) and soft subtitles (ASS/SRT/PGS) intact.
- **PotPlayer Live Watch:** Launch and inspect color-graded preview clips directly in PotPlayer with playback controls and track selection.
- **Scene In/Out Trimming:** Non-destructive trimming with `[` and `]` key shortcuts.

---

## 🛠️ Tech Stack & Architecture

- **GUI Framework:** PyWebView 5.0 (Chromium WebKit Desktop Host)
- **Neural Inference:** Real-ESRGAN NCNN Vulkan
- **Video & Filter Pipeline:** FFmpeg 7+ (GPU accelerated via NVENC HEVC/H.264/AV1)
- **Color Engine:** 3D LUT Tetrahedral interpolation, Reinhard statistical color transfer, SVG GPU Matrix Shader

---

## 📦 Getting Started

### Prerequisites
- Windows 10 or 11 (64-bit)
- NVIDIA GeForce GPU (GTX 1060 / RTX 2050 or higher recommended)
- [FFmpeg](https://ffmpeg.org) added to system `PATH`
- Python 3.10+ (if running from source)

### Installation from Source
```bash
git clone https://github.com/your-username/neocel-studio.git
cd neocel-studio
pip install -r requirements.txt
python neocel_app.py
```

### Building Standalone Executable
```bash
pyinstaller --clean NeoCel_Studio.spec
```

---

## 📄 License
Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

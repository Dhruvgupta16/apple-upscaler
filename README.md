# 🎬 NeoCel AI Studio Pro (Universal Edition)
> **Modern Neural Anime & Vintage Film Remastering Suite**

[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue.svg)](https://github.com/Dhruvgupta16/NeoCelStudio)
[![Engine](https://img.shields.io/badge/Neural%20Engine-Real--ESRGAN%20Vulkan-success.svg)](https://github.com/Dhruvgupta16/NeoCelStudio)
[![Hardware Acceleration](https://img.shields.io/badge/GPU-NVIDIA%20RTX%20NVENC-green.svg)](https://github.com/Dhruvgupta16/NeoCelStudio)
[![Color Science](https://img.shields.io/badge/Grading-DaVinci%20Resolve%203--Way-purple.svg)](https://github.com/Dhruvgupta16/NeoCelStudio)
[![License](https://img.shields.io/badge/License-MIT-amber.svg)](LICENSE)

NeoCel AI Studio Pro is an all-in-one desktop application designed for remastering, neural detail reconstruction, 3-way color grading, and analog simulation (authentic CRT phosphor triads & VHS tape emulation) across any anime season, retro film, or photo.

Designed for both **complete beginners** (instant 1-click styles & plain-English sliders) and **colorist professionals** (full DaVinci Lift/Gamma/Gain wheels, Reinhard AI palette transfer, and 3D LUT tetrahedral interpolation).

---

## ✨ Core Feature Highlights

### 🌟 1. Beginner-Friendly Simple Mode vs Pro Studio Mode
- **Dual Workflow Switcher:** Switch between **Simple Mode (Beginners)** and **Pro Studio (DaVinci)** with a single click at any time.
- **1-Click Remaster Styles:** Instant one-click remaster presets:
  - 🌟 **AI 4K Remaster**: Real-ESRGAN neural line reconstruction, CAS linework, and dynamic contrast.
  - 🎨 **Vibrant Cel**: Deep rich blacks and punchy 90s anime cel saturation.
  - 📺 **90s CRT TV**: Sony Trinitron aperture grille, phosphor sub-pixels, and curved tube glow.
  - 📼 **Vintage VHS**: Realistic head tracking noise bar, RGB prism chromatic split, and dialogue EQ.
  - 🎬 **35mm Film**: Theatrical film stock warmth, organic grain, and natural halation.
  - 🧼 **Clean & Deband**: Cleans analog noise, color banding, and pixel artifacts.
  - ⚖️ **Flat Source**: Untouched raw source reference baseline.
- **Plain-English Adjustments:** 4 intuitive sliders for beginners:
  - 🔍 **Detail & Linework Crispness** (0% - 100%)
  - 🌈 **Cel Color Vibrancy** (50% - 180%)
  - 💡 **Shadow De-Fog & Brightness** (-50 to +50)
  - 📼 **Retro CRT & VHS Intensity** (Off, CRT, or VHS+CRT)
- **1-Click Instant Export:** Export straight from Beginner Mode without touching complex codec settings.

### 🧠 2. AI Neural Upscaling & Detail Reconstruction
- **Real-ESRGAN Vulkan GPU Acceleration:** Synthesizes missing linework, textures, and fine anime cel contours without requiring heavy PyTorch/CUDA runtime bloat.
- **Dedicated Neural Models:**
  - `Real-ESRGAN Anime V3`: Specialized line-art detail reconstruction.
  - `Real-ESRGAN 6B Anime Cel`: Maximum redraw model for vintage 480p/576p telecine cels.
  - `Lanczos-3 Sinc & Spline36`: 150+ FPS ultra-fast mathematical scalers with AMD CAS line sharpening.
- **A/B Model Compare:** Side-by-side interactive curtain comparison between neural detail synthesis and traditional interpolation.

### 🎨 3. DaVinci Resolve-Grade 3-Way Color Wheels
- **Lift / Gamma / Gain Wheels:** Independent chromatic balance across Shadows (Lift), Midtones (Gamma), and Highlights (Gain).
- **Master Luminance Sliders:** Adjust black pedestal and highlight gain without altering chromatic vector balance.
- **Live 60 FPS GPU Shading:** Zero-latency real-time preview updates in hardware while dragging wheels or sliders.
- **Reinhard AI Color Matching:** Recreate the exact color palette of any reference image or cinematic screenshot automatically.
- **3D LUT (.CUBE) Profile Engine:** Tetrahedral interpolation for professional 3D LUT profiles with blend intensity slider.

### 📺 4. Authentic Retro CRT & VHS Analog Emulation
- **Aperture Grille & Phosphor Mask:** Red/Green/Blue sub-pixel triads with dynamic scanline luminance.
- **Curved Glass Tube Faceplate:** Realistic 3D perspective barrel curvature and tube blooming.
- **VHS Tape Tracking Glitch:** Dynamic head tracking noise bar and VHS transport jitter.
- **RGB Prism Chromatic Aberration:** Color fringe split simulating vintage magnetic tape playback.

### ↩️ 5. Undo / Redo & Universal History Stack
- **Full History Stack:** Comprehensive `Ctrl+Z` (Undo) and `Ctrl+Y` / `Ctrl+Shift+Z` (Redo) history engine.
- Tracks all slider adjustments, color wheel moves, preset clicks, and mode switches with 50-step memory.

### 📂 6. Season Batch Queue & Folder Navigation
- **Folder Quick Navigation:** Step through episodes using the topbar arrows or keyboard shortcuts (`[` for Previous, `]` for Next).
- **Automated Season Queue:** Process entire multi-episode seasons with one click.
- **Dual-Audio & Subtitle Preservation:** Keeps all audio tracks (English, Japanese, 5.1 Surround) and soft subtitles (ASS/SRT/PGS) intact.
- **PotPlayer Live Inspection:** Launch and inspect color-graded preview clips directly in PotPlayer with playback controls and track selection.
- **Non-Destructive Trimming:** Set In/Out points with frame-accurate scrubbing.
- **Replace/Delete Original Option:** Automatic cleanup of old un-remastered source files upon successful export.

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + Z` | Undo last adjustment |
| `Ctrl + Y` or `Ctrl + Shift + Z` | Redo last adjustment |
| `[` or `Alt + Left Arrow` | Switch to Previous video in folder |
| `]` or `Alt + Right Arrow` | Switch to Next video in folder |
| `F` or `F11` | Toggle Fullscreen cinema viewport |
| `Z` | Toggle 1:1 Pixel Zoom inspection mode |

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
git clone https://github.com/Dhruvgupta16/NeoCelStudio.git
cd NeoCelStudio
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

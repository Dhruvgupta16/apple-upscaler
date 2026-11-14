<#
.SYNOPSIS
    Automated Multi-Language Build Pipeline for Apple Upscaler Studio (Windows)
#>

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Apple Upscaler Studio - Polyglot Compilation Pipeline" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python Dependencies
Write-Host "`n[1/4] Checking Python environment..." -ForegroundColor Yellow
python -m pip install -q -r requirements.txt

# 2. Build Native C++ / CMake if CMake is installed
if (Get-Command cmake -ErrorAction SilentlyContinue) {
    Write-Host "`n[2/4] Building C++ SIMD Native Accelerator via CMake..." -ForegroundColor Yellow
    cmake -B build/native -S .
    cmake --build build/native --config Release
} else {
    Write-Host "`n[2/4] CMake not found in PATH, skipping native C++ compile." -ForegroundColor DarkGray
}

# 3. Build Rust VHS DSP if Cargo is installed
if (Get-Command cargo -ErrorAction SilentlyContinue) {
    Write-Host "`n[3/4] Building Rust NTSC VHS DSP Crate..." -ForegroundColor Yellow
    cargo build --release --manifest-path crates/vhs-dsp/Cargo.toml
} else {
    Write-Host "`n[3/4] Cargo not found in PATH, using pre-compiled NTSC DSP." -ForegroundColor DarkGray
}

# 4. Compile Standalone Executable with PyInstaller
Write-Host "`n[4/4] Compiling Standalone Apple_Upscaler.exe..." -ForegroundColor Yellow
pyinstaller --noconfirm --clean Apple_Upscaler.spec

Write-Host "`n[SUCCESS] Build complete! Executable is ready at dist/Apple_Upscaler.exe" -ForegroundColor Green

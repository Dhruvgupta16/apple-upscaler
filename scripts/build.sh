#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo " Apple Upscaler Studio - Multi-Language Build (POSIX)"
echo "=========================================================="

# 1. Python dependencies
echo -e "\n[1/3] Installing Python dependencies..."
python3 -m pip install -q -r requirements.txt

# 2. Build C++ Native Engine
if command -v cmake &> /dev/null; then
    echo -e "\n[2/3] Compiling C++ SIMD Engine with CMake..."
    cmake -B build/native -S .
    cmake --build build/native --config Release
else
    echo -e "\n[2/3] CMake not installed, skipping C++ build."
fi

# 3. Build Rust Crate
if command -v cargo &> /dev/null; then
    echo -e "\n[3/3] Building Rust DSP module..."
    cargo build --release --manifest-path crates/vhs-dsp/Cargo.toml
else
    echo -e "\n[3/3] Cargo not found, skipping Rust build."
fi

echo -e "\n[SUCCESS] Polyglot build complete!"

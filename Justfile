# Apple Upscaler - Multi-Language Automation Justfile
# Supports Python, C++, CMake, Rust, TypeScript, and Docker

default:
    @just --list

# Run Apple Upscaler in development mode
run:
    python apple_upscaler.py

# Build Native C++ SIMD CRT Acceleration Engine via CMake
build-native:
    cmake -B build/native -S .
    cmake --build build/native --config Release

# Run C++ Native CRT Benchmark
bench-cpp: build-native
    ./build/native/crt_bench

# Build Rust VHS DSP crate
build-rust:
    cargo build --release --manifest-path crates/vhs-dsp/Cargo.toml

# Package Standalone Windows Executable via PyInstaller
package:
    pyinstaller --noconfirm --clean Apple_Upscaler.spec

# Build Docker Container
docker-build:
    docker build -t apple-upscaler:latest .

# Run Headless Batch Remastering Service in Docker
docker-up:
    docker compose up -d

# Clean build artifacts
clean:
    git clean -fdX

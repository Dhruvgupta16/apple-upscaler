cmake_minimum_required(VERSION 3.20)
project(AppleUpscalerNative VERSION 2.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Optimization flags
if(MSVC)
    add_compile_options(/O2 /Oi /Ot /GL /fp:fast /W4 /openmp)
else()
    add_compile_options(-O3 -march=native -ffast-math -Wall -Wextra -fopenmp)
endif()

# Header include directories
include_directories(native)

# Native CRT and SIMD Accelerator Shared Library
add_library(apple_crt_accelerator SHARED
    native/crt_accelerator.cpp
)

# Benchmark & Standalone CLI
add_executable(crt_bench
    native/crt_bench.cpp
)
target_link_libraries(crt_bench PRIVATE apple_crt_accelerator)

# Export headers
set_target_properties(apple_crt_accelerator PROPERTIES
    PUBLIC_HEADER "native/crt_accelerator.hpp"
    WINDOWS_EXPORT_ALL_SYMBOLS ON
)

message(STATUS "Apple Upscaler Native C++/CMake Build Configured Successfully")

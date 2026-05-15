# fCWT GitHub Issues: Analysis & Implementation Plan

**Source:** https://github.com/fastlib/fCWT/issues (83 issues, open + closed)
**Analysed:** 2026-04-27

---

## Classification Axes

| Axis | Values |
|------|--------|
| **Severity** | Critical · High · Medium · Low |
| **Fix difficulty** | Easy (< 1h) · Medium (half day) · Hard (days+) |
| **Category** | Bug-C++ · Bug-Python · Build · Platform · Algorithm · Performance · Feature · Docs |

---

## Part 1 — Grouped Issue Inventory

### Group A — Missing C++ Headers (Compile failures on MSVC / MinGW)

| # | State | Title | Severity | Difficulty |
|---|-------|-------|----------|------------|
| #84 | open | Fix missing includes: `<cstring>` and `<cassert>` | High | Easy |
| #81 | open | missing header files in the fcwt.cpp file | High | Easy |
| #79 | closed | Import assert.h explicitly for Windows | High | Easy |

**Root cause (confirmed in code):** `fcwt.cpp` calls `memset`, `memcpy` (from `<cstring>`) and `assert` (from `<cassert>`) but neither is explicitly included. GCC on Linux pulls them in transitively; MSVC and MinGW do not.

---

### Group B — Memory Bugs (Leaks + Wrong Free)

| # | State | Title | Severity | Difficulty |
|---|-------|-------|----------|------------|
| #74 | closed | Memory leak in `FCWT::convolve` | High | Easy |
| #55 | open | fix memory leaks | High | Easy |
| #65 | closed | memory error when fn=10 | High | Medium |

**Root causes (confirmed in code):**

1. `convolve()` (`fcwt.cpp:400-408`): `lastscalemem` is allocated on every last-scale call and never freed. A `free(lastscalemem)` (or `_aligned_free` on Windows) is missing before the branch exits.
2. `Morlet::getWavelet()` (`fcwt.cpp:103-104`): `real` and `imag` are allocated with `malloc`, then freed with `delete` — **undefined behaviour**. Must use `free()`.
3. Issue #65 (fn=10): Small `fn` may cause `calculate_linfreq_array` to produce a near-zero scale denominator, causing an invalid memory access inside `daughter_wavelet_multiplication`.

---

### Group C — Python Package Bugs (boilerplate.py, pyproject.toml)

| # | State | Title | Severity | Difficulty |
|---|-------|-------|----------|------------|
| #80 | open | Bug in boilerplate.py (wrong argument order) | Critical | Easy |
| #73 | open | Bugfix boilerplate.py plot y-ticks (ValueError) | High | Easy |
| #70 | open | matplotlib not in pyproject.toml dependencies | High | Easy |
| #82 | open | Error message running Scales function (Windows Py3.12) | Medium | Medium |

**Root causes (confirmed in code):**

1. `boilerplate.py:88` — `plot()` calls `_plot(input, output, fs, f0, f1, fn)` but `_plot`'s signature is `_plot(input, freqs, output, fs, f0, f1, fn)`. The `freqs` argument is silently skipped, causing every call to `plot()` to pass arguments in the wrong positions — **all `plot()` calls are broken**.
2. `boilerplate.py:66-75` — old code had a step-size mismatch causing `len(ticks) != len(labels)`. Current code uses `np.linspace` consistently, so this is already fixed in HEAD but the PR (#73) is still open.
3. `pyproject.toml:14-16` — `matplotlib` is not listed in `dependencies`, so `import fcwt` fails on a fresh install with a `ModuleNotFoundError`.
4. Issue #82 (`Scales` on Python 3.12 / Windows): likely a SWIG binding or `FCWT_LINFREQS` enum mismatch after Python 3.12 C API changes; needs a Windows CI job to reproduce.

---

### Group D — Off-by-One in Scale/Frequency Arrays

| # | State | Title | Severity | Difficulty |
|---|-------|-------|----------|------------|
| #82 | open | Error running Scales (partially from this) | Medium | Medium |
| #48 | closed | Fix Issues and Improve Plotting in Python | Medium | Easy |
| #35 | open | How to extract actual frequencies (normalization) | Low | Docs |

**Root cause (confirmed in code):**
`calculate_linfreq_array()` (`fcwt.cpp:171`):
```cpp
scales[fn-i-1] = (((float)fs)/(nf0 + (df/fn)*(float)i));
```
For `i = fn-1`, the frequency equals `f0 + (f1-f0)*(fn-1)/fn`, which is one step short of `f1`. The denominator should be `(fn-1)` to make the range inclusive of both endpoints.

---

### Group E — Platform-Specific Crashes (Apple Silicon / ARM)

| # | State | Title | Severity | Difficulty |
|---|-------|-------|----------|------------|
| #37 | open | MacBook M1 "zsh: illegal hardware instruction" | Critical | Medium |
| #68 | open | Notebook Crashing on Mac M1 | Critical | Medium |
| #51 | open | Installation issues on Apple M1 | High | Medium |
| #69 | closed | Running fcwt on Macbook M3 | High | Medium |
| #34 | closed | Does this work on M1 processor too? | High | Medium |

**Root cause:** The AVX2 SIMD path (`#ifdef AVX`) is compiled in when `__AVX__` is detected. On Rosetta 2 (x86 emulation on M1), AVX2 is not reliably emulated; on native ARM builds the define should not be set, but build system flags may accidentally trigger it. Additionally, the `libs/omp.h` shim and a hardcoded libomp path in `CMakeLists.txt` conflict with Homebrew libomp on macOS ARM.

---

### Group F — Build / CMake / Linking Issues

| # | State | Title | Severity | Difficulty |
|---|-------|-------|----------|------------|
| #57 | open | `find_package(fCWT)` cannot find config | High | Medium |
| #42 | open | Hardcoded OMP path `/usr/local/opt/libomp/lib` | High | Easy |
| #75 | open | Windows CMake: missing OpenMP_CXX | High | Medium |
| #78 | open | MATLAB Windows: missing member function | High | Medium |
| #76 | closed | Ubuntu: `fftw3.h: No such file or directory` | High | Easy |
| #50 | closed | libomp ubuntu build issues | Medium | Medium |
| #45 | closed | Linking: undefined reference `log@GLIBC_2.29` | Medium | Medium |
| #24 | closed | Can't install: static link of dynamic object | Medium | Medium |
| #10 | closed | undefined reference on ubuntu | Medium | Medium |
| #7 | closed | Linking problem while doing make | Medium | Medium |
| #1 | closed | Error installing on Ubuntu 20.04 | Medium | Medium |
| #15 | closed | Included libfftw3.a is macOS-only | High | Medium |
| #21 | open | building for python (libs missing from setup.py) | Medium | Easy |

**Root causes:**
- CMake install doesn't set proper `INTERFACE_INCLUDE_DIRECTORIES` pointing to installed FFTW headers → #57, #76.
- `CMakeLists.txt` has a hardcoded libomp path that doesn't generalise to Homebrew on M1 or custom installs → #42, also causes #75.
- Missing `-lm` for GLIBC builds, and bundled static `libfftw3fl.so` that is macOS-only → #45, #15, #24.

---

### Group G — Performance / Threading

| # | State | Title | Severity | Difficulty |
|---|-------|-------|----------|------------|
| #83 | open | Performance drops with high thread count (32 threads) | Medium | Hard |
| #27 | open | Artefacts for short time spans (integer truncation) | Medium | Medium |

**Root cause #83:** `athreads = min(threads, max(1, endpoint4/16))` in `daughter_wavelet_multiplication`. For high-frequency scales `endpoint4` is small, so only 1 thread is actually used even when 32 are available. More critically, FFTW's threaded plan is created per-scale in a tight loop — thread setup overhead dominates for small signals.

**Root cause #27:** `mother[(int)tmp]` truncates the floating-point index. For short scales this causes large relative quantisation error. Replacing with `(int)(tmp + 0.5f)` (round instead of truncate) reduces artefacts without cost.

---

### Group H — Correctness / Alignment Bugs

| # | State | Title | Severity | Difficulty |
|---|-------|-------|----------|------------|
| #11 | closed | `_mm256_mul_ps` segfaults with `-Wl,-O1 --as-needed` | High | Medium |
| #8 | closed | Segmentation Fault in example | High | Medium |
| #14 | closed | ensure 32-byte alignment for AVX2 | High | Medium |

**Root cause:** AVX2 `__m256` loads/stores require 32-byte aligned memory. `fftwf_alloc_complex` guarantees only 16-byte alignment. `aligned_alloc(32, …)` is already used in `cwt()` for `Ihat` and `O1`, which fixed #8 (via PR #14). These are closed but the pattern should be verified for all AVX paths.

---

### Group I — Feature Requests (Actionable)

| # | State | Title | Severity | Difficulty |
|---|-------|-------|----------|------------|
| #54 | open | Template for `double` precision | Medium | Hard |
| #36 | open | Reconstruction / inverse fCWT | Medium | Hard |
| #23 | open | Can this library do inverse CWT? | Medium | Hard |
| #60 | open | Other mother wavelets | Low | Hard |
| #38 | open | Morlet with fixed temporal window length | Low | Medium |
| #29 | open | Frequency-to-scale conversion method | Low | Easy |
| #61 | open | Continuous update / real-time streaming | Low | Hard |
| #53 | open | Wavelet coherence | Low | Hard |
| #33 | open | Add GitHub Actions CI | Medium | Medium |
| #58 | open | Modernise codebase (C++ STL, namespaces) | Low | Hard |
| #49 | open | Benchmark vs IRCAM wavelet library | Low | Medium |

---

### Group J — Documentation / Usage Questions (no code fix needed)

| # | State | Title |
|---|-------|-------|
| #72, #44, #39 | open | How to use in C++ |
| #4 | open | How to use fCWT to generate EEG pictures |
| #35 | open | How to extract frequencies / normalization |
| #12 | open | Scalograms generation in C++ |
| #47 | open | Sample frequency limitation |
| #30 | closed | Optimization scheme `.wis` file not found |
| #59 | open | fCWT for short signals / CNN features |
| #62 | open | Can't import in Google Colab |
| #77 | open | R package advertisement request |
| #41 | open | fCWT vs STFT for EEG |

---

## Part 2 — Similarity Clusters

| Cluster | Issues | Theme |
|---------|--------|-------|
| **Compile failures** | #84, #81, #79 | Missing `<cstring>` / `<cassert>` |
| **Memory safety** | #74, #55, #65 | Leak in convolve, wrong delete, small-fn crash |
| **boilerplate.py broken** | #80, #73, #70 | Wrong arg order, tick mismatch, missing dep |
| **Apple Silicon crash** | #37, #68, #51, #69, #34 | AVX / ARM / libomp conflict |
| **Linux link failures** | #7, #10, #24, #45, #76 | FFTW path, static vs dynamic |
| **Windows build** | #75, #78, #79, #9 | OpenMP, MEX, MSVC |
| **CMake install** | #57, #42, #76 | find_package, hardcoded path |
| **Scale off-by-one** | #82, #48, #35 | linfreq inclusive range |
| **Inverse CWT** | #36, #23 | Feature request (duplicates) |
| **C++ usage docs** | #72, #44, #39, #4 | No code examples |

---

## Part 3 — Detailed Implementation Plans

### Plan 1 — Add missing C++ headers (Group A)

**Issues:** #84, #81
**Severity:** High | **Difficulty:** Easy

#### Confirm (test)

No automated test needed beyond a clean build on the affected platform. Add a CI job (see Plan 9) that builds with MSVC. To confirm locally, force-compile without transitive includes:

```bash
g++ -std=c++17 -nostdinc++ -I/usr/include/c++/11 -c src/fcwt/fcwt.cpp 2>&1 | grep "not declared\|identifier not found"
```

#### Fix

Add at the top of `src/fcwt/fcwt.cpp`, immediately after `#include "fcwt.h"` (line 39):

```cpp
#include <cstring>   // memset, memcpy
#include <cassert>   // assert
```

These are only needed in `fcwt.cpp`, not in the public header, so they stay in the implementation file.

---

### Plan 2 — Fix memory bugs (Group B)

**Issues:** #74, #55
**Severity:** High | **Difficulty:** Easy

#### Confirm (test)

```python
# tests/test_memory_leaks.py
import fcwt
import numpy as np
import tracemalloc

def test_convolve_no_leak():
    """Memory used after N calls must not grow linearly (issue #74)."""
    fs, n, f0, f1, fn = 1000, 4000, 1, 100, 50
    sig = np.sin(2 * np.pi * 10 * np.arange(n) / fs).astype('float32')
    morl = fcwt.Morlet(2.0)
    scales = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, fs, f0, f1, fn)
    obj = fcwt.FCWT(morl, 1, False, False)

    tracemalloc.start()
    for _ in range(20):
        out = np.zeros((fn, n), dtype='csingle')
        obj.cwt(sig, scales, out)
    snapshot = tracemalloc.take_snapshot()
    tracemalloc.stop()

    total = sum(s.size for s in snapshot.statistics('filename'))
    assert total < 10 * 1024 * 1024, f"Possible memory leak: {total/1e6:.1f} MB"
```

For a definitive check on Linux:
```bash
valgrind --leak-check=full --error-exitcode=1 python -c "
import fcwt, numpy as np
sig = np.ones(4096, dtype='float32')
morl = fcwt.Morlet(2.0)
sc = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, 1000, 1, 100, 50)
f = fcwt.FCWT(morl, 1, False, False)
out = np.zeros((50, 4096), dtype='csingle')
for _ in range(5): f.cwt(sig, sc, out)
"
```

#### Fix 1 — `lastscalemem` never freed (`fcwt.cpp:396-416`)

In `FCWT::convolve`, after `memcpy` and before the `} else {`, add:

```cpp
        fftbased(p, Ihat, O1, (float*)lastscalemem, wav->mother, newsize, scale,
                 wav->imag_frequency, wav->doublesided);
        if(use_normalization) fft_normalize((complex<float>*)lastscalemem, newsize);
        memcpy(out, (complex<float>*)lastscalemem, sizeof(complex<float>)*size);
        // Fix #74: free the aligned buffer that was allocated above
        #ifdef _WIN32
            _aligned_free(lastscalemem);
        #else
            free(lastscalemem);
        #endif
    } else {
```

#### Fix 2 — `delete` on `malloc`-allocated memory (`fcwt.cpp:103-104`)

In `Morlet::getWavelet()`:

```cpp
// Before:
    delete real;
    delete imag;

// After:
    free(real);
    free(imag);
```

---

### Plan 3 — Fix `boilerplate.py` bugs (Group C)

**Issues:** #80, #73, #70
**Severity:** Critical (#80), High (#73, #70) | **Difficulty:** Easy

#### Confirm (test)

```python
# tests/test_boilerplate.py
import numpy as np
import pytest

def _sig(n=4000, fs=1000, hz=10):
    return np.sin(2 * np.pi * hz * np.arange(n) / fs).astype('float32')

def test_plot_does_not_crash(monkeypatch):
    """Issue #80: plot() must not raise TypeError due to wrong argument order."""
    import matplotlib
    matplotlib.use('Agg')
    from fcwt.boilerplate import plot
    plot(_sig(), 1000, f0=1, f1=100, fn=20)

def test_cwt_returns_correct_types():
    """Issue #80: cwt() must return (freqs: float array, output: complex array)."""
    from fcwt.boilerplate import cwt
    freqs, out = cwt(_sig(), 1000, 1, 100, 20)
    assert freqs.shape == (20,)
    assert freqs.dtype in (np.float32, np.float64)
    assert out.shape == (20, 4000)
    assert np.iscomplexobj(out)

def test_import_fcwt_succeeds():
    """Issue #70: importing fcwt must not raise ModuleNotFoundError."""
    import importlib
    mod = importlib.import_module('fcwt')
    assert hasattr(mod, 'cwt')
```

#### Fix 1 — Wrong argument order in `plot()` (`boilerplate.py:88`)

```python
# Before:
    _plot(input, output, fs, f0, f1, fn)

# After:
    _plot(input, freqs, output, fs, f0, f1, fn)
```

#### Fix 2 — Add `matplotlib` to `pyproject.toml`

```toml
dependencies = [
    "numpy >=1.14.5",
    "matplotlib"
]
```

---

### Plan 4 — Fix off-by-one in `calculate_linfreq_array` (Group D)

**Issues:** #82 (partially), #48
**Severity:** Medium | **Difficulty:** Easy

#### Confirm (test)

```python
# tests/test_scales.py
import fcwt
import numpy as np

def test_linfreq_includes_endpoints():
    """Issue #48: FCWT_LINFREQS must span exactly [f0, f1] inclusive."""
    fs, f0, f1, fn = 1000, 10.0, 100.0, 20
    morl = fcwt.Morlet(2.0)
    scales = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, fs, f0, f1, fn)
    freqs = np.zeros(fn, dtype='float32')
    scales.getFrequencies(freqs)
    assert abs(freqs.max() - f1) < 0.5, f"Max freq {freqs.max():.2f} != f1 {f1}"
    assert abs(freqs.min() - f0) < 0.5, f"Min freq {freqs.min():.2f} != f0 {f0}"

def test_linfreq_fn1_no_crash():
    """Issue #65: single-frequency Scales must not crash or divide by zero."""
    morl = fcwt.Morlet(2.0)
    scales = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, 1000, 50.0, 50.0, 1)
    freqs = np.zeros(1, dtype='float32')
    scales.getFrequencies(freqs)
    assert abs(freqs[0] - 50.0) < 0.5
```

#### Fix

In `fcwt.cpp` inside `calculate_linfreq_array` (line ~171):

```cpp
// Before:
    for(int i=0; i<fn; i++) {
        scales[fn-i-1] = (((float)fs)/(nf0 + (df/fn)*(float)i));
    }

// After (inclusive endpoints, safe for fn==1):
    float denom = (fn > 1) ? (float)(fn - 1) : 1.0f;
    for(int i=0; i<fn; i++) {
        scales[fn-i-1] = (((float)fs)/(nf0 + (df/denom)*(float)i));
    }
```

Also verify `calculate_linscale_array` (line ~187) which has the same pattern:
```cpp
// Before:
        scales[i] = (s0 + (ds/fn)*i);
// After:
        float denom = (fn > 1) ? (float)(fn - 1) : 1.0f;
        scales[i] = (s0 + (ds/denom)*(float)i);
```

`calculate_logscale_array` already uses `(fn-1)` in its power formula and is correct.

---

### Plan 5 — Fix Apple Silicon / ARM crashes (Group E)

**Issues:** #37, #68, #51, #34
**Severity:** Critical | **Difficulty:** Medium

#### Confirm (test)

Reproducer for an M1/M2/M3 user:

```python
# Run this on Apple Silicon — should print "OK", not crash
import fcwt, numpy as np
sig = np.ones(4096, dtype='float32')
morl = fcwt.Morlet(2.0)
sc = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, 1000, 1, 100, 10)
f = fcwt.FCWT(morl, 1, False, False)
out = np.zeros((10, 4096), dtype='csingle')
f.cwt(sig, sc, out)
print("OK")
```

If `zsh: illegal hardware instruction` appears, the AVX path is incorrectly compiled for ARM.

A GitHub Actions runner on `macos-14` (ARM) provides automated confirmation (see Plan 9).

#### Fix

**In `CMakeLists.txt`:** Replace any unconditional `-mavx2` / `-D__AVX__` flags with a compiler feature test:

```cmake
include(CheckCXXCompilerFlag)
check_cxx_compiler_flag("-mavx2" COMPILER_SUPPORTS_AVX2)
if(COMPILER_SUPPORTS_AVX2 AND NOT CMAKE_SYSTEM_PROCESSOR MATCHES "arm|aarch64")
    target_compile_options(fCWT PRIVATE -mavx2)
    target_compile_definitions(fCWT PRIVATE __AVX__)
endif()
```

**Replace hardcoded libomp path** (also fixes #42 and #75) — remove the literal `/usr/local/opt/libomp/lib` path and use CMake's OpenMP discovery:

```cmake
find_package(OpenMP REQUIRED)
target_link_libraries(fCWT PUBLIC OpenMP::OpenMP_CXX)
```

This lets CMake resolve the correct path on Homebrew ARM (`/opt/homebrew/…`), Intel Homebrew (`/usr/local/opt/…`), and Linux (`/usr/lib/…`).

---

### Plan 6 — Fix CMake install / `find_package` (#57)

**Issues:** #57, #76
**Severity:** High | **Difficulty:** Medium

#### Confirm (test)

```bash
cmake -B /tmp/fcwt_build /path/to/fCWT -DCMAKE_INSTALL_PREFIX=/tmp/fcwt_install
cmake --build /tmp/fcwt_build -j4
cmake --install /tmp/fcwt_build

# Consumer project
mkdir /tmp/fcwt_consumer && cd /tmp/fcwt_consumer
cat > CMakeLists.txt <<'EOF'
cmake_minimum_required(VERSION 3.15)
project(consumer)
find_package(fCWT REQUIRED)
add_executable(test_consumer main.cpp)
target_link_libraries(test_consumer PRIVATE fCWT)
EOF
cmake . -DfCWT_DIR=/tmp/fcwt_install/share/fcwt/cmake
cmake --build .
```

Failure with "could not find fCWT-config.cmake" confirms the issue.

#### Fix

Add to `CMakeLists.txt` after the existing `install()` commands:

```cmake
include(CMakePackageConfigHelpers)

configure_package_config_file(
    "${CMAKE_CURRENT_SOURCE_DIR}/cmake/fCWT-config.cmake.in"
    "${CMAKE_CURRENT_BINARY_DIR}/fCWT-config.cmake"
    INSTALL_DESTINATION share/fcwt/cmake
)

write_basic_package_version_file(
    "${CMAKE_CURRENT_BINARY_DIR}/fCWT-config-version.cmake"
    VERSION ${PROJECT_VERSION}
    COMPATIBILITY SameMajorVersion
)

install(FILES
    "${CMAKE_CURRENT_BINARY_DIR}/fCWT-config.cmake"
    "${CMAKE_CURRENT_BINARY_DIR}/fCWT-config-version.cmake"
    DESTINATION share/fcwt/cmake
)
```

Create `cmake/fCWT-config.cmake.in`:

```cmake
@PACKAGE_INIT@
include("${CMAKE_CURRENT_LIST_DIR}/fCWT-targets.cmake")
find_dependency(FFTW3f REQUIRED)
```

The `FFTW3f` find_dependency ensures that downstream consumers inherit the FFTW3 header search path (fixing #76 for installed-library users).

---

### Plan 7 — Fix threading performance (#83)

**Issues:** #83
**Severity:** Medium | **Difficulty:** Hard

#### Confirm (test)

```python
# tests/test_threading.py
import fcwt, numpy as np, time

def _time_cwt(nthreads, n=200_000, fn=100, fs=1000):
    sig = np.random.randn(n).astype('float32')
    morl = fcwt.Morlet(2.0)
    sc = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, fs, 1, 200, fn)
    f = fcwt.FCWT(morl, nthreads, False, False)
    out = np.zeros((fn, n), dtype='csingle')
    t0 = time.perf_counter()
    f.cwt(sig, sc, out)
    return time.perf_counter() - t0

def test_more_threads_faster():
    """Issue #83: 8 threads must be faster than 1 thread on a large signal."""
    t1 = _time_cwt(1)
    t8 = _time_cwt(8)
    assert t8 < t1 * 0.6, f"8-thread time {t8:.3f}s not meaningfully faster than 1-thread {t1:.3f}s"
```

#### Fix approach

The core problem is that `athreads` (the number of threads used inside `daughter_wavelet_multiplication`) drops to 1 for high-frequency/small-scale bands because `endpoint4` is small. Threading within a single scale's multiplication is not the right granularity for high thread counts.

The better design is **scale-level parallelism**: process multiple scales concurrently, one thread per scale. This matches how `pywavelets` and other CWT libraries handle it:

```cpp
// Conceptual change in FCWT::cwt():
// Instead of sequential loop over scales, parallelise at scale level:
#pragma omp parallel for schedule(dynamic)
for(int i = 0; i < scales->nscales; i++) {
    // Each thread needs its own O1 buffer (currently shared — race condition)
    // Allocate per-thread O1 with thread-local storage or an array of buffers
    convolve(pinv_per_thread[omp_get_thread_num()], Ihat, O1_per_thread[...], ...);
}
```

This is an architectural change requiring thread-local FFTW plans and buffers; it should be done in a dedicated PR with profiling before and after.

---

### Plan 8 — Fix integer truncation artefacts (#27)

**Issues:** #27
**Severity:** Medium | **Difficulty:** Medium

#### Confirm (test)

```python
# tests/test_artefacts.py
import fcwt, numpy as np

def test_short_signal_peak_frequency():
    """Issue #27: CWT of a short pure sine must still peak near the correct frequency."""
    fs, hz, n, fn = 1000, 50, 512, 100
    sig = np.sin(2 * np.pi * hz * np.arange(n) / fs).astype('float32')
    morl = fcwt.Morlet(2.0)
    sc = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, fs, 10, 200, fn)
    f = fcwt.FCWT(morl, 1, False, True)
    out = np.zeros((fn, n), dtype='csingle')
    f.cwt(sig, sc, out)
    freqs = np.zeros(fn, dtype='float32')
    sc.getFrequencies(freqs)
    peak = int(np.argmax(np.abs(out).mean(axis=1)))
    assert abs(freqs[peak] - hz) < 10, f"Peak at {freqs[peak]:.1f} Hz, expected ~{hz} Hz"
```

#### Fix

Replace truncation with rounding in `daughter_wavelet_multiplication`.

Non-AVX scalar path (`fcwt.cpp` around line 291):
```cpp
// Before:
float tmp = min(maximum, step*q);
output[q1][0] = input[q1][0]*mother[(int)tmp];
output[q1][1] = input[q1][1]*mother[(int)tmp]*(1-2*imaginary);

// After:
float tmp = min(maximum, step*q);
int idx = (int)(tmp + 0.5f);
output[q1][0] = input[q1][0]*mother[idx];
output[q1][1] = input[q1][1]*mother[idx]*(1-2*imaginary);
```

AVX path: each `(int)tmp.a[N]` becomes `(int)(tmp.a[N] + 0.5f)`.

---

### Plan 9 — Add GitHub Actions CI (#33)

**Issues:** #33
**Severity:** Medium | **Difficulty:** Medium

#### Implementation

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install deps
        run: sudo apt-get install -y libfftw3-dev libomp-dev
      - name: Build
        run: |
          cmake -B build -DCMAKE_BUILD_TYPE=Release
          cmake --build build -j$(nproc)
      - name: Python tests
        run: |
          pip install ".[tests]"
          pytest tests/

  build-macos-x86:
    runs-on: macos-13
    steps:
      - uses: actions/checkout@v4
      - name: Install deps
        run: brew install fftw libomp
      - name: Build
        run: |
          cmake -B build -DCMAKE_BUILD_TYPE=Release
          cmake --build build -j$(sysctl -n hw.ncpu)
      - name: Python tests
        run: |
          pip install ".[tests]"
          pytest tests/

  build-macos-arm:
    runs-on: macos-14
    steps:
      - uses: actions/checkout@v4
      - name: Install deps
        run: brew install fftw libomp
      - name: Build
        run: |
          cmake -B build -DCMAKE_BUILD_TYPE=Release
          cmake --build build -j$(sysctl -n hw.ncpu)
      - name: Python tests
        run: |
          pip install ".[tests]"
          pytest tests/

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install FFTW via vcpkg
        run: vcpkg install fftw3:x64-windows
      - name: Build
        run: |
          cmake -B build -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake
          cmake --build build --config Release
```

This CI matrix directly confirms issues #37, #68, #51 (ARM runner), #75, #78 (Windows runner), and #84/#81 (MSVC compiler).

---

### Plan 10 — Regression test suite

**Purpose:** A single test file covering all confirmed bugs so future regressions are caught before merge.

```python
# tests/test_regressions.py
"""Regression tests for known fixed bugs."""
import numpy as np
import pytest


def _sig(n=4096, fs=1000, hz=10):
    return np.sin(2 * np.pi * hz * np.arange(n) / fs).astype('float32')


# Group B: memory safety

def test_repeated_cwt_no_segfault():
    """Issues #74, #55: repeated cwt() calls must not crash from use-after-free or leak."""
    import fcwt
    morl = fcwt.Morlet(2.0)
    sc = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, 1000, 1, 100, 20)
    f = fcwt.FCWT(morl, 1, False, False)
    for _ in range(50):
        out = np.zeros((20, 4096), dtype='csingle')
        f.cwt(_sig(), sc, out)


def test_small_fn_no_crash():
    """Issue #65: fn=10 must not cause a memory error."""
    import fcwt
    morl = fcwt.Morlet(2.0)
    sc = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, 1000, 1, 100, 10)
    f = fcwt.FCWT(morl, 1, False, False)
    out = np.zeros((10, 4096), dtype='csingle')
    f.cwt(_sig(), sc, out)


# Group C: Python boilerplate

def test_cwt_boilerplate_arg_order():
    """Issue #80: cwt() must return (freqs, output) with freqs as float32 array."""
    from fcwt.boilerplate import cwt
    freqs, out = cwt(_sig(), 1000, 1, 100, 20)
    assert freqs.shape == (20,), f"Expected (20,), got {freqs.shape}"
    assert freqs.dtype in (np.float32, np.float64), f"freqs dtype is {freqs.dtype}"
    assert out.shape == (20, 4096)
    assert np.iscomplexobj(out)


def test_import_fcwt():
    """Issue #70: importing fcwt must not fail due to missing matplotlib."""
    import importlib
    mod = importlib.import_module('fcwt')
    assert hasattr(mod, 'cwt')


# Group D: scale endpoints

def test_linfreq_endpoints():
    """Issues #48, #82: FCWT_LINFREQS must include both f0 and f1."""
    import fcwt
    fs, f0, f1, fn = 1000, 5.0, 200.0, 50
    morl = fcwt.Morlet(2.0)
    sc = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, fs, f0, f1, fn)
    freqs = np.zeros(fn, dtype='float32')
    sc.getFrequencies(freqs)
    assert abs(freqs.min() - f0) < 0.5, f"Min freq {freqs.min():.2f} != f0={f0}"
    assert abs(freqs.max() - f1) < 0.5, f"Max freq {freqs.max():.2f} != f1={f1}"


# Group H: correctness

def test_cwt_peak_at_correct_frequency():
    """Sanity: CWT of a pure sine must peak at that sine's frequency."""
    import fcwt
    fs, hz, n, fn = 1000, 50, 8192, 100
    sig = np.sin(2 * np.pi * hz * np.arange(n) / fs).astype('float32')
    morl = fcwt.Morlet(2.0)
    sc = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, fs, 1, 200, fn)
    f = fcwt.FCWT(morl, 1, False, True)
    out = np.zeros((fn, n), dtype='csingle')
    f.cwt(sig, sc, out)
    freqs = np.zeros(fn, dtype='float32')
    sc.getFrequencies(freqs)
    peak = int(np.argmax(np.abs(out).mean(axis=1)))
    assert abs(freqs[peak] - hz) < 5, f"Peak at {freqs[peak]:.1f} Hz, expected {hz} Hz"
```

---

## Part 4 — Priority Order

| Priority | Plan | Issues | Effort | Impact |
|----------|------|--------|--------|--------|
| 1 | Plan 3 — boilerplate.py bugs | #80, #73, #70 | 30 min | Fixes all Python `plot()` users |
| 2 | Plan 1 — missing headers | #84, #81 | 10 min | Fixes MSVC/MinGW builds |
| 3 | Plan 2 — memory leaks | #74, #55 | 30 min | Eliminates UB + leak |
| 4 | Plan 4 — scale off-by-one | #82, #48 | 30 min | Correct frequency endpoints |
| 5 | Plan 5 — Apple Silicon | #37, #68, #51 | 2 h | Unblocks M1/M2/M3 users |
| 6 | Plan 6 — CMake install | #57, #76 | 3 h | Unblocks C++ downstream users |
| 7 | Plan 9 — CI | #33 | 2 h | Prevents future regressions |
| 8 | Plan 8 — artefacts | #27 | 2 h | Better quality for short signals |
| 9 | Plan 7 — threading | #83 | days | Performance improvement |
| 10 | Feature requests | #54, #36, #23 | weeks | New capabilities |

---

## Part 5 — Files to Modify per Fix

| Fix | Files |
|-----|-------|
| Plan 1 | `src/fcwt/fcwt.cpp` (+2 includes) |
| Plan 2 | `src/fcwt/fcwt.cpp` (free lastscalemem; fix delete→free) |
| Plan 3 | `src/fcwt/boilerplate.py` (arg order); `pyproject.toml` (add matplotlib) |
| Plan 4 | `src/fcwt/fcwt.cpp` (linfreq + linscale denominator) |
| Plan 5 | `CMakeLists.txt` (AVX guard; OpenMP find_package) |
| Plan 6 | `CMakeLists.txt`; new `cmake/fCWT-config.cmake.in` |
| Plan 7 | `src/fcwt/fcwt.cpp` (threading architecture — larger PR) |
| Plan 8 | `src/fcwt/fcwt.cpp` (rounding in daughter_wavelet_multiplication) |
| Plan 9 | `.github/workflows/ci.yml` (new file) |
| Plan 10 | `tests/test_regressions.py` (new file) |

---

## Part 6 — Open PR Status (checked 2026-04-27)

There are **7 open PRs**. Summary and merge-readiness assessment:

| PR | Title | Issues covered | Status | Gaps / required work before merge |
|----|-------|---------------|--------|-----------------------------------|
| #84 | Fix missing includes `<cstring>` and `<cassert>` | #84, #81 | **Merge-ready** | Adds includes to `fcwt.h` (not `fcwt.cpp` as Plan 1 suggested — header placement is fine). No gaps. |
| #80 | Bug in boilerplate.py | #80 | **Merge-ready** | Fixes `_plot(input, freqs, output, ...)` arg order. Should be merged with or after #73. |
| #73 | Bugfix boilerplate.py plot y-ticks | #73 | **Merge-ready with note** | Fixes float step (`fn/10` to `int(fn/10)`) in `np.arange`. Correct but fragile: `int(fn/10)==0` when `fn<10`, which causes `np.arange` to loop infinitely. Consider `max(1, int(fn/10))` or switch to `np.linspace`. Must be merged alongside #80. |
| #70 | Fix matplotlib import error | #70 | **Merge-ready** | Moves `import matplotlib.pyplot as plt` inside `_plot()` (lazy import) rather than adding it to `pyproject.toml`. Makes matplotlib optional at import time. Still need to add matplotlib to `pyproject.toml` as an optional dep (`[project.optional-dependencies]`) so `pip install fcwt[plot]` works. |
| #55 | fix memory leaks | #74, #55 | **Merge-ready with one fix** | Comprehensive: fixes `delete`→`fftwf_free` in `Morlet::getWavelet()`, adds `Scales::~Scales()` destructor (bonus fix not in Plan 2), fixes `malloc`→`fftwf_malloc` in `create_FFT_optimization_plan`, adds `free(lastscalemem)` in `convolve()`. **One gap:** uses plain `free(lastscalemem)` but `lastscalemem` is allocated with `aligned_alloc` (POSIX) / `_aligned_malloc` (Windows). On Windows this must be `_aligned_free(lastscalemem)` to avoid UB. Add the `#ifdef _WIN32` guard described in Plan 2 before merging. |
| #58 | Restructured entire code base to modern C++ | #58 | **Not ready — hold** | +800/-44 lines; separates classes into files, adds `fcwt` namespace, replaces raw pointers. Author explicitly notes Python bindings need regeneration and the API class refactor is unfinished. Merging now breaks all Python users and downstream C++ consumers. Track separately; requires Python binding re-gen and full regression testing. |
| #33 | Add Github Actions | #33 | **Stale — needs replacement** | From April 2023; uses deprecated `actions/checkout@v3`, deprecated `setup.py install`, and `macos-12` for the ARM job (that runner is x86_64, not native ARM; use `macos-14` for true ARM). Python test job is failing per author note. Plan 9 provides a more complete, modern version. Close this PR and open a fresh one based on Plan 9. |

### What remains with no open PR

| Plan | Issues | Notes |
|------|--------|-------|
| Plan 4 — scale off-by-one | #82, #48 | `calculate_linfreq_array` still uses `fn` not `fn-1` as denominator. No PR exists. |
| Plan 5 — Apple Silicon crash | #37, #68, #51 | No PR for the AVX guard / libomp fix in CMakeLists. |
| Plan 6 — CMake install / find_package | #57, #76 | No PR for package config files. |
| Plan 7 — threading performance | #83 | No PR. |
| Plan 8 — integer truncation artefacts | #27 | No PR. |
| `pyproject.toml` matplotlib optional dep | #70 | PR #70 fixes the crash but does not add matplotlib as an optional dep. |

### Recommended merge sequence

1. **#84** — merge immediately (2-line include fix, no risk).
2. **#70** — merge (lazy matplotlib import; independent of other PRs).
3. **#80 + #73** — merge together; together they fully fix `plot()`.
4. **#55** — add the `_aligned_free` Windows guard (one-line change), then merge.
5. **#33** — close and replace with a fresh CI PR based on Plan 9 (use `macos-14`, `actions/checkout@v4`, `pip install -e ".[tests]"`).
6. **#58** — hold until Python bindings are regenerated and API class refactor is complete.

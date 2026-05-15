import numpy as np
import pytest

# We wrap the import in a try-except for the test runner, 
# but if it's broken, the test will fail correctly.
try:
    import fcwt
    HAS_FCWT = True
except ImportError:
    HAS_FCWT = False

def _sig(n=4096, fs=1000, hz=10):
    return np.sin(2 * np.pi * hz * np.arange(n) / fs).astype('float32')

def test_apple_silicon_crash():
    """
    Plan 5: Reproduce 'illegal hardware instruction' on Apple Silicon.
    This test uses a simple signal and performs a CWT.
    If AVX is incorrectly enabled on ARM, this should cause a crash.
    """
    if not HAS_FCWT:
        pytest.skip("fcwt not installed")
    
    sig = np.ones(4096, dtype='float32')
    morl = fcwt.Morlet(2.0)
    # Use a small number of scales to keep it fast
    sc = fcwt.Scales(morl, fcwt.FCWT_LINFREQS, 1000, 1, 100, 10)
    f = fcwt.FCWT(morl, 1, False, False)
    out = np.zeros((10, 4096), dtype='csingle')
    
    try:
        f.cwt(sig, sc, out)
    except Exception as e:
        pytest.fail(f"CWT call failed with error: {e}")
    
    print("OK: CWT execution successful")

if __name__ == "__main Mancode":
    # Allow running this script directly for quick verification
    import sys
    test_apple_silicon_crash()

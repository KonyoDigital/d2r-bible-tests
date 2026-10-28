# -*- coding: utf-8 -*-
"""#151 - FREE SPACE AS macOS COUNTS IT FOR A WRITE THAT MATTERS: purgeable space included.

His ask (2026-10-21, #151): the disk guards and the console's disk sign count purgeable space. macOS answers "how much can
an important write use" with the space free now PLUS what it will free on demand (local snapshots, caches it may drop) -
the figure Finder shows. shutil.disk_usage counts only the blocks free this instant. MEASURED on his Mac 2026-10-28:
13.19 GB available for important usage against 11.98 GB plain, so the ON AIR floor (8 GB) and the proving lanes' room
refused earlier than macOS itself would have.

free_bytes(path) -> (bytes, kind)
    kind "important"  macOS answered (CoreFoundation, kCFURLVolumeAvailableCapacityForImportantUsageKey, over ctypes - no
                      pyobjc needed, so every Python on the Mac reads it); bytes is the larger of that and the plain free
    kind "plain"      anywhere else: Windows, Linux CI, a key that would not answer - or a law that stubbed
                      shutil.disk_usage. A stubbed reading is a SCENARIO ("the disk is at 7 GB"), and the purgeable add-on
                      belongs to the real disk only; adding the real Mac's purgeable space to a law's pretend disk would make
                      the law pass on a runner and fail on his Mac. [[regression-guard]] section 3
It raises exactly what shutil.disk_usage raises, so a guard that read the disk before reads it the same way now, and
each caller keeps its own UNKNOWN handling. [[unknown-stays-unknown]]
"""
import ctypes
import ctypes.util
import shutil
import sys

_CF = None
_CF_WHY = None


def _cf():
    """CoreFoundation, loaded once and typed. -> the library, or None (and _CF_WHY says why)"""
    global _CF, _CF_WHY
    if _CF is not None or _CF_WHY is not None:
        return _CF
    try:
        cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library("CoreFoundation") or "CoreFoundation")
        cf.CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
        cf.CFURLCreateFromFileSystemRepresentation.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_bool]
        cf.CFURLCopyResourcePropertyForKey.restype = ctypes.c_bool
        cf.CFURLCopyResourcePropertyForKey.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p),
                                                       ctypes.c_void_p]
        cf.CFNumberGetValue.restype = ctypes.c_bool
        cf.CFNumberGetValue.argtypes = [ctypes.c_void_p, ctypes.c_long, ctypes.c_void_p]
        cf.CFRelease.argtypes = [ctypes.c_void_p]
        cf._important_key = ctypes.c_void_p.in_dll(cf, "kCFURLVolumeAvailableCapacityForImportantUsageKey")
        _CF = cf
    except Exception as e:
        _CF_WHY = "CoreFoundation would not answer (%s)" % type(e).__name__
    return _CF


def important_bytes(path):
    """What macOS says an important write at `path` may use, purgeable included. -> int, or None when it will not say"""
    if sys.platform != "darwin":
        return None
    cf = _cf()
    if cf is None:
        return None
    raw = str(path).encode("utf-8")
    url = cf.CFURLCreateFromFileSystemRepresentation(None, raw, len(raw), True)
    if not url:
        return None
    try:
        val = ctypes.c_void_p()
        if not cf.CFURLCopyResourcePropertyForKey(url, cf._important_key, ctypes.byref(val), None) or not val.value:
            return None
        try:
            out = ctypes.c_int64()
            return int(out.value) if cf.CFNumberGetValue(val, 4, ctypes.byref(out)) and out.value >= 0 else None
        finally:
            cf.CFRelease(val)
    except Exception:
        return None
    finally:
        cf.CFRelease(url)


def _disk_usage_is_real():
    """Is shutil.disk_usage the library's own function? A law that replaced it (a lambda, a mock) is asking about a
    pretend disk. Judged from the function itself, never from a copy taken at import: this module is imported lazily,
    sometimes AFTER a law installed its stub, and a captured "real" function was then the stub (measured: the warden
    read 10.59 GiB, the real disk's purgeable figure, under a law's 7 GiB disk). -> bool"""
    f = shutil.disk_usage
    return getattr(f, "__module__", None) == "shutil" and getattr(f, "__qualname__", None) == "disk_usage"


def free_bytes(path):
    """Free space at `path` for a write that matters. -> (bytes, "important" | "plain"). Raises what disk_usage raises."""
    plain = shutil.disk_usage(path).free
    if not _disk_usage_is_real():
        return plain, "plain"
    imp = important_bytes(path)
    if imp is None:
        return plain, "plain"
    return max(plain, imp), "important"


def free_gb(path):
    """free_bytes in GB (1e9, as every floor in this repo is written). -> float. Raises what disk_usage raises."""
    return free_bytes(path)[0] / 1e9

"""v1608 — REEL INDEX RECOVERY, THE ONLY WRITER.

A reel is 98 real JPEGs plus a 3 KB index.json, and WITHOUT THE INDEX IT IS NOT FOOTAGE: theatre,
read_reel() and sweep_hist() all open index.json first, so a reel that lost it plays BLACK. The
rebuild is trivial — every frame is named f_<epoch-ms>.jpg, which is exactly the ("f", "ts") pair the
index carries — and the READING half of that lives in chronicle_retro (reconstruct_index/load_index),
which is provably write-free and must stay that way (test_chronicle_retro asserts it from source).

This module is the other half: it puts the rebuilt index ON DISK. It is deliberately a separate file
so the read-only law next door keeps its structural proof. It writes exactly one filename —
index.json — atomically, never touches a .jpg, never rewrites an index that already parses, and is
LOUD when a write fails, because a swallowed failure here is how a reel goes unplayable unnoticed.
"""

import json
import os

from chronicle_retro import INDEX_REBUILD_MARK, _index_ok, reconstruct_index  # noqa: F401


def _write_json_atomic(path, obj):
    """Write JSON so a reader never sees a half-file: tmp in the SAME dir → flush → fsync → replace.
    os.replace is atomic within a directory, so index.json is either the old one or the whole new
    one, never a truncated middle."""
    d = os.path.dirname(path) or "."
    tmp = os.path.join(d, ".index.json.%d.tmp" % os.getpid())
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(obj, fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            if os.path.basename(tmp).startswith(".index.json.") and os.path.isfile(tmp):
                os.remove(tmp)   # our own tmp, never a frame
        except Exception:
            pass
        raise


def ensure_reel_index(reel_dir):
    """v1607 — SELF-HEAL A REEL, ADDITIVELY. Returns the index dict, or None if there is nothing to
    index. THIS IS THE ONLY WRITER IN THIS MODULE, and it writes exactly one file: index.json.

    · An index that exists and parses is returned UNCHANGED — never rewritten, never reordered,
      never enriched with blank flags. This is his real farming footage; the safe move on a good
      index is to touch nothing.
    · Otherwise the index is rebuilt from the frame names and written atomically.
    · A corrupt index.json is PRESERVED first, as index.json.corrupt, before the rebuilt one lands —
      nothing is destroyed to make the reel playable.
    · No .jpg is ever opened for writing, renamed, or unlinked anywhere in this module.
    · A write that fails is LOUD and returns None. Silently swallowing this failure is how a reel
      goes unplayable without anyone finding out for weeks.
    """
    # v1608 — ONLY A REEL IS A REEL. The hist dir also holds the resize caches (cache160/cache1280),
    # which are full of f_<ms>.jpg thumbnails and would otherwise be "healed" into fake reels that
    # theatre then lists as footage. Anything not named reel_* is not ours to index.
    if not os.path.basename(os.path.normpath(reel_dir)).startswith("reel_"):
        return None
    idx_path = os.path.join(reel_dir, "index.json")
    raw = None
    try:
        with open(idx_path, encoding="utf-8") as fh:
            raw = fh.read()
        idx = json.loads(raw)
        if _index_ok(idx):
            return idx                       # good index — leave it exactly as he sealed it
    except FileNotFoundError:
        raw = None
    except Exception:
        pass                                 # unreadable/corrupt → fall through to the rebuild
    rebuilt = reconstruct_index(reel_dir)
    if not rebuilt:
        return None
    try:
        if raw is not None:
            keep = idx_path + ".corrupt"
            if not os.path.exists(keep):     # additive: preserve the original bytes, once
                with open(keep, "w", encoding="utf-8") as fh:
                    fh.write(raw)
        _write_json_atomic(idx_path, rebuilt)
    except Exception as e:
        print("⚠️  chronicle_retro: could NOT write %s — the reel stays unplayable: %s"
              % (idx_path, e))
        return None
    print("🔧 chronicle_retro: rebuilt index for %s from %d frames on disk (%s)"
          % (os.path.basename(os.path.normpath(reel_dir)), rebuilt["n"], INDEX_REBUILD_MARK))
    return rebuilt

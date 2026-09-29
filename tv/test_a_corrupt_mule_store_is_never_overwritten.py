# -*- coding: utf-8 -*-
"""2026-09-29 — A MULE STORE THAT WILL NOT PARSE WAS READ AS EMPTY, AND THE NEXT SAVE ERASED IT.

Found by the #41 heart audit (verified, rank 7): the vault module's load() answered {} for d2r_muleAssign bytes that
would not parse, the picker said "<mule> holds no items in this PC's store", and the next saveA() wrote {} over the
corrupt bytes - every mule assignment gone, while the doctor reading the same store said UNKNOWN.

DRIVEN on the shipped code, cut from bible.html by its own anchors and run in node against a fake store: corrupt
bytes stay byte-for-byte after a save, the store reads UNKNOWN ("will not parse"), a healthy store still saves, and
no write to d2r_muleAssign / d2r_muleRoster in that module goes around the guard. RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

NODE = shutil.which("node")
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")


def _module():
    with io.open(BIBLE, encoding="utf-8") as fh:
        src = fh.read()
    i = src.index('<script id="v203-vault-js">')
    j = src.index("</script>", i)
    return src[i:j]


def _cut(mod, start, end_marker):
    a = mod.index(start)
    b = mod.index(end_marker, a) + len(end_marker)
    return mod[a:b]


def _run(stored):
    mod = _module()
    body = (_cut(mod, "  var _muleUnread = {};", "  window._muleStoreUnread = function(k){ return _muleUnread[k || AK] || null; };")
            + "\n" + _cut(mod, "  function saveA(){", "}"))
    js = ("var store = %s; var window = {LSR: {getItem: function(k){ return store.hasOwnProperty(k) ? store[k] : null; },"
          " setItem: function(k, v){ store[k] = String(v); }}};\n"
          "var console = {warn: function(){}};\n"
          "var RK = 'd2r_muleRoster', AK = 'd2r_muleAssign';\n%s\n"
          "var assign = load(AK, {}); assign['Shako'] = 'uni-armor'; var wrote = saveA();\n"
          "process.stdout.write(JSON.stringify({after: store[AK], unread: window._muleStoreUnread(), assign: assign}));\n"
          ) % (json.dumps(stored), body)
    # the program goes in a FILE, never on argv (test_no_law_hands_node_its_program_on_argv: argv has a length cap)
    fd, path = tempfile.mkstemp(suffix=".js", prefix="mule-guard-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(js)
        out = subprocess.run([NODE, path], capture_output=True, text=True, timeout=30)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if out.returncode != 0:
        raise AssertionError("node failed: %s" % out.stderr[-400:])
    return json.loads(out.stdout)


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class ACorruptMuleStoreIsNeverOverwritten(unittest.TestCase):

    def test_corrupt_bytes_survive_a_save_and_read_unknown(self):
        got = _run({"d2r_muleAssign": '{"Harlequin Crest":"uni-arm'})
        self.assertEqual(got["after"], '{"Harlequin Crest":"uni-arm',
                         "a save wrote over bytes that would not parse - every assignment in them is gone: %r" % got)
        self.assertEqual(got["unread"], "will not parse", "an unparseable store did not read UNKNOWN")

    def test_a_healthy_store_still_saves(self):
        got = _run({"d2r_muleAssign": '{"War Traveler":"uni-boots"}'})
        self.assertEqual(json.loads(got["after"]), {"War Traveler": "uni-boots", "Shako": "uni-armor"},
                         "the guard stopped an ordinary save")
        self.assertIsNone(got["unread"])

    def test_an_absent_store_is_empty_not_unknown(self):
        got = _run({})
        self.assertEqual(json.loads(got["after"]), {"Shako": "uni-armor"})
        self.assertIsNone(got["unread"], "a store that was never written read as UNKNOWN")

    def test_no_write_in_the_module_goes_around_the_guard(self):
        mod = _module()
        for bad in ("window.LSR.setItem(AK,", "window.LSR.setItem(RK,"):
            self.assertNotIn(bad, mod, "a write to the mule store skips the unreadable-store guard: %s" % bad)
        self.assertGreaterEqual(mod.count("_guardedSet(AK,") + mod.count("_guardedSet(RK,"), 8,
                                "PREMISE: the module's store writes were not found")

    def test_the_picker_says_unknown_not_holds_nothing(self):
        with io.open(BIBLE, encoding="utf-8") as fh:
            src = fh.read()
        i = src.index("holds no items in this PC")
        self.assertIn("window._muleStoreUnread()", src[i - 500:i],
                      "the picker still says the mule holds nothing when its store would not parse")


RED_PROOF = [
    {
        "why": "2026-09-29 - a save writes over mule-store bytes that would not parse again (every assignment erased)",
        "file": "bible.html",
        "find": "  function _guardedSet(k, v){ if (_muleUnread[k]) {",
        "replace": "  function _guardedSet(k, v){ if (false) {",
        "matches": 1,
    },
    {
        "why": "2026-09-29 - an unparseable mule store reads as empty again instead of UNKNOWN",
        "file": "bible.html",
        "find": "    try{ var v=JSON.parse(raw); return v||f; }catch(e){ _muleUnread[k] = 'will not parse'; return f; } }",
        "replace": "    try{ var v=JSON.parse(raw); return v||f; }catch(e){ return f; } }",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)

# -*- coding: utf-8 -*-
"""#229 — A CHILD'S WORDS ARE READ AS UTF-8 ON EVERY OS.

MEASURED 2026-09-24 on his Windows ALT: running the doctor there, a subprocess reader thread died with
`UnicodeDecodeError: 'charmap' codec can't decode byte 0x9c` - the `visual lock` row ran its child with
`text=True` and no encoding, so Python decoded the child's "✅ VISUAL-LOCK OK — ..." with the Windows locale
(cp1255). On the Mac's UTF-8 locale every such call works, which is why none of them was ever seen failing.
42 production calls had the shape; all pass encoding="utf-8", errors="replace" now.

  · AST: no production tv/*.py runs a subprocess in text mode without an explicit encoding.
  · PREMISE: the scanner sees the shape it bans (a planted call is found), so it cannot pass vacuously.
RED_PROOF below.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def unencoded_text_calls(src, name="<src>"):
    """-> [lineno] subprocess.run/check_output/Popen calls in text mode with no `encoding=`."""
    out = []
    for n in ast.walk(ast.parse(src, filename=name)):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in ("run", "check_output", "Popen") and getattr(n.func.value, "id", "") == "subprocess"):
            kws = {k.arg for k in n.keywords}
            text = any(k.arg in ("text", "universal_newlines") and getattr(k.value, "value", None) is True
                       for k in n.keywords)
            if text and "encoding" not in kws:
                out.append(n.lineno)
    return out


class AChildsWordsAreReadAsUTF8(unittest.TestCase):

    def test_premise_the_scanner_sees_the_banned_shape(self):
        planted = "import subprocess\nsubprocess.run(['x'], capture_output=True, text=True)\n"
        self.assertEqual(unencoded_text_calls(planted), [2])
        fixed = "import subprocess\nsubprocess.run(['x'], text=True, encoding='utf-8')\n"
        self.assertEqual(unencoded_text_calls(fixed), [])

    def test_no_production_module_reads_a_child_in_the_locale_encoding(self):
        hits = []
        for fn in sorted(os.listdir(HERE)):
            if not fn.endswith(".py") or fn.startswith("test_"):
                continue
            try:
                src = io.open(os.path.join(HERE, fn), encoding="utf-8").read()
                lines = unencoded_text_calls(src, fn)
            except SyntaxError:
                continue
            hits += ["%s:%d" % (fn, ln) for ln in lines]
        self.assertEqual(hits, [], "text-mode subprocess reads with the LOCALE encoding (cp1255 on his Windows "
                                   "box - a child's emoji kills the reader): %s" % hits[:8])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#229 - the visual-lock row reads its child in the locale encoding again (cp1255 on the ALT: the reader thread died on the child's emoji)",
        "file": "console_doctor.py",
        "find": "        p = subprocess.run([sys.executable, lock], capture_output=True, text=True, encoding=\"utf-8\", errors=\"replace\",",
        "replace": "        p = subprocess.run([sys.executable, lock], capture_output=True, text=True,",
        "matches": 1,
    },
]

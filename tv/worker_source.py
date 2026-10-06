# -*- coding: utf-8 -*-
"""The beacon worker's shared helpers, LIFTED from functions/api/console.js for laws that run one block of it in node.

REG-1839 — a shaper lifted on its own sees only its own text. cutAtWord() lives once, at the worker's top level, and
every shaper that ends a sentence calls it. A law that runs one shaper puts prelude() in front of it, which is the
SHIPPED function cut from the file, never a copy written here: a copy is what the law would then be grading.
[[copy-drift]] [[source-reading-guard]]
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(os.path.dirname(HERE), "functions", "api", "console.js")

#: the helpers a lifted shaper may call, each anchored on its own declaration
HELPERS = ("function cutAtWord(v, n) {",)


def prelude(src=None):
    """The shipped top-level helpers, ready to sit in front of a lifted block. -> str"""
    if src is None:
        with io.open(API, encoding="utf-8") as fh:
            src = fh.read()
    out = []
    for start in HELPERS:
        n = src.count(start)
        assert n == 1, "%r occurs %d times in functions/api/console.js" % (start, n)
        i = src.index(start)
        j = src.index("\n}\n", i)
        out.append(src[i:j + 3])
    return "".join(out)

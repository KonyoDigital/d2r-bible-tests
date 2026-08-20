#!/usr/bin/env python3
"""WHICH BLOCK ACTUALLY WINS for a selector — ask before editing a CSS rule in bible.html.

WHY. `d2r_css_last_rule_wins` is a carved scar: `.hero-title` had FOUR rules, and a twin
`filterSilver` cost him a whole pane. At equal specificity the LAST declaration wins, so editing
the first occurrence of a property changes nothing and looks like the edit did not take.

Measured on bible.html at v1877: 4,682 top-level rules, 201 selectors declared more than once, and
**153 that set the SAME property in more than one block**. That is not 153 defects — a file grown
over 1,800 versions overrides deliberately — which is exactly why this is a LOOKUP and not a gate.
A gate here would cry wolf 153 times; the hazard is a person editing the wrong copy, and the answer
to that is a question you can ask in one second.

    python3 tv/css_who_wins.py .h-title
    python3 tv/css_who_wins.py .hero-title color

Only <style> blocks are scanned, so a selector-looking string inside JS or an HTML attribute cannot
pollute the answer, and only TOP-LEVEL rules are collected — a rule inside @media is a different
cascade question and saying otherwise would be worse than silence.
"""
import io
import os
import re
import sys

# v1877 — his own guard caught this file the minute it existed: a tool that prints non-ASCII and
# does not make stdout encoding-safe CRASHES WHILE REPORTING on a non-UTF-8 console, so a clean
# tree exits non-zero and the failure is blamed on the thing being measured.
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass


def _css_spans(path):
    """Each <style> body with its EXACT offset in the file, so a rule's line number is real.

    v1877 — the first cut concatenated the style blocks and then hunted for a needle to guess the
    line. Two different rules came back "~line 29448", which in a tool whose entire job is "which
    copy do I edit" is worse than printing nothing. Offsets are carried through instead.
    Comments are blanked IN PLACE (same length) rather than removed, so every offset still lands.
    """
    src = io.open(path, encoding="utf-8").read()
    spans = []
    for m in re.finditer(r"<style[^>]*>(.*?)</style>", src, re.S):
        body = m.group(1)
        body = re.sub(r"/\*.{0,4000}?\*/", lambda c: " " * len(c.group(0)), body, flags=re.S)
        spans.append((m.start(1), body))
    return spans, src


def blocks_for(path, selector):
    """[(line, selector_list, body)] for every TOP-LEVEL rule whose selector list names `selector`.

    Only <style> bodies, so a selector-looking string in JS or an HTML attribute cannot pollute the
    answer; only DEPTH-1 rules, because a rule inside @media is a different cascade question and
    answering it here would be worse than silence.
    """
    spans, src = _css_spans(path)
    out = []
    for base, css in spans:
        depth, buf, sel, sel_at = 0, "", None, 0
        for i, ch in enumerate(css):
            if ch == "{":
                depth += 1
                if depth == 1:
                    sel = buf.strip()
                    sel_at = base + i - len(buf) + (len(buf) - len(buf.lstrip()))
                    buf = ""
                else:
                    buf += ch
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    if sel and not sel.startswith("@"):
                        parts = [p.strip() for p in sel.split(",")]
                        if selector in parts or selector == sel.strip():
                            out.append((src.count("\n", 0, sel_at) + 1, sel, buf.strip()))
                    buf, sel = "", None
                else:
                    buf += ch
            else:
                buf += ch
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    selector = argv[1]
    prop = argv[2] if len(argv) > 2 else None
    here = os.path.dirname(os.path.abspath(__file__))
    path = argv[3] if len(argv) > 3 else os.path.join(os.path.dirname(here), "bible.html")
    if not os.path.isfile(path):
        print("no such file: %s" % path)
        return 2
    rows = blocks_for(path, selector)
    if not rows:
        print("no top-level rule declares %r in %s" % (selector, os.path.basename(path)))
        return 1
    print("%d block(s) declare %s — the LAST one that sets a property is the one you see\n"
          % (len(rows), selector))
    winner = {}
    for idx, (ln, sel, body) in enumerate(rows):
        props = re.findall(r"([-a-z]+)\s*:\s*([^;]+)", body)
        for p, v in props:
            winner[p] = (idx, v.strip())
        shown = [(p, v) for p, v in props if not prop or p == prop]
        print("  [%d] line %d   %s" % (idx, ln, sel[:90]))
        for p, v in shown[:12]:
            print("        %-24s %s" % (p + ":", v.strip()[:60]))
        if not shown:
            print("        (does not set %s)" % prop)
    if prop:
        w = winner.get(prop)
        print("\n>> %s comes from block [%d]%s" % (prop, w[0], "" if w else " — nothing sets it")
              if w else "\n>> nothing sets %s" % prop)
    else:
        clash = sorted(p for p in winner
                       if sum(1 for _, b, in [(r[1], r[2]) for r in rows]
                              for _ in re.finditer(r"(?<![-a-z])" + re.escape(p) + r"\s*:", b)) > 1)
        if clash:
            print("\n>> set in more than one block (the last wins): %s" % ", ".join(clash[:14]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

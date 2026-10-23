#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1c (#152 item 4) - THE HAND-ADD SPEED CURVE, MEASURED ON THE WHOLE PAGE IN NODE.

    python3 tv/vault_speed_bench.py                 # the door (vaultHandAdd) and the click (vaultHandTake) at 50/200/550
    python3 tv/vault_speed_bench.py --n 50,200      # other sizes
    python3 tv/vault_speed_bench.py --memo-off      # window._vaultMemoOff = true: the path v3784 took (every V1c memo off)
    python3 tv/vault_speed_bench.py --door-only     # skip the click path (it repaints the vault after every add)

Each size is a FRESH page (an empty install, tv/vault_page_node.py): the planner catalogue's uniques, set pieces and
runewords are added one at a time, in catalogue order, through the real door; a name the door refuses is skipped and
counted. It prints, per size: the total, the mean of the last 10 adds before each mark, and one paint at the end.

This is a REPORT, not a gate - a clock moves with the load on the box. tv/test_a_hand_add_is_not_quadratic.py is the
gate (it counts work, which a load cannot move); GrokBot's perf3.py is the browser measurement on his screen.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import vault_page_node as VPN  # noqa: E402

BODY = r"""
(function(){
var N = __N, MODE = __MODE;
window._vaultMemoOff = __OFF;
window._vaultAutoIntakeSet(false);
var rows, take;
if (MODE === 'click') {
  window.vaultHandOpen();
  rows = (window._vhCat && window._vhCat.rows || []).filter(function(r){ return r.q === 'u' || r.q === 's' || r.q === 'r'; });
  take = function(r){ return window.vaultHandTake(r.id); };
} else {
  var KIND = { u: 'unique', s: 'set', r: 'runeword' };
  rows = window._cbHandCatalog('').rows.filter(function(r){ return r.q === 'u' || r.q === 's' || r.q === 'r'; });
  take = function(r){ return window.vaultHandAdd(r.name, null, { kind: KIND[r.q] }); };
}
var t = [], refused = 0, i = 0, T0 = H.now();
while (t.length < N && i < rows.length){
  var r = rows[i++], a = H.now();
  var res = take(r);
  H.flush(60, 3);
  var dt = H.now() - a;
  if (res && res.ok && res.mode === 'added') t.push(dt); else refused++;
}
var total = H.now() - T0;
function avg(a, b){ var s = t.slice(a, b); return s.length ? s.reduce(function(x, y){ return x + y; }, 0) / s.length : null; }
var marks = {};
[10, 50, 100, 200, 300, 400, 500, 550].forEach(function(k){ if (k <= t.length) marks[k] = Math.round(avg(Math.max(0, k - 10), k) * 10) / 10; });
var p0 = H.now(); renderVault(); H.flush(60, 3);
OUT.r = { mode: MODE, memoOff: !!window._vaultMemoOff, n: N, added: t.length, refused: refused, totalMs: Math.round(total),
          msPerAddAt: marks, paintMs: Math.round(H.now() - p0) };
})();
"""


def measure(n, mode, memo_off):
    body = (BODY.replace("__N", str(int(n))).replace("__MODE", json.dumps(mode))
            .replace("__OFF", "true" if memo_off else "false"))
    return VPN.run(body, timeout=7200)["r"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--n", default="50,200,550", help="comma-separated sizes (default 50,200,550)")
    ap.add_argument("--memo-off", action="store_true", help="run with every V1c memo off (the v3784 path)")
    ap.add_argument("--door-only", action="store_true", help="measure vaultHandAdd only, not the click path")
    a = ap.parse_args(argv)
    if not VPN.NODE:
        print("node is not on this machine - nothing measured")
        return 2
    sizes = [int(x) for x in a.n.split(",") if x.strip()]
    for mode in (("door",) if a.door_only else ("door", "click")):
        for n in sizes:
            t0 = time.time()
            r = measure(n, mode, a.memo_off)
            print(json.dumps(r), "(wall %.1fs)" % (time.time() - t0))
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())

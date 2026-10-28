# -*- coding: utf-8 -*-
"""REG-2890 / REG-2891 (intake design P2, #230 c6473846977) - A READ CARRIES WHEN IT WAS CAPTURED, NEVER WHEN IT ARRIVED.

His design: "Capture time, never arrival time. A photo takes its file's capture date; a frame takes its own timestamp."
Measured before this:
  * a dropped or picked photo was stamped with the moment it was dropped (vaultIntake's witness `at: new Date()`), and a
    folder or TV photo carried no time at all - its receipt fell back to the door's clock;
  * a live read's look (_vaultLiveWitness) carried no time, though the read row carries two: `ts` (when the read landed)
    and `captureTs` (the frame's own clock) - and the board never read captureTs;
  * a look's time, when it had one, was dropped by the witness gate (_vaultWitnessCheck kept id/frame/conf/holder/loc/cell)
    and by the filing row (vaultFile's looks), so P1 measured "0 of the 20 filing looks" dated.

Now: a photo's capture time is its file's own clock (File.lastModified - no EXIF reader exists in this repo, none is
added) on its look and its receipt; a live look takes captureTs, never ts; the gate and the filing row keep a look's time.
A file or a read with no clock says capture time unknown - no time is invented, and the receipt stays unmeasured.

Driven on the whole page in node (vault_page_node), fixtures only. RED_PROOF below.
"""
import io
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import vault_page_node as VPN  # noqa: E402

BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")
CAP = 1761609600000          # 2025-10-28T00:00:00Z - a frame's own clock
LANDED = 1761696000000       # a day later - when a read arrived
ISO = "2025-10-28T00:00:00.000Z"

BODY = r"""
var W = window, CAP = %(cap)d, LANDED = %(landed)d, ISO = %(iso)s;
OUT.shot = [W._vaultShotTime({ name: 'a.png', lastModified: CAP }), W._vaultShotTime({ name: 'b.png', lastModified: 0 }),
            W._vaultShotTime({ name: 'c.png' }), W._vaultShotTime(null)];
var wf = W._vaultPhotoWitness('a.png', { fromFolder: true }, ISO), wn = W._vaultPhotoWitness('b.png', { fromTv: true }, null);
var wh = W._vaultPhotoWitness('a.png', {}, ISO);
OUT.folderLook = wf.sessions[0]; OUT.tvLook = wn.sessions[0]; OUT.hand = wh;
OUT.recFolder = W._vaultPhotoReceipt('a.png', wf, ISO); OUT.recNone = W._vaultPhotoReceipt('b.png', wn, null);
OUT.recHand = W._vaultPhotoReceipt('a.png', wh, ISO);
OUT.takenMixed = W._vaultTakenSay([{ taken: ISO }, { taken: null }]);
OUT.takenNone = W._vaultTakenSay([{ taken: null }, { taken: null }]);
/* the owned door: a receipt with the capture time is MEASURED at that time; without one it is not */
W._ownedAdd('Harlequin Crest', OUT.recFolder);
W._ownedAdd('Stone of Jordan', OUT.recNone);
var prov = JSON.parse(localStorage.getItem('d2r_vaultProv') || '{}');
OUT.provDated = prov['Harlequin Crest'] || null; OUT.provUndated = prov['Stone of Jordan'] || null;
/* a live read: the frame's clock, never the landing clock */
OUT.live = W._vaultLiveWitness({ sessionId: 's1', frameId: 'f1', captureTs: CAP, ts: LANDED });
OUT.liveNoCap = W._vaultLiveWitness({ sessionId: 's1', frameId: 'f1', ts: LANDED });
/* the gate keeps a look's time, and refuses to invent one for a look whose time does not read */
var wc = W._vaultWitnessCheck({ lane: 'stash', sessions: [{ session: 's1', frame: 'f1', at: ISO, cell: 'stash:c0r0' },
                                                           { session: 's2', frame: 'f2', at: 'not a time', cell: 'stash:c0r0' }] });
OUT.gate = wc;
/* and the filing row keeps it */
var fw = { lane: 'stash', by: 'tv-live', sessions: [{ session: 's1', frame: 'f1', at: ISO, cell: 'stash:c0r0' },
                                                     { session: 's2', frame: 'f2', at: CAP + 3600000, cell: 'stash:c0r0' }] };
OUT.filed = W.vaultFile('Magefist', fw, { mule: 'uni-armor' });
var prov2 = JSON.parse(localStorage.getItem('d2r_vaultProv') || '{}');
OUT.fileRow = prov2['Magefist'] || null;
""" % {"cap": CAP, "landed": LANDED, "iso": json.dumps(ISO)}


def _intake_src():
    src = io.open(BIBLE, encoding="utf-8").read()
    i = src.index("  window.vaultIntake = async function(files, opts){")
    return src[i:src.index("\n  };\n", i)]


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AReadCarriesWhenItWasCaptured(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude="localStorage.setItem('d2r_ownerClaim', '*');\n", timeout=300)

    def test_a_photo_is_timed_by_its_own_file_clock_or_unknown(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertEqual(self.o["shot"], [ISO, None, None, None], "a file with no clock was given a time: %r" % self.o["shot"])

    def test_a_photo_look_and_its_receipt_carry_the_capture_time(self):
        self.assertEqual(self.o["folderLook"].get("at"), ISO)
        self.assertNotIn("at", self.o["tvLook"], "a photo with no clock was dated: %r" % self.o["tvLook"])
        self.assertEqual(self.o["recFolder"].get("ts"), ISO)
        self.assertNotIn("ts", self.o["recNone"], "a receipt with no clock was dated: %r" % self.o["recNone"])
        # his hand: the declaration keeps its own time (when he said so); the picture's time rides on the receipt
        self.assertEqual(self.o["hand"]["by"], "hand")
        self.assertEqual(self.o["recHand"].get("ts"), ISO)

    def test_the_owned_door_measures_the_receipt_at_the_capture_time(self):
        d, u = self.o["provDated"], self.o["provUndated"]
        self.assertTrue(d and d.get("tsMeasured") is True and d.get("ts") == CAP, "the dated receipt is not measured at its capture: %r" % d)
        self.assertTrue(u and u.get("tsMeasured") is False and u.get("ts") is None,
                        "an undated receipt was measured at the door's clock - arrival read as capture: %r" % u)

    def test_the_report_says_when_the_pictures_were_taken_or_that_it_is_unknown(self):
        self.assertIn('data-taken-from="%s"' % ISO, self.o["takenMixed"])
        self.assertIn("1 with capture time unknown", self.o["takenMixed"])
        self.assertIn("capture time unknown for all 2", self.o["takenNone"])
        self.assertNotIn("taken 20", self.o["takenNone"], "a batch with no clocks was given a date")

    def test_the_door_hands_every_file_its_own_time(self):
        src = _intake_src()
        for call in ("window._vaultShotTime(f)", "window._vaultPhotoWitness(fname, opts, _capOf(fname))",
                     "window._vaultPhotoReceipt(fname, _intakeWitness(fname), _capOf(fname))", "window._vaultTakenSay(perFile)"):
            self.assertEqual(src.count(call), 1, "vaultIntake does not call %s exactly once" % call)
        self.assertNotIn("at: new Date().toISOString(), where: 'his photo upload'", src,
                         "vaultIntake builds its own witness again instead of the one door")

    def test_a_live_look_takes_the_frames_clock_never_the_landing_clock(self):
        live, none = self.o["live"], self.o["liveNoCap"]
        self.assertEqual((live["sessions"][0].get("at"), live.get("at")), (ISO, ISO), live)
        self.assertNotIn("at", none["sessions"][0], "a read with no captureTs was dated by when it landed: %r" % none)
        self.assertNotIn("at", none)

    def test_the_gate_keeps_a_looks_time_and_never_invents_one(self):
        g = self.o["gate"]
        self.assertTrue(g.get("ok"), g)
        at = {k["id"]: k.get("at") for k in g["looks"]}
        self.assertEqual(at, {"s1": ISO, "s2": None}, "the gate lost a look's time or kept one that does not read: %r" % at)

    def test_the_filing_row_keeps_each_looks_time(self):
        self.assertTrue((self.o["filed"] or {}).get("ok"), "PREMISE: the two-session filing did not file: %r" % self.o["filed"])
        looks = (self.o["fileRow"] or {}).get("looks") or []
        self.assertEqual(sorted(l.get("at") for l in looks), [ISO, "2025-10-28T01:00:00.000Z"],
                         "the filing row dropped its looks' capture times: %r" % looks)


RED_PROOF = [
    {"why": "REG-2890 - a photo with no clock is dated now",
     "file": "bible.html",
     "find": "    return (typeof lm === 'number' && isFinite(lm) && lm > 0) ? new Date(lm).toISOString() : null;\n",
     "replace": "    return (typeof lm === 'number' && isFinite(lm) && lm > 0) ? new Date(lm).toISOString() : new Date().toISOString();\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2890 - a photo's look loses its capture time",
     "file": "bible.html",
     "find": "    if (cap) look.at = cap;\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2890 - a photo's receipt loses its capture time, so the owned door measures it at arrival",
     "file": "bible.html",
     "find": "    if (cap) r.ts = cap;   /* the receipt's read time is when the picture was taken */\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2890 - the door drops each file's time on the way to the witness",
     "file": "bible.html",
     "find": "window._vaultPhotoWitness(fname, opts, _capOf(fname))",
     "replace": "window._vaultPhotoWitness(fname, opts, null)",
     "matches": 1, "needs": "node"},
    {"why": "REG-2891 - a live look is dated by when the read landed, not when the frame was taken",
     "file": "bible.html",
     "find": "    var cap = (typeof rd.captureTs === 'number' && isFinite(rd.captureTs) && rd.captureTs > 0) ? new Date(rd.captureTs).toISOString() : null;\n",
     "replace": "    var cap = (typeof rd.ts === 'number' && isFinite(rd.ts) && rd.ts > 0) ? new Date(rd.ts).toISOString() : null;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2891 - the witness gate drops a look's capture time",
     "file": "bible.html",
     "find": "      if (isFinite(_kat) && _kat > 0) _kept.at = new Date(_kat).toISOString();\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2891 - the filing row drops its looks' capture times",
     "file": "bible.html",
     "find": "        if (k.at) lk.at = k.at;   /* REG-2891 capture time */\n",
     "replace": "",
     "matches": 1, "needs": "node"},
]


if __name__ == "__main__":
    unittest.main()

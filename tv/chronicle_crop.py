# chronicle_crop.py — v1901, ONE CROP FOR BOTH LANES.
#
# WHY THIS FILE EXISTS. The Chronicle is read by two lanes so that agreement between them is
# evidence. That argument holds only if the two lanes are looking at THE SAME PIXELS — and they
# were not. The Claude lane has cropped to the list band since v1780; the Grok lane was handed the
# whole 2940x1912 desktop grab, every time, and nothing anywhere recorded that difference.
#
# v1780's own measurement, on six frames of his thorough reel, same reader, same day:
#
#     full frame : 0/6 pages read, 0 names, six "no-found-state" refusals
#     list crop  : 5/6 pages read, 17 names, one refusal
#
# ⚠ AND THE OPPOSITE MEASUREMENT EXISTS TOO, so this file does not claim the crop is simply better.
# v1829 measured one frame the sweep had refused twice and found the FULL frame read it fine — and
# the Grok lane read it fine full-frame as well (conf 0.88, six names). Both measurements are real
# and they are in tension; the cause of the transience is still open. What is NOT in tension is
# that a second witness handed different pixels is a weaker witness than one handed the same, and
# that nobody could tell which had happened, because it was never written down.
#
# So this file does two things and refuses to guess at a third:
#   1. ONE crop, called by both lanes, so a change to the framing moves both.
#   2. The framing each lane actually read is STAMPED onto the page, so the next disagreement is
#      attributable instead of mysterious. [[unknown-stays-unknown]]
#
# It never writes into the repo — the crop goes to a temp file — and it degrades to the full frame
# on any failure, so it can only ever cost a read, never lose one.
import os
import tempfile

CROP = "crop"
FULL = "full"


def list_crop(image_path):
    """Return (path_to_read, framing). Falls back to the full frame on ANY failure.

    The band and its aspect correction live in chronicle_template, which measured them on his own
    calibration film — this function must never carry a second copy of those numbers.
    """
    ap = os.path.abspath(str(image_path or ""))
    if not os.path.isfile(ap):
        return ap, FULL
    try:
        import chronicle_template as _ct
        from PIL import Image as _Im
        im = _Im.open(ap).convert("RGB")
        w, h = im.size
        band = _ct.LIST_BAND
        try:
            band, _ = _ct._scale_band_for_aspect(_ct.LIST_BAND, float(w) / float(h))
        except Exception:
            pass
        c = im.crop((int(w * band[0]), int(h * band[1]), int(w * band[2]), int(h * band[3])))
        if c.width > 200 and c.height > 200:
            cp = os.path.join(tempfile.gettempdir(), "tvd_chron_crop_%d.jpg" % os.getpid())
            c.save(cp, quality=94)
            return cp, CROP
    except Exception:
        pass
    return ap, FULL


def crop_answer_refused(raw, ledger_lane=True):
    """Is a CROPPED read's answer refused, in every shape a refusal actually arrives in?

    v1829 — THE HALF THAT WAS MISSING. Both crop routes retried the full frame on `not raw`, which
    catches only a crop that returned NOTHING. A crop that returns a well-formed
    `{"stateVisible": false}` is TRUTHY, so the retry never fired, and a refusal is by far the
    likelier shape of a bad read than a crash. The comment on both routes promised "cropping can
    only add reads, never remove one"; with `not raw` that promise was false.

    ⚠ WHAT THIS DOES **NOT** EXPLAIN — recorded because the first version of this docstring got it
    wrong, confidently, and a wrong mechanism sends the next person to the wrong subsystem. One
    frame was recorded `no-found-state` by the sweep on two separate passes. I wrote that the CROP
    FRAMING was blinding the reader. Then I measured the crop alone on that exact frame: it reads
    the page correctly. So does the full frame, and so does the Grok lane. Same image, same prompt,
    same PROMPT_VER: refused twice inside the sweep, read correctly three times out of three by
    hand. The framing is not the variable and the readers are not the variable. What differs is
    that the sweep reads through the worker pool under concurrency, which makes a transient,
    load-shaped degradation the leading hypothesis — a HYPOTHESIS, not a finding.

    So the honest account: this does not repair the framing, it gives a refused page a SECOND
    ATTEMPT it never got. The cause of the transience stays OPEN.
    """
    if not isinstance(raw, dict) or not raw:
        return True
    if ledger_lane:
        # A refusal IS an answer. Ask whether the answer is USABLE, not whether one arrived.
        # `wrongTab` is included deliberately: a crop that cuts the tab chrome reports the wrong
        # ledger for the same reason it reports no found-state. If the ledger really IS wrong the
        # full frame says so too, and the caller keeps the crop's answer — so this cannot lose one.
        return raw.get("stateVisible") is False or raw.get("wrongTab") is True
    # The vault lane marks its own refusals with `note`. An EMPTY page is not a refusal — a stash
    # tab with nothing in it is a real answer, and retrying every empty page would double the cost
    # of the commonest read there is.
    return bool(raw.get("note"))

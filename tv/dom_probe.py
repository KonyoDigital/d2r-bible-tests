"""JS probe primitives that stop me measuring the wrong thing — one per scar, all from 2026-09-03.

Every DOM probe I wrote tonight was written fresh, and FIVE of them measured something adjacent to
the question. None of the five was a wrong answer about the page; each was a right answer to a
question I had not meant to ask. That is a tooling failure, not an attention failure, so it gets
tooling.

    1. `body *` INCLUDES <script>. Two probes returned source code as if it were rendered text —
       one reported a JS comment as a type-size violation, another named the D2R_BUILD script tag
       as the clipped element.
    2. A CLIP TEST ON AN INLINE ELEMENT IS MEANINGLESS. Inline boxes report clientWidth 0, so
       `scrollWidth > clientWidth` is false no matter how long the text is. I nearly published
       "this element structurally cannot clip" off exactly that.
    3. OCCLUSION HAS A DIRECTION. Sampling an element's own centre and asking elementFromPoint what
       is there tells you what covers IT. I used that twice to "refute" a claim that it covered
       something else.
    4. SELECTING BY TEXT FINDS THE WRONG BOX. Searching for a phrase and taking the first match
       gave me a 183x33 inner div while the thing under discussion was a 925x118 panel.
    5. ASSUMING THE MECHANISM. I checked for a `q-*` rarity class, found zero, and nearly reported
       "no item names are coloured" — the colour arrives through a different class on that surface.
       Ask what it PAINTS, never how you think it is painted.

Each helper below is one of those, fixed. They are JS source strings because the measurement has to
happen in the page. [[feedback-suspect-the-instrument]] [[visual-regression-detector]]
"""

#: Tags whose textContent is SOURCE, not screen. Scar 1.
SKIP_TAGS = "script|style|noscript|template|title"

#: Leaf text nodes that are actually rendered. Use this instead of `body *`.
LEAF_TEXT = """
function __leafText(root){
  var out=[], all=(root||document.body).querySelectorAll('*');
  for (var i=0;i<all.length;i++){
    var e=all[i];
    if (/^(%s)$/i.test(e.tagName)) continue;      // scar 1
    if (e.children.length) continue;
    var t=(e.textContent||'').trim(); if(!t) continue;
    var q=e.getBoundingClientRect(); if(q.width<2||q.height<2) continue;
    var cs=getComputedStyle(e);
    if (cs.visibility==='hidden'||cs.display==='none') continue;
    out.push(e);
  }
  return out;
}
""" % SKIP_TAGS

#: Is this element's text actually cut off? Scar 2 — inline boxes cannot answer the usual way.
CLIPPED = """
function __clipped(e){
  var cs=getComputedStyle(e);
  var hides=/hidden|clip/.test(cs.overflow+cs.overflowX) || /ellipsis/.test(cs.textOverflow);
  if (!hides) return {clipped:false, why:'overflow is visible — this element wraps, it cannot clip itself'};
  var inline = /^inline$/.test(cs.display);
  if (inline) {
    // scar 2: clientWidth is 0 on an inline box, so the usual test is meaningless. Compare the
    // element's own client rects against its parent's content box instead.
    var p=e.parentElement; if(!p) return {clipped:null, why:'inline with no parent — UNKNOWN'};
    var pq=p.getBoundingClientRect(), q=e.getBoundingClientRect();
    return {clipped:(q.right > pq.right + 1), why:'inline box compared to its parent content edge'};
  }
  return {clipped:(e.scrollWidth > e.clientWidth + 1),
          lost:Math.max(0, e.scrollWidth - e.clientWidth), why:'block box, scrollWidth vs clientWidth'};
}
"""

#: Does A cover B? Scar 3 — sample B, and ask whether A is what answers.
COVERS = """
function __covers(a, b){
  var q=b.getBoundingClientRect();
  if (q.width<2||q.height<2) return {covered:null, why:'target has no box — UNKNOWN, not uncovered'};
  var pts=0, hit=0;
  for (var gx=0; gx<5; gx++) for (var gy=0; gy<3; gy++){
    var x=Math.round(q.left+q.width*(gx+0.5)/5), y=Math.round(q.top+q.height*(gy+0.5)/3);
    if (x<0||y<0||x>=innerWidth||y>=innerHeight) continue;
    pts++;
    var top=document.elementFromPoint(x,y);
    if (!top) continue;
    if (a===top || a.contains(top)) hit++;
  }
  // ⚠ a target scrolled below its own container's fold also fails this. Say so rather than
  // reporting occlusion: that exact confusion cost an hour.
  var sc=b.closest('[style*=overflow],*');
  return {covered:hit, of:pts, why:(hit? 'A is topmost over B at these points'
        : 'A never answered at B — either it does not cover B, or B is below its own scroll fold')};
}
"""

#: What does it PAINT? Scar 5 — never infer colour from a class name.
PAINTED = """
function __painted(e){
  var cs=getComputedStyle(e);
  return {color:cs.color, bg:cs.backgroundColor, fontPx:parseFloat(cs.fontSize),
          weight:cs.fontWeight, cls:String(e.className||'')};
}
"""

#: Does a QUOTED string actually exist on the page? Scar 7 — a cold read can quote a sentence
#: that was never there.
QUOTED = """
function __quotedIn(s, bodyText){
  // ⚠ SCAR 7, 2026-09-03. A cold cross-family read reported a line 'cut mid-sentence at the right
  // edge' and QUOTED it. Measured: the item names inside the quote were real and on screen, the
  // connecting phrases were NOT IN THE DOM AT ALL, and the page had ZERO clipped nodes. It had
  // assembled a plausible sentence out of names it could see.
  // Every cold-read prompt says 'quote exact strings', on the assumption that a quote disciplines
  // a claim. It only does if somebody checks it. This is that check.
  var norm = function(t){ return String(t||'').replace(/\\s+/g,' ').trim().toLowerCase(); };
  var needle = norm(s);
  if (!needle) return {exists:null, why:'empty quote — nothing to check'};
  // ⚠⚠ THE TEXT MUST COME FROM THE STATE THAT WAS PHOTOGRAPHED, NOT A FRESH LOAD.
  // Found on this helper's FIRST REAL USE: I checked three strings a cold read had quoted and got
  // "Fleshrender — NOT on the page at all", an hour after measuring that exact element painting
  // #c7b377. The page had simply re-rendered a rotating list between the screenshot and the check.
  // A quote-checker that loads the page again is answering about a DIFFERENT page, which is the
  // same class of error the rest of this file exists to stop — the right answer to the wrong
  // question. Callers pass the innerText captured ALONGSIDE the screenshot; the no-argument form
  // falls back to "right now" and SAYS so.
  var body = norm(bodyText != null ? bodyText
                                   : (document.body.innerText || document.body.textContent));
  var against = (bodyText != null) ? 'the captured page text' : 'the page AS IT IS NOW (not the '
              + 'state that was photographed — pass the captured text to be sure)';
  if (body.indexOf(needle) >= 0) return {exists:true, against:against, why:'found verbatim in ' + against};
  // a partial match is the interesting case: real fragments stitched into an unreal sentence
  var words = needle.split(' ').filter(function(w){ return w.length > 3; });
  var found = words.filter(function(w){ return body.indexOf(w) >= 0; });
  return {exists:false, against:against,
          fragmentsPresent: found.length, fragmentsTotal: words.length,
          missing: words.filter(function(w){ return body.indexOf(w) < 0; }).slice(0, 8),
          why: (found.length && found.length < words.length)
            ? 'NOT on the page as quoted — some words appear separately, which is what a stitched '
              + 'sentence looks like. Treat the claim as unverified until re-quoted.'
            : 'NOT on the page at all'};
}
function __quoted(s){ return __quotedIn(s, null); }   // convenience: checks NOW, and says so
"""

#: Every helper, ready to prepend to a probe.
PRELUDE = LEAF_TEXT + CLIPPED + COVERS + PAINTED + QUOTED


def prelude():
    """-> str. Prepend to any tab.ev() body to get the corrected primitives."""
    return PRELUDE


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    print(__doc__)
    print("helpers: __leafText(root) · __clipped(el) · __covers(a,b) · __painted(el) · __quoted(str)")
    print("prelude is %d chars" % len(PRELUDE))

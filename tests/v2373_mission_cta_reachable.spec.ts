import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v2373 (test-only) — CAN HE ACTUALLY CLICK "Do this now"?
 *
 * A cold cross-family look at v2371 read the taskforce render and said the overlay "wholly covers
 * the lower portion of the MISSION BRIEF section and the buttons below it (including parts of
 * 'Do this now', 'Pin mission')". It named the DOCK as the cover. It is not the dock: with the
 * button scrolled into view at 1440x1000, elementFromPoint at its centre answers #inbox-sticky
 * (position:sticky, z-index:60).
 *
 * ⚠ WHY THIS LIVES HERE AND NOT IN THE PYTHON HARNESS. I could not settle it on the Mac. Under
 * CDP `Emulation.setDeviceMetricsOverride`, document.scrollingElement reports scrollHeight 2206
 * against clientHeight 1000 with html/body overflow `visible` — and setting scrollTop to 300
 * yields 0. The element never moves, so the scan reported "tested=0, NEVER clickable at any
 * scroll position" with an EMPTY coveredBy: an unfalsifiable answer wearing the clothes of a
 * verdict. That is the 27-dead-links shape — a harness that cannot reach its subject reporting
 * the subject as broken — and it is exactly what `feedback-suspect-the-instrument` is about.
 * Playwright drives a real browser that really scrolls, so this is the venue that can answer.
 *
 * THE LAW, and it is deliberately the weak one: a control the user can scroll out from under is
 * NOT unreachable, it is merely somewhere else right now. So this does not demand that the CTA be
 * clear at every scroll position — a sticky panel passing over content is the page working. It
 * demands that there EXISTS a scroll position where the button answers the hit test for itself.
 * If none exists, the button is dead wherever he goes, and that is the defect worth his time.
 *
 * The inbox is seeded so #inbox-sticky carries `.has` — without it the panel is display:none and
 * this case would pass by testing a world where the suspected cover does not exist at all.
 * [[gate-blind-to-unexercised-input]]
 */

const SEED = `(function(){
  localStorage.setItem('d2r_ownerClaim','*');
  localStorage.setItem('d2r_chronicleInbox', JSON.stringify([
    {name:'Shadow Dancer', tier:'grail', gateHeld:true, proposedAt:1,
     gateWhy:'only 1 independent witness'},
    {name:"Razor's Edge", tier:'grail', gateHeld:true, proposedAt:2,
     gateWhy:'only 1 independent witness'}]));
  return 1; })()`;

const OPEN_SESSIONS = `(function(){
  var t=[].slice.call(document.querySelectorAll('.tab[data-tab]'))
        .filter(function(x){ return x.getAttribute('data-tab')==='session'; })[0];
  if(t) t.click();
  try{ window.renderInboxFab && window.renderInboxFab(); }catch(e){}
  return !!t; })()`;

/* Walk the whole scroll range and report, for the named control:
 *   tested  - positions where it was actually on screen (0 means WE never looked at it)
 *   free    - positions where it answered the hit test for itself
 *   covers  - what answered instead, counted by class
 * Reporting `tested` is what makes a zero interpretable instead of a verdict. */
const SCAN = (needle: string) => `(function(){
  var b=[].slice.call(document.querySelectorAll('button,a,[role=button]'))
        .filter(function(x){ return (x.textContent||'').toLowerCase()
                 .indexOf(${JSON.stringify(needle)})>=0; })[0];
  if(!b) return {found:false};
  var doc=Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
  var maxY=Math.max(0, doc-window.innerHeight);
  var tested=0, free=0, first=null, covers={};
  for(var y=0; y<=maxY; y+=40){
    window.scrollTo(0,y);
    var r=b.getBoundingClientRect(), cx=r.left+r.width/2, cy=r.top+r.height/2;
    if(r.width<2||r.height<2) continue;
    if(cy<0||cy>window.innerHeight||cx<0||cx>window.innerWidth) continue;
    tested++;
    var hit=document.elementFromPoint(cx,cy);
    if(hit&&(hit===b||b.contains(hit)||hit.contains(b))){ free++; if(first===null) first=y; }
    else if(hit){ var k=String(hit.className||hit.tagName).split(' ')[0];
                  covers[k]=(covers[k]||0)+1; }
  }
  window.scrollTo(0,0);
  return {found:true, tested:tested, free:free, firstFreeY:first, covers:covers, maxY:maxY};
})()`;

for (const [w, h] of [[1440, 1000], [1120, 900], [901, 900]] as const) {
  test(`the mission CTA is reachable at some scroll position — ${w}x${h}`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: h });
    await page.goto(URL);
    await page.evaluate(SEED);
    await page.goto(URL);                       // reload so the seeded inbox is read at startup
    await page.evaluate(OPEN_SESSIONS);
    await page.waitForTimeout(700);

    // the suspected cover must actually be on screen, or this proves nothing
    const stickyShown = await page.evaluate(`(function(){
      var s=document.getElementById('inbox-sticky');
      if(!s) return 'missing';
      var r=s.getBoundingClientRect();
      return (getComputedStyle(s).display!=='none' && r.height>2) ? 'shown' : 'hidden'; })()`);
    expect(stickyShown, 'the inbox sticky is not on screen, so this case would pass without ever '
      + 'exercising the element suspected of covering the CTA').toBe('shown');

    const r: any = await page.evaluate(SCAN('do this now'));
    expect(r.found, 'no "Do this now" control exists on the Sessions tab').toBe(true);
    expect(r.tested, 'the scan never saw the CTA on screen at ANY scroll position — that is a '
      + 'HARNESS fault, not a verdict about the button').toBeGreaterThan(0);
    expect(r.free, `"Do this now" answered the hit test at NONE of ${r.tested} scroll positions; `
      + `covered by ${JSON.stringify(r.covers)}. A control that is covered wherever he scrolls is `
      + `dead, not merely somewhere else.`).toBeGreaterThan(0);
  });
}

/* The v2369 law, in a browser that really lays out: the inbox panel must not run under the dock.
 * The Python render gate asserts this via elementFromPoint on the panel's own buttons; this
 * asserts the GEOMETRY that makes it true, so a regression is caught even if the hit test is
 * confused by something new sitting on top. 375px is the width where it actually broke. */
for (const [w, h] of [[375, 800], [560, 800], [700, 900]] as const) {
  test(`the inbox panel stays above the dock — ${w}x${h}`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: h });
    await page.goto(URL);
    await page.evaluate(SEED);
    await page.goto(URL);
    await page.evaluate(OPEN_SESSIONS);
    await page.waitForTimeout(700);

    const m: any = await page.evaluate(`(function(){
      var p=document.getElementById('inbox-sticky'), d=document.getElementById('control-dock');
      if(!p||!d) return {err:'missing '+(!p?'panel':'dock')};
      if(getComputedStyle(p).display==='none') return {err:'the panel is not shown'};
      var pr=p.getBoundingClientRect(), dr=d.getBoundingClientRect();
      return {panelBottom:Math.round(pr.bottom), dockTop:Math.round(dr.top),
              dockH:getComputedStyle(document.documentElement)
                      .getPropertyValue('--dock-h').trim()}; })()`);
    expect(m.err, `could not measure: ${m.err}`).toBeUndefined();
    expect(m.panelBottom,
      `the inbox panel runs to ${m.panelBottom} while the fixed dock starts at ${m.dockTop} `
      + `(--dock-h=${m.dockH}). Its last rows are painted under the dock, which is what v2369 `
      + `fixed by correcting a static that reserved 118px for a 142-219px dock.`)
      .toBeLessThanOrEqual(m.dockTop);
  });
}

import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v2130 — #108. NOTHING EVER HOVERED.
//
// The tooltip work has three shipped fixes and every guard on them is a SOURCE GREP:
//   #107 (v2119) an anchor matching ARTTIP_SEL *and* carrying a native `title` drew the rich card
//        with the OS grey box on top, because the defer returned before borrowing the title
//   #130 (v2121) the borrowed title was given back on every child-to-child move INSIDE the anchor,
//        so the grey box flickered back mid-hover
//   v2114     a borrowed title must survive a re-render and be given back on release
//
// TestV2109/TestV2114/TestV2122 pin the SHAPE of all three. None of them can see a hover, and #108
// is right that a defer pinned by grep is a defer that cannot go red for the thing it is about.
//
// Konyo's words on the defect these exist for: "i want hdart only not double one is rendering a
// regular OS message box."
//
// ⚠ MEASURED WHILE WRITING THIS: not one anchor on the default board carries BOTH a title and
// children, so the case cannot be found — it has to be CONSTRUCTED on an anchor whose card really
// opens. That is why this spec picks a live anchor first and adds the second attribute to it,
// rather than inventing an element the lane may not even bind.

test('a dual-attribute anchor shows the rich card and NOT the OS box, across a child move', async ({ page }) => {
  await page.goto(URL);
  await page.waitForFunction(() => !!(window as any).ARTTIP_SEL && !!document.getElementById('arttip'));

  const r = await page.evaluate(() => {
    const w = window as any;
    const tip = document.getElementById('arttip') as HTMLElement;
    const all = Array.from(document.querySelectorAll(w.ARTTIP_SEL)) as HTMLElement[];
    const fire = (t: EventTarget, type: string, related?: EventTarget | null) =>
      t.dispatchEvent(new MouseEvent(type, { bubbles: true, relatedTarget: related as any }));

    for (const host of all.filter(n => n.offsetParent).slice(0, 60)) {
      fire(host, 'mouseover'); fire(host, 'mousemove');
      if (!tip.classList.contains('on')) { fire(host, 'mouseout', document.body); continue; }
      fire(host, 'mouseout', document.body);

      // this anchor's card really opens — now give it the SECOND attribute and a child
      host.setAttribute('title', 'THE OS BOX TEXT');
      if (!host.children.length) host.appendChild(document.createElement('b'));
      const kid = host.querySelector('*') as HTMLElement;

      fire(host, 'mouseover'); fire(host, 'mousemove');
      const enter = { title: host.getAttribute('title'), held: host.getAttribute('data-tip-held'),
                      card: tip.classList.contains('on') };
      fire(host, 'mouseout', kid);                 // #130: moving onto its OWN child
      const child = { title: host.getAttribute('title'), held: host.getAttribute('data-tip-held'),
                      card: tip.classList.contains('on') };
      fire(host, 'mouseout', document.body);       // and now genuinely leaving
      const leave = { title: host.getAttribute('title'), held: host.getAttribute('data-tip-held'),
                      card: tip.classList.contains('on') };
      return { anchor: host.className || host.tagName, enter, child, leave };
    }
    return null;
  });

  expect(r, 'no anchor on the board opened the rich card at all — this spec measured nothing, '
    + 'which is not the same as the lane working').not.toBeNull();

  // #107 — the native box must be SUPPRESSED while the rich card is up, and the text kept safe
  expect(r!.enter.card, 'the rich card did not open on a dual-attribute anchor').toBe(true);
  expect(r!.enter.title, 'the native title is still on the element, so the OS grey box opens ON TOP '
    + 'of the rich card — the exact doubling he reported').toBeNull();
  expect(r!.enter.held, 'the title was removed but not parked, so it can never be given back')
    .toBe('THE OS BOX TEXT');

  // #130 — leaving a CHILD is not leaving the anchor
  expect(r!.child.card, 'the card was dropped when the pointer moved onto the anchor\'s own child')
    .toBe(true);
  expect(r!.child.title, 'the borrowed title was handed back mid-hover, so the OS box flickers '
    + 'straight back on the same anchor').toBeNull();

  // and no strand: a real exit gives it back
  expect(r!.leave.card, 'the card stayed up after the pointer genuinely left').toBe(false);
  expect(r!.leave.title, 'the borrowed title was NOT given back on a real exit — the element has '
    + 'permanently lost its tooltip text').toBe('THE OS BOX TEXT');
  expect(r!.leave.held, 'data-tip-held was left behind, so the next hover reads a stale steal')
    .toBeNull();
});

/**
 * /api/d2jsp_quote — a public reading of forum gold for one item.
 *
 * The bible cannot read forums.d2jsp.org from the browser (no CORS). This
 * function fetches the softcore non-ladder board search and returns the
 * middle fg price only when the page actually contains prices for that item.
 * A challenge page, a failed fetch, or a page with no fg number returns
 * fg:null. It never substitutes a remembered or default price.
 *
 * Board 268 is the forum moderators named as D2:R softcore non-ladder
 * trading (the board that is not the ladder board).
 */

const CORS = {
  'Access-Control-Allow-Origin': 'https://bull-4-u.com',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};
const BOARD = 268;

function json(body, status) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
      ...CORS,
    },
  });
}

/* ⟦D2JSP QUOTE BEGIN⟧ */
function d2jspPrices(text, itemName) {
  var name = String(itemName || '').trim().toLowerCase();
  if (!name) return [];
  var chunks = String(text || '').split(/\n{2,}|<br\s*\/?>|<\/p>|<\/div>|topic\.php/i);
  var nums = [];
  chunks.forEach(function (chunk) {
    if (chunk.toLowerCase().indexOf(name) < 0) return;
    var re = /(\d+(?:\.\d+)?)\s*fg\b/ig;
    var m;
    while ((m = re.exec(chunk))) {
      var n = Number(m[1]);
      if (n > 0 && n < 1000000) nums.push(n);
    }
  });
  return nums;
}

function d2jspMedian(nums) {
  if (!nums || !nums.length) return null;
  var s = nums.slice().sort(function (a, b) { return a - b; });
  var mid = Math.floor(s.length / 2);
  if (s.length % 2) return s[mid];
  return Math.round((s[mid - 1] + s[mid]) / 2);
}

function d2jspRead(html, item, readAt) {
  var text = String(html || '');
  var base = { item: String(item || ''), fg: null, n: 0, readAt: readAt, reason: 'unread', board: BOARD };
  if (!text || /Just a moment/i.test(text) || /cf-browser-verification/i.test(text)) return base;
  var nums = d2jspPrices(text, item);
  var fg = d2jspMedian(nums);
  if (fg == null) {
    base.reason = 'no prices';
    return base;
  }
  return { item: String(item || ''), fg: fg, n: nums.length, readAt: readAt, reason: 'read', board: BOARD };
}
/* ⟦D2JSP QUOTE END⟧ */

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS });
}

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const item = (url.searchParams.get('item') || '').trim().slice(0, 80);
  const readAt = new Date().toISOString();
  if (!item) return json({ item: '', fg: null, n: 0, readAt: readAt, reason: 'no item', board: BOARD });
  const search = 'https://forums.d2jsp.org/search.php?sr=posts&search_keywords='
    + encodeURIComponent(item) + '&fid%5B%5D=' + BOARD;
  try {
    const r = await fetch(search, {
      headers: {
        'User-Agent': 'KonyoD2RBible/1.0 (+https://bull-4-u.com/d2r/)',
        Accept: 'text/html',
      },
    });
    if (!r.ok) return json(d2jspRead('', item, readAt));
    const html = await r.text();
    return json(d2jspRead(html.slice(0, 200000), item, readAt));
  } catch (e) {
    return json(d2jspRead('', item, readAt));
  }
}

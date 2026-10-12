/**
 * /api/d2jsp_quote — a public reading of forum gold for one item.
 *
 * The bible cannot read forums.d2jsp.org from the browser (no CORS). This
 * function fetches the Switch Ladder board search and returns the middle
 * fg price only when a line that names the item carries an fg number.
 * A challenge page, a login wall, a failed fetch, or a page with no such
 * line returns fg:null. It never substitutes a remembered or default price.
 *
 * Board 243 is D2:R Switch Ladder Trading, the board that search was on.
 * Posts still go to board 268. The two are different economies.
 */

const CORS = {
  'Access-Control-Allow-Origin': 'https://bull-4-u.com',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};
const BOARD = 243;

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
var D2JSP_QUOTE_BOARD = 243;

function d2jspFoldPrice(text) {
  return String(text || '').replace(/['\u2018\u2019\u02BC`]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
}

function d2jspPrices(text, itemName) {
  var name = d2jspFoldPrice(itemName);
  if (!name) return [];
  var plain = String(text || '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(?:p|div|tr|li|h\d)>/gi, '\n')
    .replace(/<[^>]+>/g, ' ');
  var nums = [];
  plain.split('\n').forEach(function (line) {
    if (d2jspFoldPrice(line).indexOf(name) < 0) return;
    var re = /(\d+(?:\.\d+)?)\s*fg\b/ig;
    var m;
    while ((m = re.exec(line))) {
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

function d2jspSpan(nums) {
  if (!nums || !nums.length) return { low: null, high: null };
  var s = nums.slice().sort(function (a, b) { return a - b; });
  return { low: s[0], high: s[s.length - 1] };
}

function d2jspRead(html, item, readAt) {
  var text = String(html || '');
  var base = {
    item: String(item || ''), fg: null, low: null, high: null,
    n: 0, readAt: readAt, reason: 'unread', board: D2JSP_QUOTE_BOARD
  };
  if (!text || /Just a moment/i.test(text) || /cf-browser-verification/i.test(text)) return base;
  if (/do not have permission/i.test(text) || /not currently logged in/i.test(text)) {
    base.reason = 'need-login';
    return base;
  }
  var nums = d2jspPrices(text, item);
  var fg = d2jspMedian(nums);
  if (fg == null) {
    base.reason = 'no prices';
    return base;
  }
  var span = d2jspSpan(nums);
  return {
    item: String(item || ''), fg: fg, low: span.low, high: span.high,
    n: nums.length, readAt: readAt, reason: 'read', board: D2JSP_QUOTE_BOARD
  };
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
  const keywords = String(item).replace(/['\u2018\u2019\u02BC`]/g, '');
  const search = 'https://forums.d2jsp.org/search.php?sr=posts&search_keywords='
    + encodeURIComponent(keywords) + '&fid%5B%5D=' + BOARD;
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

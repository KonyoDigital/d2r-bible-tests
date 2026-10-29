/**
 * /api/d2jsp_quote — a public reading of forum gold for one item.
 *
 * The bible cannot read forums.d2jsp.org from the browser (no CORS). This
 * function fetches the Switch Ladder board search and returns the middle
 * fg price only when a line that names the item carries an fg number.
 * A challenge page, a login wall, a failed fetch, or a page with no such
 * line returns fg:null. It never substitutes a remembered or default price.
 *
 * Board 268 is D2:R RotW Softcore Trading (non-ladder), the board the search reads (v3843; it was 243, Switch Ladder).
 * Posts still go to board 268. The two are different economies.
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
var D2JSP_QUOTE_BOARD = 268;
/* v3843 - ONLY RECENT POSTS PRICE AN ITEM. A price line counts only under a post dated within the last
   D2JSP_QUOTE_WINDOW_DAYS days of the reading (its readAt, else now) - a rolling window, so prices do not stop on
   Jan 1. A page that dates nothing, or only older posts, reads 'no prices' and the desk says unknown. */
var D2JSP_QUOTE_WINDOW_DAYS = 120;
var D2JSP_DAY_MS = 86400000;

/* v3843 - THE D2JSP LEXICON: the trade forum's own short names (its guides' slang and notation, never their prices).
   Each item maps to the words traders write for it; the search asks with the first, and a price line naming any
   form counts. */
var D2JSP_SLANG = {
  "Annihilus": ["anni"], "Hellfire Torch": ["torch"], "Gheed's Fortune": ["gheeds"],
  "Harlequin Crest": ["shako"], "Griffon's Eye": ["gface", "griffons"], "Crown of Ages": ["coa"],
  "Arreat's Face": ["arreats"], "Andariel's Visage": ["andy"], "Herald of Zakarum": ["hoz"],
  "Jalal's Mane": ["jalals"], "Stone of Jordan": ["soj"],
  "Bul-Kathos' Wedding Band": ["bk", "bk ring"], "Raven Frost": ["raven"], "Mara's Kaleidoscope": ["maras"],
  "Highlord's Wrath": ["highlords"], "Crown of Thieves": ["cot"], "Nightwing's Veil": ["nightwing", "veil"],
  "Mang Song's Lesson": ["mang song", "mangs"], "Eschuta's Temper": ["eschutas"], "Death's Fathom": ["fathom"],
  "Call to Arms": ["cta"], "Breath of the Dying": ["botd"], "Heart of the Oak": ["hoto"],
  "Hand of Justice": ["hoj"], "Enigma": ["nigma"], "Infinity": ["infy"], "Insight": [],
  "Grief": [], "Spirit": [], "Heart of Winter": [], "Fortitude": ["forti"],
  "Stormshield": ["storm shield"], "Death's Web": ["deathweb"], "Titan's Revenge": ["titans"],
  "Windforce": ["wf"], "Eaglehorn": [], "War Traveler": ["war travs", "wartravs"], "Waterwalk": [],
  "Sandstorm Trek": ["treks"], "Shadow Dancer": ["sdancer"], "Gore Rider": ["gores"],
  "Steelrend": ["rends"], "Magefist": ["mages"], "Dracul's Grasp": ["dracs"], "Bloodfist": ["bfists"],
  "Chance Guards": ["chancies"], "Arachnid Mesh": ["arach", "arachnid"], "Verdungo's Hearty Cord": ["dungo"],
  "Thundergod's Vigor": ["tgod"], "String of Ears": ["soe"], "Nosferatu's Coil": ["nos", "nosferatus"],
  "The Oculus": ["occy", "oculus"], "Spirit Ward": [],
  "Tyrael's Might": ["tyraels"], "Skullder's Ire": ["skullders"], "Vipermagi": ["viper", "vmagi"],
  "Shaftstop": ["shaft"], "Leviathan": ["levi"], "Guardian Angel": ["ga"], "Blackhorn's Face": ["bhades"],
  "Gladiator's Bane": ["glads"], "Templar's Might": ["templars"], "Atma's Scarab": ["atmas"],
  "Metalgrid": ["mgrid"], "Seraph's Hymn": ["seraphs"],
  "Doombringer": ["doom"], "Death Cleaver": ["dc"], "Executioner's Justice": ["ej"],
  "The Reaper's Toll": ["reapers"], "Stormlash": [], "Tomb Reaver": ["reaver"],
  "Grandfather": ["gf sword"], "Azurewrath": ["azure"], "Lightsabre": ["lsabre"],
  "Hellslayer": [], "Messerschmidt's Reaver": ["messer"], "Rainbow Facet": ["facet"]
};

/* the guides' notation for mods: the short word and the plain words a seller means by it */
var D2JSP_NOTATION = {
  "@": "all resistances", "os": "open sockets", "eth": "ethereal", "ed": "enhanced damage", "dr": "damage reduced",
  "mdr": "magic damage reduced", "fcr": "faster cast rate", "fhr": "faster hit recovery", "frw": "faster run walk",
  "ias": "increased attack speed", "ll": "life leech", "ml": "mana leech", "lpl": "life per level",
  "lpk": "life per kill", "mpk": "mana per kill", "cb": "crushing blow", "gc": "grand charm", "lc": "large charm",
  "sc": "small charm", "perf": "perfect roll", "p": "perfect roll", "upd": "upgraded", "rand": "random roll",
  "unid": "unidentified", "igg": "in game gold", "pc": "poison charm", "pnb": "poison and bone",
  "cr": "cold resist", "fr": "fire resist", "lr": "lightning resist", "pr": "poison resist",
  "mf": "magic find", "gf": "gold find", "rep": "replenish", "res": "resistances", "req": "requirement",
  "str": "strength", "dex": "dexterity", "ar": "attack rating", "def": "defense", "dmg": "damage",
  "ow": "open wounds", "ls": "life stolen", "sorc": "sorceress", "sin": "assassin", "zon": "amazon",
  "barb": "barbarian", "dru": "druid", "nec": "necromancer", "pala": "paladin"
};

function d2jspSlangOf(itemName) {
  var f = d2jspFoldPrice(itemName);
  for (var k in D2JSP_SLANG) {
    if (Object.prototype.hasOwnProperty.call(D2JSP_SLANG, k) && d2jspFoldPrice(k) === f) return D2JSP_SLANG[k].slice();
  }
  return [];
}

/* the simplified name: no apostrophes, no leading "The", no "'s" */
function d2jspSimpleName(itemName) {
  return d2jspFoldPrice(String(itemName || '').replace(/['\u2018\u2019\u02BC`]s\b/gi, '')).replace(/^the\s+/, '').replace(/[^a-z0-9 \-]/g, ' ').replace(/\s+/g, ' ').trim();
}

/* the search words like a search box takes them: the slang form when traders have one, else the simplified name;
   every form a price line may name it by rides along in `forms` */
function d2jspSearchWords(itemName) {
  var slang = d2jspSlangOf(itemName), simple = d2jspSimpleName(itemName), full = d2jspFoldPrice(itemName);
  var forms = [];
  [full, simple].concat(slang).forEach(function (w) { if (w && forms.indexOf(w) < 0) forms.push(w); });
  return { query: slang.length ? slang[0] : simple, slang: slang, simple: simple, forms: forms };
}

/* the notation parser: "Anni 20/20/10 eth 2os @30 perf" -> slash tuples, socket count, ethereal, all res, perfect,
   upgraded, random, and each known short word in plain words */
function d2jspNotation(text) {
  var t = String(text || '');
  var out = { tuples: [], sockets: null, eth: false, perfect: false, upgraded: false, random: false, allRes: null, words: [] };
  var m, re = /(\d+(?:\/\d+)+)/g;
  while ((m = re.exec(t))) out.tuples.push(m[1].split('/').map(Number));
  if ((m = /\b(\d)\s*os\b/i.exec(t))) out.sockets = Number(m[1]);
  if ((m = /@\s*(\d+)|(\d+)\s*@/.exec(t))) out.allRes = Number(m[1] || m[2]);
  out.eth = /\beth\b/i.test(t);
  out.perfect = /\bperf(?:ect)?\b/i.test(t);
  out.upgraded = /\bup'?d\b|\bupped\b/i.test(t);
  out.random = /\brand\b/i.test(t);
  String(t).toLowerCase().replace(/'/g, '').split(/[^a-z@]+/).forEach(function (w) {
    if (w && Object.prototype.hasOwnProperty.call(D2JSP_NOTATION, w) && out.words.indexOf(D2JSP_NOTATION[w]) < 0) out.words.push(D2JSP_NOTATION[w]);
  });
  return out;
}

var D2JSP_MONTHS = 'jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec';
/* the UTC day (ms) a line dates its post by, or null: "Oct 12, 2026", "12 Oct 2026", "2026-10-12", or Today /
   Yesterday (counted from nowMs) */
function d2jspLineDate(line, nowMs) {
  var t = String(line || ''), mon = D2JSP_MONTHS.split('|');
  var m = new RegExp('\\b(' + D2JSP_MONTHS + ')[a-z]*\\.?\\s+(\\d{1,2})(?:st|nd|rd|th)?,?\\s+(20\\d\\d)\\b', 'i').exec(t);
  if (m) return Date.UTC(Number(m[3]), mon.indexOf(m[1].toLowerCase()), Number(m[2]));
  m = new RegExp('\\b(\\d{1,2})\\s+(' + D2JSP_MONTHS + ')[a-z]*\\.?,?\\s+(20\\d\\d)\\b', 'i').exec(t);
  if (m) return Date.UTC(Number(m[3]), mon.indexOf(m[2].toLowerCase()), Number(m[1]));
  m = /\b(20\d\d)-(\d\d)-(\d\d)\b/.exec(t);
  if (m) return Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  if (/\btoday\b/i.test(t)) return nowMs;
  if (/\byesterday\b/i.test(t)) return nowMs - D2JSP_DAY_MS;
  return null;
}
/* the reading's own clock: its readAt when that is a time, else now */
function d2jspNowMs(readAt) {
  var t = Date.parse(String(readAt || ''));
  return isFinite(t) ? t : Date.now();
}
/* a post dated `when` is recent for a reading at nowMs: inside the window, and not in the future past a day of clock skew */
function d2jspRecent(when, nowMs) {
  return when != null && when <= nowMs + D2JSP_DAY_MS && when >= nowMs - D2JSP_QUOTE_WINDOW_DAYS * D2JSP_DAY_MS;
}

function d2jspFoldPrice(text) {
  return String(text || '').replace(/['\u2018\u2019\u02BC`]/g, '').toLowerCase().replace(/\s+/g, ' ').trim();
}

/* v3843 - THE FG AMOUNTS ON A LINE, LARGE ONES INCLUDED. "300fg", "300 fg", "1,500 fg", "30,000fg", "1.5k", "25k fg",
   "10K". A comma groups thousands (before this "1,500 fg" read as 500). A bare "k" amount counts: the trade forum writes
   tens-of-thousands prices that way. Anything at or above 10,000,000 is not a price. */
function d2jspFgAmounts(line) {
  var out = [], m, re = /(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(k\b|k(?=\s*fg)|)\s*(fg\b)?/ig;
  while ((m = re.exec(String(line || '')))) {
    if (!m[2] && !m[3]) continue;
    var n = Number(m[1].replace(/,/g, ''));
    if (m[2]) n = Math.round(n * 1000);
    if (n > 0 && n < 10000000) out.push(n);
  }
  return out;
}

function d2jspPrices(text, itemName, nowMs) {
  if (nowMs == null) nowMs = Date.now();
  var forms = d2jspSearchWords(itemName).forms;
  if (!forms.length) return [];
  var plain = String(text || '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(?:p|div|tr|li|h\d)>/gi, '\n')
    .replace(/<[^>]+>/g, ' ');
  var nums = [], when = null;
  plain.split('\n').forEach(function (line) {
    var d = d2jspLineDate(line, nowMs);
    if (d != null) when = d;
    /* v3843 - a price counts only under a recently dated post */
    if (!d2jspRecent(when, nowMs)) return;
    var folded = ' ' + d2jspFoldPrice(line).replace(/[^a-z0-9]+/g, ' ') + ' ';
    var named = forms.some(function (f) { return folded.indexOf(' ' + f.replace(/[^a-z0-9]+/g, ' ').trim() + ' ') >= 0; });
    if (!named) return;
    d2jspFgAmounts(line).forEach(function (n) { nums.push(n); });
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
  var nums = d2jspPrices(text, item, d2jspNowMs(readAt));
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
  const keywords = d2jspSearchWords(item).query || String(item).replace(/['\u2018\u2019\u02BC`]/g, '');
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

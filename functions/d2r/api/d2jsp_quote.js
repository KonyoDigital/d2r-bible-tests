/**
 * /d2r/api/d2jsp_quote — same reading as /api/d2jsp_quote, under the app prefix.
 * The board lives at /d2r/, so a relative fetch must hit this path.
 */
export { onRequestGet, onRequestOptions } from '../../api/d2jsp_quote.js';

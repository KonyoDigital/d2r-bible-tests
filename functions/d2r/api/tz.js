/**
 * /d2r/api/tz — same payload as /api/tz, under the app prefix.
 *
 * v1710: middleware used to 401 this path (only pathname === '/api/tz' was
 * ungated). The board lives at /d2r/, so a relative `api/tz` fetch — or a
 * relay that "fixed" the upstream to match the app prefix — hit the gate
 * and the console painted "could not reach the live site" while the public
 * function was 200. This file is the same handler, not a second tracker.
 */
export { onRequestGet, onRequestOptions } from '../../api/tz.js';

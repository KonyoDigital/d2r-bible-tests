// Shared network-stub fixture (audit 2026-06-12, hygiene item B-2).
// Specs that load external diablo2.io art AND assert "no console errors" red
// intermittently on a slow/offline link (9× net::ERR_INTERNET_DISCONNECTED in
// one full run; v114 + v136 flaked). This fixture fulfills every diablo2.io
// request with a 1×1 PNG so image loads are deterministic and silent.
// NOTE: safe for the d2art-failed assertions — they all check the onerror
// ATTRIBUTE markup or assert the failed class is ABSENT, never that a real
// network failure occurred.
import { test as base } from '@playwright/test';

const PNG_1X1 = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64'
);

export const test = base.extend({
  page: async ({ page }, use) => {
    await page.route('**://diablo2.io/**', (r) =>
      r.fulfill({ status: 200, contentType: 'image/png', body: PNG_1X1 })
    );
    await use(page);
  },
});

export { expect } from '@playwright/test';

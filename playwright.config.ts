import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './tests',
  // v684 CI calibration: retries 2 × 180s let ONE failing test burn up to 9 minutes of worker time —
  // that's what pushed Routine I's red shard past the job cap, where SIGKILL destroyed the blob report
  // and the failing specs stayed nameless for 40 runs. In CI a broken spec now costs at most 4 min
  // (2 × 120s) and the shard finishes and REPORTS. Local behavior is unchanged.
  timeout: process.env.CI ? 120000 : 180000,
  expect: { timeout: 10000 },
  fullyParallel: false,
  workers: 2,
  retries: process.env.CI ? 1 : 2,
  // Exit gracefully BELOW the workflow's timeout-minutes so the blob report always gets written:
  // a global stop reports "did not run" counts; the runner's SIGKILL reports nothing.
  globalTimeout: process.env.CI ? 45 * 60 * 1000 : undefined,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'file://' + __dirname + '/bible.html',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // v1491 — SAY WHICH WORLD THE SUITE IS TESTING. devices['Desktop Chrome'] ships a
        // "Windows NT 10.0" user agent. The board derives its storage world by joining EVERY
        // platform signal (userAgentData.platform + navigator.platform + userAgent) and asking
        // /mac|iphone|ipad|ipod/ — so on Konyo's Mac the platform probes still say "MacIntel" and
        // the world is `mac` (bare keys), while on the Linux CI runner nothing says mac and the
        // world becomes the isolated `W·` COUSIN world (W·d2r_wishlist, W·d2r_muleAssign, …).
        // 105 spec files address the BARE keys, so the suite was silently exercising a different
        // world than it was written for: 100 spec files red on CI, every one of them green on the
        // Mac, with the app innocent each time (REG-082). The subject of this suite is Konyo's Mac
        // world, so declare it instead of inheriting it from whichever host runs the job. The
        // cousin world keeps its own coverage in v663_machine_shell.spec.ts, which sets the
        // machine by hand and is unaffected by the UA.
        userAgent:
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ' +
          '(KHTML, like Gecko) Chrome/148.0.7778.96 Safari/537.36',
      },
    },
  ],
});

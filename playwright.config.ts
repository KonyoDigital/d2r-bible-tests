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
    /* v1705 — SHARD 2 HAS NEVER REPORTED, AND THE TRACE SETTING IS WHY.
       Measured on two consecutive runs of the same commit: shard 2/6 died in `Upload blob report`
       at 9.2GB and then 8.7GB — "there will be 1 file uploaded", climbing until the runner sent a
       shutdown signal. Not a flake: same shard, same step, same mechanism, twice. So the suite has
       never once returned a COMPLETE verdict; shard 2's specs are unknown, not green.

       `retain-on-failure` RECORDS a trace for every test and throws it away on pass — the recording
       cost is paid by the whole shard, and the shard holding the every-item simulations (which walk
       ~300 uniques and every set piece through a full tick/untick lifecycle) produces gigabytes.
       `on-first-retry` records nothing on the first attempt and traces only the RETRY, which with
       retries:1 is exactly the attempt worth debugging. Strictly lighter, same diagnostic value on
       a real failure.

       This is v684's lesson arriving through a different door: that comment reduced timeouts so a
       red shard would "finish and REPORT" after SIGKILL left failing specs nameless for 40 runs.
       Same principle — a report that cannot be delivered is a report nobody has. Local keeps
       retain-on-failure, where volume costs nothing. */
    trace: process.env.CI ? 'on-first-retry' : 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      // v1710 — --shard splits by FILE COUNT, not duration. The every-item
      // simulations (v645 walks ~300 uniques; v333/v566 recipe+grail sims)
      // plus the 600s audit files made shard 2 finish 64 tests in 45m while
      // its siblings finished ~320 in 15. Peel them into `slow` so the
      // 6-way shard only sees the fast files.
      testIgnore: /(?:^|[\\/])(?:[^\\/]*(?:_sim|simulation)\.spec\.ts|v645_every_item_sim\.spec\.ts|v42_full_ux_audit\.spec\.ts|v43_editorial_audit\.spec\.ts|platform_routing_audit\.spec\.ts|golden_intake\.spec\.ts|v628_exact_fit_gate\.spec\.ts)$/,
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
    // CI (and PW_SLOW=1) only — a bare local `npx playwright test` must not
    // pick these up. The Mac is not a test runner (test-venue).
    ...((process.env.CI || process.env.PW_SLOW)
      ? [{
          name: 'slow',
          testMatch: /(?:^|[\\/])(?:[^\\/]*(?:_sim|simulation)\.spec\.ts|v645_every_item_sim\.spec\.ts|v42_full_ux_audit\.spec\.ts|v43_editorial_audit\.spec\.ts|platform_routing_audit\.spec\.ts|golden_intake\.spec\.ts|v628_exact_fit_gate\.spec\.ts)$/,
          timeout: 600000,
          use: {
            ...devices['Desktop Chrome'],
            userAgent:
              'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ' +
              '(KHTML, like Gecko) Chrome/148.0.7778.96 Safari/537.36',
          },
        }]
      : []),
  ],
});

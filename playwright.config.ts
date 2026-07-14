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
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});

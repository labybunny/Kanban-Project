import { defineConfig, devices } from "@playwright/test";
import path from "node:path";

const repoRoot = path.resolve(__dirname, "..");
const imageName = "pm-mvp-e2e";
const serverPort = 8000;

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  globalTeardown: "./tests/global-teardown.ts",
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: `http://127.0.0.1:${serverPort}`,
    trace: "retain-on-failure",
  },
  webServer: {
    command: `docker build -t ${imageName} "${repoRoot}" && docker run --rm -p ${serverPort}:8000 ${imageName}`,
    url: `http://127.0.0.1:${serverPort}`,
    reuseExistingServer: false,
    timeout: 240_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});

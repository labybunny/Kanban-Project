import { execSync } from "node:child_process";

export default async function globalTeardown(): Promise<void> {
  try {
    const output = execSync("docker ps -q --filter ancestor=pm-mvp-e2e", {
      encoding: "utf-8",
      stdio: ["ignore", "pipe", "ignore"],
    });
    const containerIds = output
      .split(/\s+/)
      .map((value) => value.trim())
      .filter(Boolean);

    for (const containerId of containerIds) {
      execSync(`docker rm -f ${containerId}`, { stdio: "ignore" });
    }
  } catch {
    // Ignore teardown failures in local environments.
  }
}

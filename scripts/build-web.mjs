import { cp, mkdir, readdir, rm, stat } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { buildRunnerBundle } from "./build-runner.mjs";
import { verifyWebBuild } from "./verify-web-build.mjs";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const dist = join(root, "dist");

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

const files = ["index.html", "native-bridge.js"];
const directories = ["css", "js"];
for (const file of files) await cp(join(root, file), join(dist, file));
for (const directory of directories) await cp(join(root, directory), join(dist, directory), { recursive: true });

// Overwrite the naive copy of js/background-task.js with a flattened, import-free
// bundle — the background-runner worker has no module resolution system.
await buildRunnerBundle(dist);

const required = [
  "index.html",
  "native-bridge.js",
  "css/styles.css",
  "js/app.js",
  "js/notifications.js",
  "js/background-task.js",
  "js/core/scoring.js",
  "js/core/evaluation.js",
  "js/core/locations.js",
  "js/core/weather_api.js",
  "js/core/models.js",
  "js/core/timezone.js",
  "js/core/daily_summary.js",
];
for (const relative of required) {
  const information = await stat(join(dist, relative));
  if (!information.isFile() || information.size === 0) throw new Error(`Missing or empty web asset: ${relative}`);
}

await verifyWebBuild(dist);
const outputFiles = await readdir(dist);
console.log(`Web build ready: ${dist} (${outputFiles.length} top-level entries)`);

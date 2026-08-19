import { readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Script } from "node:vm";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));

// @capacitor/background-runner executes its `src` file as a raw script string in a
// headless JS engine with no module resolution (confirmed by reading BackgroundRunner.kt's
// initContext(), which does `newContext.execute(srcFile, false)` on the file's raw text).
// So the deployed runner artifact must be a single flat script with no import/export syntax,
// even though each source file below is authored as a normal ES module for testability.
const MODULE_ORDER = [
  "js/core/scoring.js",
  "js/core/timezone.js",
  "js/core/models.js",
  "js/core/locations.js",
  "js/core/weather_api.js",
  "js/core/evaluation.js",
  "js/core/daily_summary.js",
  "js/background-task.js",
];

const IMPORT_LINE = /^import\s.+;\s*$/gm;
const EXPORT_PREFIX = /^export\s+(?=(async\s+function|function|const|let|class)\b)/gm;

function flatten(source) {
  return source.replace(IMPORT_LINE, "").replace(EXPORT_PREFIX, "");
}

// The bundle is produced by stripping module syntax rather than by a real bundler,
// so nothing else proves the result is still a parseable classic script. Parse it
// here (parse only, no execution) so a bad strip fails the build loudly instead of
// only failing at 8am inside the headless runner.
export function validateRunnerBundle(bundle) {
  try {
    new Script(bundle, { filename: "dist/js/background-task.js" });
  } catch (error) {
    throw new Error(`Generated background runner bundle is not a valid classic script: ${error.message}`);
  }
  return bundle;
}

export async function createRunnerBundle() {
  const sections = await Promise.all(
    MODULE_ORDER.map(async (relative) => flatten(await readFile(join(root, relative), "utf8")).trim()),
  );
  return validateRunnerBundle(`${sections.join("\n\n")}\n`);
}

export async function buildRunnerBundle(dist = join(root, "dist")) {
  const bundle = await createRunnerBundle();
  await writeFile(join(dist, "js/background-task.js"), bundle);
  return bundle;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  await buildRunnerBundle(process.argv[2] || join(root, "dist"));
  console.log("Background runner bundle written");
}

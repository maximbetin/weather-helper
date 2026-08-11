import { mkdir, readdir, stat, copyFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const variant = process.argv.includes("--variant") ? process.argv[process.argv.indexOf("--variant") + 1] : "debug";
const output = process.argv.includes("--output") ? process.argv[process.argv.indexOf("--output") + 1] : join(root, "artifacts", `weather-helper-${variant}.apk`);
if (!new Set(["debug", "release"]).has(variant)) throw new Error(`Unsupported APK variant: ${variant}`);

const sourceDirectory = join(root, "android", "app", "build", "outputs", "apk", variant);
let candidates = [];
try {
  candidates = (await readdir(sourceDirectory)).filter((file) => file.toLowerCase().endsWith(".apk")).map((file) => join(sourceDirectory, file));
} catch {
  candidates = [];
}
if (candidates.length !== 1) throw new Error(`Expected exactly one ${variant} APK in ${sourceDirectory}, found ${candidates.length}`);
const information = await stat(candidates[0]);
if (!information.isFile() || information.size === 0) throw new Error(`APK is missing or empty: ${candidates[0]}`);
await mkdir(resolve(output, ".."), { recursive: true });
await copyFile(candidates[0], output);
console.log(`APK: ${resolve(output)}`);
console.log(`Size: ${information.size} bytes`);

import { access, stat } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const apk = resolve(process.argv[2] || resolve(root, "artifacts/weather-helper-debug.apk"));
await access(apk);
const information = await stat(apk);
if (!information.isFile() || information.size === 0) throw new Error(`APK is missing or empty: ${apk}`);

const listing = spawnSync(process.platform === "win32" ? "jar.exe" : "jar", ["tf", apk], { encoding: "utf8" });
if (listing.status !== 0) throw new Error("Could not inspect APK as a ZIP with the Java jar tool.");
if (!listing.stdout.split(/\r?\n/).includes("assets/public/index.html")) throw new Error("APK does not contain assets/public/index.html");

const analyzerName = process.platform === "win32" ? "apkanalyzer.bat" : "apkanalyzer";
const analyzerCandidates = [
  analyzerName,
  process.env.ANDROID_SDK_ROOT && join(process.env.ANDROID_SDK_ROOT, "cmdline-tools", "latest", "bin", analyzerName),
  process.env.ANDROID_HOME && join(process.env.ANDROID_HOME, "cmdline-tools", "latest", "bin", analyzerName),
].filter(Boolean);
const analyzerPath = analyzerCandidates.find((candidate) => {
  const result = spawnSync(candidate, ["--help"], { encoding: "utf8", shell: process.platform === "win32" });
  return result.status === 0 || result.status === 1;
});
const analyzer = analyzerPath ? spawnSync(analyzerPath, ["manifest", "application-id", apk], { encoding: "utf8", shell: process.platform === "win32" }) : { status: 1, stdout: "" };
if (analyzer.status === 0) {
  if (analyzer.stdout.trim() !== "com.maximbk.weatherhelper") throw new Error(`Unexpected APK application ID: ${analyzer.stdout.trim()}`);
  console.log("Package ID: com.maximbk.weatherhelper");
} else {
  console.warn("apkanalyzer was not available; package ID inspection was not performed.");
}
console.log(`APK inspection passed: ${apk} (${information.size} bytes)`);

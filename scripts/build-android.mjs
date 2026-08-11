import { spawn } from "node:child_process";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const variant = process.argv[2] || "debug";
const gradle = process.platform === "win32" ? ".\\gradlew.bat" : "./gradlew";
const task = `assemble${variant[0].toUpperCase()}${variant.slice(1)}`;

const child = spawn(gradle, [task, "--no-daemon"], { cwd: resolve(root, "android"), stdio: "inherit", shell: process.platform === "win32" });
child.on("error", (error) => { throw error; });
child.on("exit", (code, signal) => {
  if (signal) process.exit(1);
  if (code !== 0) process.exit(code ?? 1);
  const output = variant === "release" ? "artifacts/weather-helper-release.apk" : "artifacts/weather-helper-debug.apk";
  const locator = resolve(root, "scripts", "locate-apk.mjs");
  const locatorChild = spawn(process.execPath, [locator, "--variant", variant, "--output", resolve(root, output)], { cwd: root, stdio: "inherit" });
  locatorChild.on("exit", (locatorCode) => process.exit(locatorCode ?? 1));
});

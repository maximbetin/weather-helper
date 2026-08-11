import { readFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));

export async function verifyWebBuild(dist = join(root, "dist")) {
  const entry = await readFile(join(dist, "index.html"), "utf8");
  // Only resource-loading tags (script/link/img) are checked for remote hosts — the
  // page also has legitimate outbound <a href="https://api.met.no/..."> attribution
  // links required by MET Norway's ToS, which aren't runtime resource loads.
  const resourceTag = /<(?:script|link|img)\b[^>]*\b(?:src|href)=["']([^"']+)["']/gi;
  const remoteRuntime = /^(?:https?:)?\/\//i;
  const localhost = /(?:https?:\/\/)?(?:localhost|127\.0\.0\.1)(?::\d+)?/i;
  for (const [, url] of entry.matchAll(resourceTag)) {
    if (remoteRuntime.test(url)) throw new Error(`Web entry point loads a remote runtime resource: ${url}`);
    if (localhost.test(url)) throw new Error(`Web entry point loads a localhost resource: ${url}`);
  }
  const localModule = "(?:\\.\\/)?js\\/app\\.js(?:\\?[^\"']*)?";
  if (!new RegExp(`<script\\b[^>]*src=[\"']${localModule}[\"'][^>]*type=[\"']module[\"']`, "i").test(entry) && !new RegExp(`<script\\b[^>]*type=[\"']module[\"'][^>]*src=[\"']${localModule}[\"']`, "i").test(entry)) {
    throw new Error("Web entry point does not load the local application module");
  }
  return true;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  await verifyWebBuild(process.argv[2] || join(root, "dist"));
  console.log("Web asset validation passed");
}

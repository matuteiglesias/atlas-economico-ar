import { readFile, readdir } from "node:fs/promises";
import path from "node:path";

const dataRoot = path.resolve(process.cwd(), "site-data");
const manifest = JSON.parse(await readFile(path.join(dataRoot, "manifest.json"), "utf8"));
const search = JSON.parse(await readFile(path.join(dataRoot, "search-index.json"), "utf8"));
const folderByKind = { region: "regions", topic: "topics", question: "questions", indicator: "indicators", chart: "charts" };
const errors = [];

for (const [kind, folder] of Object.entries(folderByKind)) {
  const indexed = search.filter((item) => item.kind === kind);
  const files = (await readdir(path.join(dataRoot, folder))).filter((file) => file.endsWith(".json"));
  if (indexed.length !== manifest.counts[kind]) errors.push(`${kind}: search index has ${indexed.length}; expected ${manifest.counts[kind]}`);
  if (files.length !== manifest.counts[kind]) errors.push(`${folder}: found ${files.length} files; expected ${manifest.counts[kind]}`);
}

const hrefs = search.map((item) => item.href);
if (new Set(hrefs).size !== hrefs.length) errors.push("search index contains duplicate hrefs");
for (const item of search) {
  if (!item.id || !item.slug || !item.title || !item.text || !item.href?.startsWith("/")) errors.push(`invalid search item: ${item.id ?? "unknown"}`);
}

if (errors.length) {
  console.error(`Data contract verification failed:\n- ${errors.join("\n- ")}`);
  process.exit(1);
}
console.log(`Data contract verification passed (${search.length} public entities).`);

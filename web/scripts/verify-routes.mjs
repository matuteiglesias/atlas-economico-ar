import { access, readFile } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const out = path.join(root, "out");
const search = JSON.parse(await readFile(path.resolve(root, "site-data/search-index.json"), "utf8"));
const routes = ["/", "/atlas", ...search.map((item) => item.href)];
const uniqueRoutes = new Set(routes);
const missing = [];

if (uniqueRoutes.size !== 279) {
  console.error(`Route contract verification failed: expected 279 unique routes, found ${uniqueRoutes.size}.`);
  process.exit(1);
}
for (const route of uniqueRoutes) {
  const output = route === "/" ? path.join(out, "index.html") : path.join(out, route.slice(1), "index.html");
  try { await access(output); } catch { missing.push(route); }
}
if (missing.length) {
  console.error(`Static route verification failed (${missing.length} missing):\n${missing.join("\n")}`);
  process.exit(1);
}
console.log(`Static route verification passed (${uniqueRoutes.size} routes).`);

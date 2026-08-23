import { access, readFile } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const out = path.join(root, "out");
const surface = JSON.parse(await readFile(path.resolve(root, "site-data/public-surface.json"), "utf8"));
const routes = [...surface.staticRoutes, ...surface.routes.map((item) => item.href)];
const uniqueRoutes = new Set(routes);
const missing = [];
if (uniqueRoutes.size !== routes.length) {
  console.error(`Route contract verification failed: ${routes.length - uniqueRoutes.size} duplicate href(s).`);
  process.exit(1);
}
for (const route of uniqueRoutes) {
  if (typeof route !== "string" || !route.startsWith("/")) {
    console.error(`Route contract verification failed: invalid route ${JSON.stringify(route)}.`);
    process.exit(1);
  }
  const output = route === "/" ? path.join(out, "index.html") : path.join(out, route.slice(1), "index.html");
  try { await access(output); } catch { missing.push(route); }
}
if (missing.length) {
  console.error(`Static route verification failed (${missing.length} missing):\n${missing.join("\n")}`);
  process.exit(1);
}
console.log(`Static route verification passed (${uniqueRoutes.size} intentional public routes).`);

import { readFile, readdir } from "node:fs/promises";
import path from "node:path";

const dataRoot = path.resolve(process.cwd(), "site-data");
const manifest = JSON.parse(await readFile(path.join(dataRoot, "manifest.json"), "utf8"));
const surface = JSON.parse(await readFile(path.join(dataRoot, "public-surface.json"), "utf8"));
const search = JSON.parse(await readFile(path.join(dataRoot, "search-index.json"), "utf8"));
const folderByKind = { region: "regions", topic: "topics", question: "questions", indicator: "indicators", chart: "charts" };
const childKinds = new Set(["topic", "question", "indicator", "chart"]);
const errors = [];

if (surface.schemaVersion !== "0.2") errors.push(`public surface schema ${surface.schemaVersion}; expected 0.2`);
if (JSON.stringify(manifest.publicSurface) !== JSON.stringify({
  schemaVersion: surface.schemaVersion,
  semanticCounts: surface.semanticCounts,
  addressableCounts: surface.addressableCounts,
  discoverableCounts: surface.discoverableCounts,
  activationBlockedCounts: surface.activationBlockedCounts,
  chartCensus: surface.chartCensus,
})) errors.push("manifest publicSurface summary differs from public-surface.json");

for (const entity of surface.entities ?? []) {
  if (!entity.owningRegionId || typeof entity.regionActivated !== "boolean" || typeof entity.activationBlocked !== "boolean") {
    errors.push(`entity lacks region activation metadata: ${entity.kind}/${entity.id}`);
    continue;
  }
  const shouldBeBlocked = childKinds.has(entity.kind) && !entity.regionActivated;
  if (entity.activationBlocked !== shouldBeBlocked) {
    errors.push(`activationBlocked mismatch: ${entity.kind}/${entity.id}`);
  }
  if (entity.activationBlocked && (entity.addressable || entity.discoverable || entity.prominent)) {
    errors.push(`inactive-region child leaked public capabilities: ${entity.kind}/${entity.id}`);
  }
}

for (const [kind, folder] of Object.entries(folderByKind)) {
  const indexed = search.filter((item) => item.kind === kind);
  const files = (await readdir(path.join(dataRoot, folder))).filter((file) => file.endsWith(".json"));
  const routes = surface.routes.filter((item) => item.kind === kind);
  const discovery = surface.discovery.filter((item) => item.kind === kind);
  if (files.length !== surface.addressableCounts[kind]) errors.push(`${folder}: found ${files.length} route files; expected ${surface.addressableCounts[kind]}`);
  if (routes.length !== surface.addressableCounts[kind]) errors.push(`${kind}: route manifest has ${routes.length}; expected ${surface.addressableCounts[kind]}`);
  if (indexed.length !== surface.discoverableCounts[kind]) errors.push(`${kind}: search index has ${indexed.length}; expected ${surface.discoverableCounts[kind]}`);
  if (discovery.length !== surface.discoverableCounts[kind]) errors.push(`${kind}: discovery manifest has ${discovery.length}; expected ${surface.discoverableCounts[kind]}`);
}

const expectedChartCensus = { semantic: 119, materialized: 41, addressable: 41, discoverable: 27 };
if (JSON.stringify(surface.chartCensus) !== JSON.stringify(expectedChartCensus)) {
  errors.push(`chart census ${JSON.stringify(surface.chartCensus)}; expected ${JSON.stringify(expectedChartCensus)}`);
}

const routeHrefs = surface.routes.map((item) => item.href);
if (new Set(routeHrefs).size !== routeHrefs.length) errors.push("public route manifest contains duplicate hrefs");
const discoveryKeys = new Set(surface.discovery.map((item) => `${item.kind}:${item.id}:${item.href}`));
const hrefs = search.map((item) => item.href);
if (new Set(hrefs).size !== hrefs.length) errors.push("search index contains duplicate hrefs");
for (const item of search) {
  if (!item.id || !item.slug || !item.title || !item.text || !item.href?.startsWith("/")) errors.push(`invalid search item: ${item.id ?? "unknown"}`);
  if (!discoveryKeys.has(`${item.kind}:${item.id}:${item.href}`)) errors.push(`search item outside discoverable public surface: ${item.kind}/${item.id}`);
}

if (errors.length) {
  console.error(`Data contract verification failed:\n- ${errors.join("\n- ")}`);
  process.exit(1);
}
console.log(`Data contract verification passed (${surface.routes.length} addressable routes; ${search.length} discoverable entities).`);

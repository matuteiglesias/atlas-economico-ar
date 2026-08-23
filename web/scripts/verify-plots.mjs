import { createHash } from "node:crypto";
import { access, readFile, readdir } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const chartRoot = path.resolve(root, "site-data/charts");
const publicRoot = path.resolve(root, "public");
const artifactRoot = path.resolve(root, "../plot-artifacts");
const embedRoot = path.join(artifactRoot, "embed");
const manifest = JSON.parse(await readFile(path.resolve(root, "site-data/manifest.json"), "utf8"));
const plotManifest = JSON.parse(await readFile(path.join(artifactRoot, "manifest.json"), "utf8"));
const expectedArtifacts = manifest.plotArtifacts;
const artifacts = [];
const errors = [];

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

if (!Number.isInteger(expectedArtifacts) || expectedArtifacts < 0) {
  errors.push("site-data manifest has invalid plotArtifacts count");
}
if (plotManifest.presentation_contract?.review !== "self_describing" || plotManifest.presentation_contract?.embed !== "page_owned_chrome") {
  errors.push("plot-artifacts manifest does not declare the review/embed presentation boundary");
}

for (const file of await readdir(chartRoot)) {
  if (!file.endsWith(".json")) continue;
  const page = JSON.parse(await readFile(path.join(chartRoot, file), "utf8"));
  if (!page.artifact) continue;
  artifacts.push({ id: page.id, artifact: page.artifact });
}

if (Number.isInteger(expectedArtifacts) && artifacts.length !== expectedArtifacts) {
  errors.push(`manifest declares ${expectedArtifacts} materialized chart pages; found ${artifacts.length}`);
}

for (const { id, artifact } of artifacts) {
  for (const field of ["svg", "png"]) {
    const publicPath = artifact[field];
    if (typeof publicPath !== "string" || !publicPath.startsWith("/plots/")) {
      errors.push(`${id}: invalid ${field} public path`);
      continue;
    }
    const filename = path.basename(publicPath);
    const publishedPath = path.join(publicRoot, publicPath.slice(1));
    const embedPath = path.join(embedRoot, filename);
    const reviewPath = path.join(artifactRoot, field, filename);
    try {
      await access(publishedPath);
      await access(embedPath);
      await access(reviewPath);
      const [published, embed, review] = await Promise.all([
        readFile(publishedPath),
        readFile(embedPath),
        readFile(reviewPath),
      ]);
      if (sha256(published) !== sha256(embed)) {
        errors.push(`${id}: published ${field} is not the page-owned embed variant`);
      }
      if (sha256(embed) === sha256(review)) {
        errors.push(`${id}: embed ${field} unexpectedly equals self-describing review output`);
      }
    } catch {
      errors.push(`${id}: missing review/embed/published ${field} for ${publicPath}`);
    }
  }
  if (!artifact.altText) errors.push(`${id}: missing altText`);
  if (!artifact.dataAsOf) errors.push(`${id}: missing dataAsOf`);
  if (!artifact.chartSpecId || !artifact.frameId) errors.push(`${id}: incomplete publication metadata`);
}

if (errors.length) {
  console.error(`Plot publication verification failed:\n- ${errors.join("\n- ")}`);
  process.exit(1);
}
console.log(`Plot publication verification passed (${artifacts.length} real charts; web uses page-owned embed variants).`);

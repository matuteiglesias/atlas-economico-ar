import { cp, mkdir, readdir, rm } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const sourceRoot = path.resolve(root, "../plot-artifacts/embed");
const destination = path.resolve(root, "public/plots");

await rm(destination, { recursive: true, force: true });
await mkdir(destination, { recursive: true });

for (const file of await readdir(sourceRoot)) {
  if (!file.endsWith(".svg") && !file.endsWith(".png")) continue;
  await cp(path.join(sourceRoot, file), path.join(destination, file));
}

console.log(`Synced page-owned PlotArtifact embed variants from ${sourceRoot} to ${destination}.`);

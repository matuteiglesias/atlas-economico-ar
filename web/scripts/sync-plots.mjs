import { cp, mkdir, readdir, rm } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const sourceRoot = path.resolve(root, "../plot-artifacts");
const destination = path.resolve(root, "public/plots");

await rm(destination, { recursive: true, force: true });
await mkdir(destination, { recursive: true });

for (const folder of ["svg", "png"]) {
  const source = path.join(sourceRoot, folder);
  for (const file of await readdir(source)) {
    if (!file.endsWith(`.${folder}`) && !(folder === "png" && file.endsWith(".png"))) continue;
    await cp(path.join(source, file), path.join(destination, file));
  }
}

console.log(`Synced static PlotArtifacts from ${sourceRoot} to ${destination}.`);

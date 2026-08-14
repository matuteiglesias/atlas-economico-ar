import { cp, rm } from "node:fs/promises";
import path from "node:path";

const root = process.cwd();
const source = path.resolve(root, "../site-data");
const destination = path.resolve(root, "site-data");

await rm(destination, { recursive: true, force: true });
await cp(source, destination, { recursive: true });
console.log(`Synced compiled site data from ${source} to ${destination}.`);

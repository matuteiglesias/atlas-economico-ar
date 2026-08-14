import "server-only";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import type { EntityPage, Navigation, RegionPage, TopicPage } from "./types";

const dataRoot = path.resolve(process.cwd(), "../site-data");

async function readJson<T>(relativePath: string): Promise<T> {
  return JSON.parse(await readFile(path.join(dataRoot, relativePath), "utf8")) as T;
}

export const getNavigation = () => readJson<Navigation>("navigation.json");
export const getTopic = (slug: string) => readJson<TopicPage>(`topics/${slug}.json`);
export const getRegion = (slug: string) => readJson<RegionPage>(`regions/${slug}.json`);
export const getEntity = (kind: "questions" | "indicators" | "charts", slug: string) =>
  readJson<EntityPage>(`${kind}/${slug}.json`);

export async function getTopicSlugs(): Promise<string[]> {
  return (await readdir(path.join(dataRoot, "topics")))
    .filter((file: string) => file.endsWith(".json"))
    .map((file: string) => file.slice(0, -5));
}

export async function getSlugs(kind: "regions" | "questions" | "indicators" | "charts"): Promise<string[]> {
  return (await readdir(path.join(dataRoot, kind))).filter((file) => file.endsWith(".json")).map((file) => file.slice(0, -5));
}

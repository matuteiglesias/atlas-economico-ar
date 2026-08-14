import "server-only";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import type { Navigation, TopicPage } from "./types";

const dataRoot = path.resolve(process.cwd(), "../site-data");

async function readJson<T>(relativePath: string): Promise<T> {
  return JSON.parse(await readFile(path.join(dataRoot, relativePath), "utf8")) as T;
}

export const getNavigation = () => readJson<Navigation>("navigation.json");
export const getTopic = (slug: string) => readJson<TopicPage>(`topics/${slug}.json`);

export async function getTopicSlugs(): Promise<string[]> {
  return (await readdir(path.join(dataRoot, "topics")))
    .filter((file: string) => file.endsWith(".json"))
    .map((file: string) => file.slice(0, -5));
}

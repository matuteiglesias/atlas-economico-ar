import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { PublicEntityPage } from "@/components/entity-page";
import { getEntity, getNavigation, getSlugs } from "@/lib/site-data";
export const dynamicParams = false;
export async function generateStaticParams() { return (await getSlugs("questions")).map((slug) => ({ slug })); }
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> { const { slug } = await params; const page = await getEntity("questions", slug).catch(() => null); return { title: page?.title ?? "Question" }; }
export default async function Page({ params }: { params: Promise<{ slug: string }> }) { const { slug } = await params; const page = await getEntity("questions", slug).catch(() => notFound()); return <PublicEntityPage page={page} navigation={await getNavigation()} />; }

import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { BarChart3, CircleHelp, Database, Layers3 } from "lucide-react";
import { ChartCard } from "@/components/charts";
import { LinkList, PageHeader } from "@/components/content";
import { ExploreRail, PageBreadcrumbs, SiteHeader } from "@/components/shell";
import { getNavigation, getRegion, getSlugs } from "@/lib/site-data";

export const dynamicParams = false;
export async function generateStaticParams() { return (await getSlugs("regions")).map((slug) => ({ slug })); }
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> { const { slug } = await params; const page = await getRegion(slug).catch(() => null); return { title: page?.title ?? "Area" }; }

export default async function Area({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params; const area = await getRegion(slug).catch(() => notFound()); const navigation = await getNavigation();
  return <><SiteHeader /><div className="page-grid area-layout"><ExploreRail navigation={navigation} activeRegion={slug} /><main className="main-content entity-page">
    <PageHeader kind="Economic area" title={area.title} dek={area.dek ?? null} />
    {!area.populated ? <div className="empty-area"><Layers3 /><p className="eyebrow">Atlas structure</p><h2>This area is ready for its knowledge vertical.</h2><p>It will populate as its compiled knowledge becomes available.</p><a href="/atlas">Return to the atlas →</a></div> : <>
      <section className="area-stats">{(["topics", "questions", "indicators", "charts"] as const).map((key) => <div key={key}><strong>{area.stats[key]}</strong><span>{key}</span></div>)}</section>
      <AreaSection title="Key questions" icon={<CircleHelp />}><LinkList items={area.questions.slice(0, 8)} /></AreaSection>
      <AreaSection title="Core topics" icon={<Layers3 />}><div className="topic-grid">{area.topics.map((topic) => <a key={topic.href} href={topic.href}>{topic.title}<b>›</b></a>)}</div></AreaSection>
      <AreaSection title="Selected charts" icon={<BarChart3 />}><div className="chart-grid">{area.charts.slice(0, 3).map((chart) => <ChartCard key={chart.href} item={chart} />)}</div></AreaSection>
      <AreaSection title="Indicators" icon={<Database />}><LinkList items={area.indicators} /></AreaSection>
    </>}
  </main></div><PageBreadcrumbs items={area.breadcrumbs} current={area.title} /></>;
}
function AreaSection({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) { return <section className="content-section"><header><h2>{icon}{title}</h2></header>{children}</section>; }

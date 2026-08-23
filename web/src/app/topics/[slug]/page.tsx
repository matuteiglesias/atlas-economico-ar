import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ChartCard, evidenceFirstCharts } from "@/components/charts";
import { EntityHeader, QuestionRow, Section, WhyItMatters } from "@/components/content";
import { Breadcrumbs, EntityContextRail, ExploreRail, SiteHeader } from "@/components/shell";
import { getNavigation, getTopic, getTopicSlugs } from "@/lib/site-data";

export const dynamicParams = false;

export async function generateStaticParams() {
  return (await getTopicSlugs()).map((slug) => ({ slug }));
}
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params; const topic = await getTopic(slug).catch(() => null);
  return { title: topic?.title ?? "Topic", description: topic?.dek ?? undefined };
}

export default async function Topic({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const topic = await getTopic(slug).catch(() => notFound());
  const navigation = await getNavigation();
  const evidenceCharts = evidenceFirstCharts(topic.charts);
  const relatedTopics = topic.connections.filter(({ entity }) => entity.kind === "topic").slice(0, 5).map(({ entity }) => entity);
  const contextGroups = [
    { title: "Related topics", links: relatedTopics },
    { title: "Indicators", links: topic.indicators },
    { title: "Used by these questions", links: topic.questions },
  ];

  return <><SiteHeader /><div className="page-grid">
    <ExploreRail navigation={navigation} activeRegion={topic.region.slug} />
    <main className="main-content">
      <EntityHeader title={topic.title} dek={topic.dek} region={topic.region} />
      <Section id="questions" title="Questions people ask">
        <div>{topic.questions.map((question) => <QuestionRow key={question.href} item={question} />)}</div>
      </Section>
      {evidenceCharts.length > 0 && <Section id="charts" title="See it in the data">
        <div className="chart-grid">{evidenceCharts.slice(0, 3).map((chart) => <ChartCard key={chart.href} item={chart} />)}</div>
      </Section>}
      {slug === "inflation" && <WhyItMatters />}
    </main>
    <EntityContextRail label="In this topic" groups={contextGroups} />
  </div><Breadcrumbs topic={topic} /></>;
}

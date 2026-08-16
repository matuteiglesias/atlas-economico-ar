import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { ChartCard, isProminentChart } from "@/components/charts";
import { EntityHeader, QuestionRow, Section, WhyItMatters } from "@/components/content";
import { Breadcrumbs, ContextRail, ExploreRail, SiteHeader } from "@/components/shell";
import { getNavigation, getTopic, getTopicSlugs } from "@/lib/site-data";
import type { EntityLink } from "@/lib/types";

export const dynamicParams = false;

export async function generateStaticParams() {
  return (await getTopicSlugs()).map((slug) => ({ slug }));
}
export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params; const topic = await getTopic(slug).catch(() => null);
  return { title: topic?.title ?? "Topic", description: topic?.dek ?? undefined };
}

const featuredCharts: EntityLink[] = [
  { kind: "chart", slug: "headline-vs-core-inflation", title: "Headline vs Core Inflation", href: "/charts/headline-vs-core-inflation" },
  { kind: "chart", slug: "inflation-momentum-monthly-and-3-month-annualized", title: "Inflation Momentum", href: "/charts/inflation-momentum-monthly-and-3-month-annualized" },
  { kind: "chart", slug: "inflation-driver-decomposition", title: "Inflation Driver Decomposition", href: "/charts/inflation-driver-decomposition" },
];

export default async function Topic({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const topic = await getTopic(slug).catch(() => notFound());
  const navigation = await getNavigation();
  const prominentCharts = topic.charts.filter(isProminentChart);
  const charts = slug === "inflation" ? featuredCharts : prominentCharts.slice(0, 3);

  return <><SiteHeader /><div className="page-grid">
    <ExploreRail navigation={navigation} activeRegion={topic.region.slug} />
    <main className="main-content">
      <EntityHeader title={topic.title} dek={topic.dek} region={topic.region} />
      <Section id="questions" title="Questions people ask" count={topic.questions.length}>
        <div>{topic.questions.slice(0, 6).map((question) => <QuestionRow key={question.href} item={question} />)}</div>
      </Section>
      <Section id="charts" title="See it in the data" count={prominentCharts.length}>
        <div className="chart-grid">{charts.map((chart) => <ChartCard key={chart.href} item={chart} />)}</div>
      </Section>
      {slug === "inflation" && <WhyItMatters />}
    </main>
    <ContextRail topic={topic} />
  </div><Breadcrumbs topic={topic} /></>;
}

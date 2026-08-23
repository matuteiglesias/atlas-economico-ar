import { BarChart3, CircleHelp, Database, Tag } from "lucide-react";
import { ChartCard, evidenceFirstCharts } from "./charts";
import { LinkList, PageHeader } from "./content";
import { EntityContextRail, ExploreRail, PageBreadcrumbs, SiteHeader } from "./shell";
import type { EntityLink, EntityPage, Navigation } from "@/lib/types";

const labels = { question: "Question", indicator: "Indicator", chart: "Chart" } as const;

function ChartSurface({ page }: { page: EntityPage }) {
  if (!page.artifact) return null;
  return <div className="large-chart"><ChartCard item={page} chrome="page" /></div>;
}

function withoutKnownLinks(links: EntityLink[], knownGroups: EntityLink[][]) {
  const knownHrefs = new Set(knownGroups.flatMap((group) => group.map((item) => item.href)));
  return links.filter((item) => !knownHrefs.has(item.href));
}

export function PublicEntityPage({ page, navigation }: { page: EntityPage; navigation: Navigation }) {
  const topics = page.topics ?? (page.topic ? [page.topic] : []);
  const questions = page.questions ?? [];
  const indicators = page.indicators ?? [];
  const charts = page.charts ?? [];
  const evidenceCharts = evidenceFirstCharts(charts);
  const nearby = withoutKnownLinks(page.nearby, [topics, questions, indicators]);
  const groups = [{ title: "Topics", links: topics }, { title: "Questions", links: questions }, { title: "Indicators", links: indicators }, { title: "Nearby", links: nearby }];
  return <><SiteHeader /><div className="page-grid">
    <ExploreRail navigation={navigation} activeRegion={page.region.slug} />
    <main className="main-content entity-page">
      <PageHeader kind={labels[page.kind]} title={page.title} dek={page.dek} region={page.region} />
      {page.kind === "chart" && <ChartSurface page={page} />}
      {page.kind === "indicator" && <section className="fact-strip"><div><small>Frequency</small><strong>{humanize(page.frequency)}</strong></div><div><small>Unit</small><strong>{humanize(page.unitSemantics)}</strong></div><div><small>Series status</small><strong>Data integration pending</strong></div></section>}
      {page.intro && <section className="editorial-intro"><p>{page.intro}</p></section>}
      {page.kind === "question" && <EntitySection icon={<Tag />} title="Ideas involved"><LinkList items={topics} /></EntitySection>}
      {page.kind === "question" && evidenceCharts.length > 0 && <EntitySection icon={<BarChart3 />} title="Ways to look at it"><div className="chart-grid">{evidenceCharts.slice(0, 3).map((chart) => <ChartCard key={chart.href} item={chart} />)}</div></EntitySection>}
      {page.kind === "question" && <EntitySection icon={<Database />} title="Measurements underneath"><LinkList items={indicators} /></EntitySection>}
      {page.kind === "indicator" && evidenceCharts.length > 0 && <EntitySection icon={<BarChart3 />} title="Charts using this indicator"><div className="chart-grid">{evidenceCharts.slice(0, 3).map((chart) => <ChartCard key={chart.href} item={chart} />)}</div></EntitySection>}
      {page.kind === "chart" && <EntitySection icon={<CircleHelp />} title="Questions answered"><LinkList items={questions} /></EntitySection>}
      {page.kind === "chart" && <EntitySection icon={<Database />} title="Indicators used"><LinkList items={indicators} /></EntitySection>}
    </main>
    <EntityContextRail label={`About this ${page.kind}`} groups={groups} />
  </div><PageBreadcrumbs items={page.breadcrumbs} current={page.title} /></>;
}

function EntitySection({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return <section className="content-section"><header><h2>{icon}{title}</h2></header>{children}</section>;
}

function humanize(value?: string) {
  if (!value) return "Not specified";
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

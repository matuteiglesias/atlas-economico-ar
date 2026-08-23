import Link from "next/link";
import { BarChart3, CircleHelp, Search } from "lucide-react";
import { LinkList } from "@/components/content";
import { SiteHeader } from "@/components/shell";
import { getNavigation, getRegion } from "@/lib/site-data";

export const metadata = { title: "Browse the Atlas" };

export default async function Atlas() {
  const navigation = await getNavigation();
  const activeRegions = navigation.regions.filter((region) => region.populated);
  const plannedRegions = navigation.regions.filter((region) => !region.populated);
  const activeAreas = await Promise.all(activeRegions.map((region) => getRegion(region.slug)));
  const selectedQuestions = activeAreas.flatMap((area) => area.questions.slice(0, 3));
  const selectedEvidence = activeRegions.map((region) => ({ title: `${region.title} evidence`, href: region.href }));

  return <><SiteHeader /><main className="browse-page">
    <p className="eyebrow">Browse</p>
    <h1>Economic atlas</h1>
    <p className="browse-dek">An orientation surface for the parts of Argentina&apos;s economic atlas that are ready to explore today, with the broader six-area scope kept visible without pretending unfinished areas are destinations.</p>

    <section>
      <p className="eyebrow">Active areas</p>
      <div className="atlas-areas">{activeRegions.map((region) => <Link href={region.href} key={region.href} className="populated"><span>Active</span><h2>{region.title}</h2><p>{region.dek}</p><b>Explore area →</b></Link>)}</div>
    </section>

    <section className="browse-columns">
      <Browse title="Selected questions" icon={<CircleHelp />} items={selectedQuestions} />
      <Browse title="Selected evidence / charts" icon={<BarChart3 />} items={selectedEvidence} />
      <Browse title="Search" icon={<Search />} items={[{ title: "Search the atlas", href: "?search=open" }]} />
    </section>

    <section className="content-section">
      <header><h2>Atlas scope</h2></header>
      <p className="browse-dek">The conceptual map spans six economic areas. The remaining areas stay visible as roadmap context until they have public content worth navigating to.</p>
      <div className="chart-grid">{plannedRegions.map((region) => <article className="chart-card" key={region.slug}><div className="chart-title"><p>Planned area</p><h3>{region.title}</h3></div></article>)}</div>
    </section>
  </main></>;
}

function Browse({ title, icon, items }: { title: string; icon: React.ReactNode; items: Parameters<typeof LinkList>[0]["items"] }) {
  return <section><h2>{icon}{title} <small>{items.length}</small></h2><LinkList items={items} /></section>;
}

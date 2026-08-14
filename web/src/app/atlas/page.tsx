import { BarChart3, CircleHelp, Database, Layers3 } from "lucide-react";
import { LinkList } from "@/components/content";
import { SiteHeader } from "@/components/shell";
import { getNavigation, getRegion } from "@/lib/site-data";

export const metadata = { title: "Browse the Atlas" };
export default async function Atlas() {
  const navigation = await getNavigation(); const area = await getRegion("nominal-stabilization");
  return <><SiteHeader /><main className="browse-page"><p className="eyebrow">Browse</p><h1>Economic atlas</h1><p className="browse-dek">A structured way into Argentina&apos;s economic questions, concepts, indicators, and chart ideas.</p>
    <section className="atlas-areas">{navigation.regions.map((region) => <a href={region.href} key={region.href} className={region.populated ? "populated" : ""}><span>{region.populated ? "Available" : "Structure ready"}</span><h2>{region.title}</h2><p>{region.dek}</p><b>Explore area →</b></a>)}</section>
    <section className="browse-columns"><Browse title="Topics" icon={<Layers3 />} items={area.topics} /><Browse title="Questions" icon={<CircleHelp />} items={area.questions} /><Browse title="Indicators" icon={<Database />} items={area.indicators} /><Browse title="Charts" icon={<BarChart3 />} items={area.charts} /></section>
  </main></>;
}
function Browse({ title, icon, items }: { title: string; icon: React.ReactNode; items: Parameters<typeof LinkList>[0]["items"] }) { return <section><h2>{icon}{title} <small>{items.length}</small></h2><LinkList items={items} /></section>; }

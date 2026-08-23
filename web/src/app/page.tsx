import { BarChart3, CircleHelp } from "lucide-react";
import Link from "next/link";
import { ChartCard, isProminentChart } from "@/components/charts";
import { LinkList } from "@/components/content";
import { SiteHeader } from "@/components/shell";
import { getNavigation, getRegion } from "@/lib/site-data";
export default async function Home() {
  const navigation = await getNavigation(); const area = await getRegion("nominal-stabilization"); const prominentCharts = area.charts.filter(isProminentChart);
  const activeRegions = navigation.regions.filter((region) => region.populated);
  return <><SiteHeader /><main className="home-page"><section className="home-hero"><p className="eyebrow">Argentina / Economic Atlas</p><h1>Explore the questions shaping Argentina&apos;s economy.</h1><p>Move from public questions to the concepts, measurements, and chart ideas that help examine them.</p><div><Link className="primary-link" href="/topics/inflation">Start with inflation →</Link><Link href="/atlas">Browse the atlas →</Link></div></section>
    <section className="home-counts">{Object.entries(navigation.counts).map(([kind, count]) => <div key={kind}><strong>{count}</strong><span>{kind}s</span></div>)}</section>
    <section className="home-areas"><header><p className="eyebrow">Active economic areas</p><h2>Public entry points into the atlas</h2></header><div>{activeRegions.map((region) => <Link href={region.href} key={region.href} className="populated"><small>Now available</small><h3>{region.title}</h3><p>{region.dek}</p></Link>)}</div></section>
    <section className="home-editorial"><div><h2><CircleHelp /> Selected questions</h2><LinkList items={area.questions.slice(0, 6)} /></div><div><h2><BarChart3 /> Selected charts</h2><div className="chart-grid">{prominentCharts.slice(0, 3).map((chart) => <ChartCard key={chart.href} item={chart} />)}</div></div></section>
  </main></>;
}

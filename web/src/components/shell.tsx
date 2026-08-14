import Link from "next/link";
import { BarChart3, Building2, CircleHelp, Compass, Database, Globe2, Home, Landmark, Menu, Search, Tag, Users } from "lucide-react";
import type { EntityLink, Navigation, TopicPage } from "@/lib/types";

const areaIcons = [BarChart3, Globe2, Building2, Users, Home, Landmark];

export function SiteHeader() {
  return <header className="site-header">
    <Link href="/" className="brand"><Compass aria-hidden /><strong>ARGENTINA</strong><span>/ ECONOMIC ATLAS</span></Link>
    <button className="mobile-menu" aria-label="Open navigation"><Menu /></button>
    <div className="header-actions"><button className="search-trigger"><Search size={18} /><span>Search the atlas…</span><kbd>⌘ K</kbd></button><a href="#about">About</a></div>
  </header>;
}

export function ExploreRail({ navigation, activeRegion }: { navigation: Navigation; activeRegion: string }) {
  const quick = [
    [CircleHelp, "All Questions", "/atlas#questions"], [BarChart3, "All Charts", "/atlas#charts"],
    [Database, "All Indicators", "/atlas#indicators"], [Tag, "Topics", "/atlas#topics"],
    [Search, "Search", "#search"], [Compass, "Atlas Map", "/atlas"],
  ] as const;
  return <aside className="explore-rail">
    <p className="rail-label">Explore</p>
    <nav aria-label="Economic areas" className="area-list">{navigation.regions.map((area, index) => {
      const Icon = areaIcons[index];
      return <Link key={area.slug} href={area.href} className={area.slug === activeRegion ? "active" : ""}><Icon /><span>{area.title}</span></Link>;
    })}</nav>
    <div className="quick"><p className="rail-label">Quick links</p>{quick.map(([Icon, label, href]) => <Link key={label} href={href}><Icon /><span>{label}</span></Link>)}</div>
    <div id="about" className="about"><div><CircleHelp /> <strong>About this atlas</strong></div><p>A map of the questions, concepts and measurements that help explain the Argentine economy.</p></div>
  </aside>;
}

function RailList({ links }: { links: EntityLink[] }) {
  return <div className="rail-links">{links.map((item) => <Link key={item.href} href={item.href}><span>{item.title}</span><b>›</b></Link>)}</div>;
}

export function ContextRail({ topic }: { topic: TopicPage }) {
  const related = topic.connections.filter(({ entity }) => entity.kind === "topic").slice(0, 5).map(({ entity }) => entity);
  return <aside className="context-rail">
    <p className="rail-label">In this topic</p>
    <div className="stats">
      <a href="#questions"><CircleHelp /><strong>{topic.counts.questions}</strong><span>Questions</span><b>›</b></a>
      <a href="#charts"><BarChart3 /><strong>{topic.counts.charts}</strong><span>Charts</span><b>›</b></a>
      <a href="#indicators"><Database /><strong>{topic.counts.indicators}</strong><span>Indicators</span><b>›</b></a>
    </div>
    <section><p className="rail-label">Related topics</p><RailList links={related} /></section>
    <section><p className="rail-label">Used by these questions</p><RailList links={topic.questions.slice(0, 3)} /><Link className="see-all" href="#questions">See all {topic.questions.length} questions →</Link></section>
  </aside>;
}

export function Breadcrumbs({ topic }: { topic: TopicPage }) {
  return <nav className="breadcrumbs" aria-label="Breadcrumb"><Link href="/"><Home /></Link>{topic.breadcrumbs.slice(1).map((item) => <Link key={item.href} href={item.href}>› <span>{item.title}</span></Link>)}<span>› &nbsp;{topic.title}</span></nav>;
}

export function PageBreadcrumbs({ items, current }: { items: EntityLink[]; current: string }) {
  return <nav className="breadcrumbs" aria-label="Breadcrumb"><Link href="/"><Home /></Link>{items.map((item) => <Link key={item.href} href={item.href}>› <span>{item.title}</span></Link>)}<span>› &nbsp;{current}</span></nav>;
}

export function EntityContextRail({ label, groups }: { label: string; groups: { title: string; links: EntityLink[] }[] }) {
  return <aside className="context-rail"><p className="rail-label">{label}</p>{groups.filter((group) => group.links.length).map((group) => <section key={group.title}><p className="rail-label">{group.title}</p><RailList links={group.links.slice(0, 7)} /></section>)}</aside>;
}

import Link from "next/link";
import { ArrowRight, BarChart3, Lightbulb } from "lucide-react";
import type { EntityLink } from "@/lib/types";

export function EntityHeader({ title, dek, region }: { title: string; dek: string | null; region: EntityLink }) {
  return <header className="entity-header"><p className="eyebrow">Topic</p><h1>{title}</h1>{dek && <p className="dek">{dek}</p>}<div className="pills"><Link href={region.href}>{region.title}</Link></div></header>;
}

export function Section({ id, title, count, children }: { id: string; title: string; count: number; children: React.ReactNode }) {
  return <section id={id} className="content-section"><header><h2>{id === "charts" && <BarChart3 />} {title}</h2><a href={`#${id}`}>See all {count} {id} <ArrowRight /></a></header>{children}</section>;
}

export function QuestionRow({ item }: { item: EntityLink }) {
  return <Link className="question-row" href={item.href}><span>›</span><strong>{item.title}</strong><b>›</b></Link>;
}

export function WhyItMatters() {
  return <aside className="why"><Lightbulb /><div><strong>Why this matters</strong><p>Inflation is central to understanding purchasing power and Argentina&apos;s nominal stabilization process.</p></div></aside>;
}

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { EntityLink, PlotArtifactRef } from "@/lib/types";

const paths = {
  "headline-vs-core-inflation": ["M8 94 L30 83 L47 75 L65 78 L83 61 L103 65 L120 52 L141 48 L159 25 L174 49 L190 20 L204 49 L222 60 L240 78 L260 86 L278 91", "M8 98 L30 88 L52 86 L72 76 L94 80 L114 68 L136 64 L158 60 L178 54 L196 66 L218 65 L239 78 L260 82 L278 94"],
  "inflation-momentum-monthly-and-3-month-annualized": ["M8 74 L20 53 L29 70 L40 45 L53 66 L65 37 L78 56 L92 44 L105 76 L121 52 L142 57 L155 32 L169 24 L181 55 L195 45 L210 65 L224 59 L238 77 L254 54 L265 91 L278 96"],
} as const;

function LineChart({ slug }: { slug: keyof typeof paths }) {
  return <svg viewBox="0 0 286 128" role="img" aria-label="Illustrative placeholder line chart"><g className="grid"><path d="M5 20H281M5 48H281M5 76H281M5 104H281" /></g>{paths[slug].map((d, i) => <path key={d} className={`line l${i}`} d={d} />)}<text x="10" y="123">2022</text><text x="112" y="123">2024</text><text x="250" y="123">2025</text></svg>;
}

function DriverChart() {
  return <svg viewBox="0 0 286 128" role="img" aria-label="Illustrative placeholder diverging bar chart"><g className="grid"><path d="M5 20H281M5 48H281M5 76H281M5 104H281" /></g>{Array.from({ length: 22 }, (_, i) => { const h = 15 + (i * 13) % 42; return <g key={i}><rect x={8+i*12} y={75-h} width="4" height={h} className="bar b0"/><rect x={12+i*12} y={75-h*.65} width="4" height={h*.65} className="bar b1"/><rect x={16+i*12} y="75" width="4" height={8+(i%4)*4} className="bar b2"/></g>;})}<text x="35" y="123">2023</text><text x="135" y="123">2024</text><text x="235" y="123">2025</text></svg>;
}

function PlotArtifactImage({ artifact }: { artifact: PlotArtifactRef }) {
  return <img className="plot-artifact-image" src={artifact.svg} alt={artifact.altText} />;
}

export function GenericChartPlaceholder() { return <div className="generic-chart"><span /><span /><span /><span /></div>; }

export function isProminentChart(item: EntityLink) {
  return item.artifact?.publicationStatus !== "quarantine";
}

export function ChartPreview({ item }: { item: EntityLink }) {
  if (item.artifact) return <PlotArtifactImage artifact={item.artifact} />;
  const slug = item.slug ?? "";
  if (slug in paths) return <LineChart slug={slug as keyof typeof paths} />;
  if (slug === "inflation-driver-decomposition") return <DriverChart />;
  return <GenericChartPlaceholder />;
}

function artifactCaption(artifact: PlotArtifactRef) {
  if (artifact.publicationStatus === "quarantine") {
    return `Editorial QA: quarantined${artifact.qaNote ? ` · ${artifact.qaNote}` : ""}`;
  }
  const stale = artifact.freshnessState === "stale_warning" ? " · stale source snapshot" : "";
  const historical = artifact.publicationStatus === "historical" ? "Historical evidence · " : "";
  return `${historical}Data through ${artifact.dataAsOf}${stale}`;
}

export function ChartCard({ item, displayTitle }: { item: EntityLink; displayTitle?: string }) {
  const isDummy = item.slug === "inflation-driver-decomposition" || (item.slug ? item.slug in paths : false);
  const caption = item.artifact ? artifactCaption(item.artifact) : (isDummy ? "Illustrative placeholder" : "Chart preview pending");
  return <article className="chart-card"><div className="chart-title"><h3>{displayTitle ?? item.title}</h3><p>{caption}</p></div><ChartPreview item={item} /><Link href={item.href}>View chart <ArrowRight /></Link></article>;
}

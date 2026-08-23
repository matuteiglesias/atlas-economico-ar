import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { EntityLink, PlotArtifactRef } from "@/lib/types";

type MaterializedChart = EntityLink & { artifact: PlotArtifactRef };

function PlotArtifactImage({ artifact }: { artifact: PlotArtifactRef }) {
  return <img className="plot-artifact-image" data-plot-render="embed" src={artifact.svg} alt={artifact.altText} />;
}

export function isProminentChart(item: EntityLink) {
  return item.artifact?.disposition.prominent === true;
}

function isCardEvidence(item: EntityLink): item is MaterializedChart {
  const disposition = item.artifact?.disposition;
  return Boolean(
    item.artifact &&
    (disposition?.prominent || disposition?.state === "REFERENCE" || disposition?.state === "HISTORICAL"),
  );
}

function evidencePriority(item: MaterializedChart) {
  const { disposition } = item.artifact;
  if (disposition.primaryEvidence) return 0;
  if (disposition.prominent) return 1;
  if (disposition.state === "REFERENCE") return 2;
  if (disposition.state === "HISTORICAL") return 3;
  return 4;
}

export function evidenceFirstCharts(items: EntityLink[]) {
  return items.filter(isCardEvidence).sort((a, b) => evidencePriority(a) - evidencePriority(b));
}

function providerLabel(provider: string) {
  if (provider === "bcra_monetarias_v4") return "BCRA";
  if (provider === "datos_argentina") return "Datos Argentina";
  return provider === "multiple" ? "Multiple sources" : provider.replaceAll("_", " ");
}

function sourceLabel(artifact: PlotArtifactRef) {
  const providers = artifact.sources?.map((source) => providerLabel(source.provider)) ?? [providerLabel(artifact.source.provider)];
  return [...new Set(providers)].join(", ");
}

function artifactCaption(artifact: PlotArtifactRef) {
  const provenance = `Data through ${artifact.dataAsOf} · Source: ${sourceLabel(artifact)}`;
  const { disposition } = artifact;
  if (disposition.state === "QUARANTINE") {
    return `Editorial QA: quarantined · ${provenance}${disposition.note ? ` · ${disposition.note}` : ""}`;
  }
  if (disposition.state === "SUPERSEDED") {
    return `Superseded evidence · ${provenance}${disposition.note ? ` · ${disposition.note}` : ""}`;
  }
  if (disposition.state === "REFERENCE") {
    return `Reference evidence · ${provenance}`;
  }
  const stale = artifact.freshnessState === "stale_warning" ? " · stale source snapshot" : "";
  const historical = disposition.state === "HISTORICAL" ? "Historical evidence · " : "";
  return `${historical}${provenance}${stale}`;
}

type ChartChrome = "card" | "page";

export function ChartCard({ item, displayTitle, chrome = "card" }: { item: EntityLink; displayTitle?: string; chrome?: ChartChrome }) {
  if (!item.artifact) return null;
  const caption = artifactCaption(item.artifact);
  return <article className={`chart-card chart-card-${chrome}`} data-plot-chrome={chrome}>
    {chrome === "card"
      ? <div className="chart-title"><h3>{displayTitle ?? item.title}</h3><p>{caption}</p></div>
      : <div className="chart-meta"><p>{caption}</p></div>}
    <PlotArtifactImage artifact={item.artifact} />
    {chrome === "card" && <Link href={item.href}>View chart <ArrowRight /></Link>}
  </article>;
}

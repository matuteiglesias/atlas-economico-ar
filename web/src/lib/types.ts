export type EntityKind = "region" | "topic" | "question" | "indicator" | "chart";

export interface PlotArtifactRef {
  chartSpecId: string;
  frameId: string;
  renderer: string;
  dataAsOf: string;
  generatedAt: string;
  svg: string;
  png: string;
  altText: string;
  freshnessState: string;
  indicatorIds: string[];
  seriesIds: string[];
  snapshotSha256: Record<string, string>;
  source: {
    provider: string;
    providerSeriesId: string;
    sourceUnit?: string | null;
    normalization: { kind: string; factor?: number };
  };
}

export interface EntityLink {
  id?: string;
  kind?: EntityKind;
  slug?: string;
  title: string;
  href: string;
  distance?: number;
  artifact?: PlotArtifactRef;
}

export interface Region extends EntityLink {
  id: string;
  kind: "region";
  slug: string;
  populated?: boolean;
  dek?: string;
}

export interface Connection {
  relation_id: string;
  relation_type: string;
  direction: "incoming" | "outgoing";
  entity: EntityLink;
}

export interface TopicPage extends EntityLink {
  id: string;
  kind: "topic";
  slug: string;
  dek: string | null;
  intro: string | null;
  region: Region;
  breadcrumbs: EntityLink[];
  connections: Connection[];
  questions: EntityLink[];
  indicators: EntityLink[];
  charts: EntityLink[];
  nearby: EntityLink[];
  counts: { connections: number; questions: number; indicators: number; charts: number };
}

export interface Navigation {
  regions: Region[];
  counts: Record<EntityKind, number>;
}

export interface SearchItem extends EntityLink {
  id: string;
  kind: EntityKind;
  slug: string;
  regionId: string;
  text: string;
}

export interface RegionPage extends Region {
  intro: string | null;
  breadcrumbs: EntityLink[];
  stats: Record<"topics" | "questions" | "indicators" | "charts" | "relations", number>;
  topics: EntityLink[];
  questions: EntityLink[];
  indicators: EntityLink[];
  charts: EntityLink[];
}

export interface EntityPage extends EntityLink {
  id: string;
  kind: "question" | "indicator" | "chart";
  slug: string;
  dek: string | null;
  intro: string | null;
  region: Region;
  breadcrumbs: EntityLink[];
  topics?: EntityLink[];
  questions?: EntityLink[];
  indicators?: EntityLink[];
  charts?: EntityLink[];
  nearby: EntityLink[];
  counts: Record<string, number>;
  topic?: EntityLink;
  frequency?: string;
  unitSemantics?: string;
  seriesBindingStatus?: string;
}

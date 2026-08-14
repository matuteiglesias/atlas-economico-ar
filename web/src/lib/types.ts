export type EntityKind = "region" | "topic" | "question" | "indicator" | "chart";

export interface EntityLink {
  id?: string;
  kind?: EntityKind;
  slug?: string;
  title: string;
  href: string;
  distance?: number;
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

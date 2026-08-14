# Compiled data contract — frontend expectations

The fixture in `fixtures/site-data/` is authoritative.

## Public kinds

`region | topic | question | indicator | chart`

Every public entity has:

```ts
type EntityRef = {
  id: string
  kind: "region" | "topic" | "question" | "indicator" | "chart"
  slug: string
  title: string
  href: string
}

type NearbyRef = EntityRef & { distance: number }
```

Full page objects additionally include `dek`, `intro`, region/breadcrumb context, and kind-specific joins.

## Region page

Important fields:
- `populated`
- `stats`
- `topics`
- `questions`
- `indicators`
- `charts`
- `localGraph`

Unpopulated regions are real public pages and must render intentionally.

## Topic page

Important fields:
- `region`
- `breadcrumbs`
- `connections[]` with:
  - `relation_id`
  - `relation_type`
  - `direction`
  - `entity`
- `questions`
- `indicators`
- `charts`
- `nearby`
- `counts`

## Question page

Important fields:
- `questionFamily`
- `topics`
- `indicators`
- `charts`
- `nearby`
- `counts`

## Indicator page

Important fields:
- `topic`
- `unitSemantics`
- `frequency`
- `seriesBindingStatus`
- `charts`
- `derivedAsInput`
- `derivedAsOutput`
- `nearby`
- `counts`

Do not expose `seriesBindingStatus` as an alarming error. It is expected in v0.1.

## Chart page

Important fields:
- `questions`
- `topics`
- `indicators`
- `referenceFrameIds`
- optional `chartSpec`:
  - `id`
  - `templateId`
  - `refreshPolicy`
  - `dataAsOfPolicy`
- `nearby`
- `counts`

A missing ChartSpec is allowed. A chart page still renders.

## Global files

- `navigation.json` → left Explore navigation and global counts
- `search-index.json` → command palette
- `stats.json` → homepage/global counts
- `manifest.json` → compatibility and route-count checks
- `graph.json` → **not for normal entity page joins**
- `editorial-gaps.json` → developer/editorial cleanup queue, not public UI

## Fixture invariants

Current fixture:
- 6 regions
- 25 topics
- 18 questions
- 42 indicators
- 52 charts
- 143 public entities
- 303 graph edges
- 1 populated vertical

See `reference/expected-counts.json`.

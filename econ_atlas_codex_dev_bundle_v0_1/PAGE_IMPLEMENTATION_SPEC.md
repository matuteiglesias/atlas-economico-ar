# Page implementation spec

The frozen grammar under `contracts/frontend/` is authoritative. This file adds implementation detail.

## Shared desktop shell

At wide desktop widths, target:

```text
┌───────────────────────────────────────────────────────────────┐
│ Site header                                                   │
├──────────────┬────────────────────────────────┬───────────────┤
│ Explore rail │ Main editorial reading surface │ Context rail  │
└──────────────┴────────────────────────────────┴───────────────┘
```

Target proportions close to the reference image:
- Explore rail: ~270–300 px
- Context rail: ~300–330 px
- Main: flexible, generous
- Overall content should comfortably fill a 1536 px viewport

The rails may be sticky below the site header if this remains robust.

## Topic — primary acceptance page

`/topics/inflation` must be the closest visual match to the reference.

Main column:
1. eyebrow `TOPIC`
2. title `Inflation`
3. dek
4. subtle topic/area pills only if supported by real data; do not invent fake taxonomies
5. divider
6. `Questions people ask`
7. up to 6 question rows
8. divider
9. `See it in the data`
10. 3 chart preview cards:
   - Headline vs Core Inflation
   - Inflation Momentum
   - Inflation Driver Decomposition
11. optional restrained `Why this matters` note only if it can be sourced from current `dek`/relationships without invented claims

Right rail:
- counts for questions/charts/indicators
- related topics from direct semantic connections first
- `Used by these questions` / backlinks
- no ontology IDs

Left rail:
- six Areas
- populated Area visually active
- quick links:
  - All Questions
  - All Charts
  - All Indicators
  - Topics
  - Search
  - Atlas
- compact atlas description at bottom

## Question

Human-curiosity-first.
- title is the question itself
- `dek` if available
- `Ideas involved`
- `Ways to look at it` = chart cards
- `Measurements underneath`
- related/nearby in context rail

## Chart

- large placeholder/preview surface near top
- actual dummy SVG only for the three chosen charts
- all other charts use one consistent placeholder
- show `What to look at` using `dek`
- questions answered
- topics
- indicators
- related charts from `nearby`

Do not imply that dummy data is real. Dummy charts must be visibly labeled `Illustrative placeholder`.

## Indicator

Reference-oriented.
- what it measures (`dek` if present; otherwise title + technical facts only)
- frequency
- unit semantics converted to human-readable label
- related Topic
- charts using it
- derived-use metadata may be placed in secondary reference UI

## Area

Populated:
- mission/dek
- counts
- key questions
- core topics
- selected chart cards
- browse-all lists

Unpopulated:
- polished empty state
- area mission/dek
- text such as `This area is part of the frozen atlas structure and will populate as its knowledge vertical is compiled.`
- no fake counts or invented content

## Home

Editorial orientation, not a marketing landing page:
- Argentina / Economic Atlas statement
- six Areas
- current populated area highlighted
- selected Questions
- selected Charts
- global counts
- quick entry to `/topics/inflation`

## Atlas

v0.1 is a structured browse surface, **not** a graph visualization.
- six Areas
- counts/status
- populated Area contents
- links to Topics/Questions/Charts

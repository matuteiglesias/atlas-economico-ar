# Approved frontend stack

Use current stable releases at implementation time.

## Core

- **Next.js App Router**
- **TypeScript**, strict mode
- **React**
- **Tailwind CSS**
- **pnpm**
- **Lucide React** for icons

## Accessible UI primitives

`shadcn/ui` is allowed for a small number of behavioral primitives where it saves routine accessibility work,
especially:
- Command / command palette
- Dialog
- Sheet for mobile Explore navigation
- Tooltip / Separator if useful

Do not adopt a full prebuilt visual theme. Editorial cards/layout should remain custom.

## Rendering model

Prefer static generation.

All `[slug]` routes must enumerate compiled slugs with `generateStaticParams`.
The intended release may use `output: "export"` because the current product needs no request-time server state.

## Data access

The canonical repo-level input is `site-data/`.

Recommended implementation:
- a prebuild/dev sync step copies repo-root `site-data/` into a generated folder inside `web/`, or
- a build-time-only filesystem reader resolves it directly.

Whichever path is chosen:
- components receive typed objects;
- no runtime HTTP fetch is required;
- no browser code loads dozens of individual JSON files to reconstruct a page.

## Typography

No font dependency is required for v0.1.

Use a restrained editorial pairing:
- serif stack for brand and major page headings (`Georgia`, `ui-serif`, serif fallback);
- system sans stack for UI/body.

This avoids a remote-font dependency while preserving the mockup's publication character.

## Charts

**Do not install a chart library in v0.1.**

Implement three deterministic inline-SVG dummy chart previews:
1. Headline vs Core Inflation — two-line chart.
2. Inflation Momentum — one-line chart.
3. Inflation Driver Decomposition — stacked/diverging bar-style chart.

All other chart cards/pages use a polished generic placeholder derived from ChartSpec metadata.

## Testing / quality

Required scripts:
- `pnpm lint`
- `pnpm typecheck`
- `pnpm build`

A lightweight test runner may be added if useful, but do not make test-framework setup larger than the feature
being tested. The final build must prove all expected static routes can be generated.

# Argentina Economic Atlas web app

Static Next.js frontend for the Argentina Economic Atlas. Pages are generated from the compiled `web/site-data/` deployment snapshot; the browser does not call a data API or fetch entity JSON at runtime.

## Requirements

- Node.js 22 or newer
- pnpm 10

## Local development

From `web/`:

```bash
pnpm install --frozen-lockfile
pnpm dev
```

The development server is available at `http://localhost:3000`. Changes to `site-data/` are read when a page is rebuilt; restart the development server after a full data refresh.

## Validate and build

```bash
pnpm check
```

This verifies the compiled data contract, runs ESLint and TypeScript, creates the production static export, and confirms that all 145 public routes exist. The deployable output is written to `web/out/` and can be hosted by any static-file server.

Individual commands are also available:

```bash
pnpm verify:data
pnpm lint
pnpm typecheck
pnpm build
pnpm verify:routes
```

`verify:routes` must run after `pnpm build` because it audits the generated `out/` directory.

## Refreshing data

The canonical input remains the repository-level `site-data/` directory. After regenerating it with the knowledge compiler workflow, refresh the deployable snapshot and validate it:

```bash
pnpm sync:data
pnpm check
```

Commit the refreshed `web/site-data/` snapshot with the compiler output. This explicit copy keeps Vercel builds rooted at `web/` independent from parent-directory access. Do not edit either set of generated page JSON by hand or add browser-side joins against `graph.json`.

## Vercel deployment

Create or import the Vercel project with these settings:

- **Root Directory:** `web`
- **Framework Preset:** Next.js (auto-detected)
- **Install Command:** automatic (`pnpm install`)
- **Build Command:** automatic (`next build`)
- **Output Directory:** automatic; do not override it
- **Environment variables:** none

The checked-in `web/site-data/` snapshot is intentionally inside the Root Directory, so no dashboard option for reading source files outside `web/` is required.

With the Vercel CLI authenticated and the project linked, run a Preview deployment from `web/`:

```bash
pnpm dlx vercel
```

After reviewing the Preview URL, promote the approved build with:

```bash
pnpm dlx vercel --prod
```

For Git-based deployments, connect this repository in the Vercel dashboard, retain `web` as the Root Directory, and set `main` as the Production Branch. Pull requests and non-production branches then receive Preview deployments, while pushes to `main` produce Production deployments.

## Static and placeholder behavior

- The app retains `output: "export"` and `trailingSlash: true`; there is no application server, database, authentication layer, or runtime data API.
- Chart surfaces are deterministic illustrative previews, not real time-series plots. Cards label illustrative fixtures and otherwise show that a preview or data integration is pending.
- Empty economic areas are intentional placeholders for knowledge verticals that have not yet been compiled.

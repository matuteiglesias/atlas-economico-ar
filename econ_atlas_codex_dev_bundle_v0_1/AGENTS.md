# AGENTS.md — Argentina Economic Atlas frontend

## Mission

Build the website described by the frozen frontend contract and visual reference. Do not redesign the
product architecture while implementing it.

## Autonomy

You may:
- make routine component/API/CSS implementation decisions;
- refactor locally when it reduces duplication;
- add tests needed by the active PR packet;
- choose exact spacing within the visual system when the target image does not decide it;
- use accessible primitives from the approved stack.

You must stop and ask before:
- changing the public data model or compiler output;
- changing public route names;
- adding a database/API/server runtime;
- adding a graph visualization/layout system;
- adding real data-series fetching;
- adding a charting library;
- adding a large new dependency not listed in `TECH_STACK.md`;
- changing scope to include news, provenance, trails, authentication, CMS, or real plot pipelines;
- modifying `argentina_econ_semantic_scope_v0_1/`, `econ_knowledge_compiler_v0_1/`, or knowledge bundles.

## PR discipline

Implement one `tasks/PR-*.yaml` packet at a time.

Within a packet:
1. inspect existing code;
2. write a concise plan;
3. implement to completion;
4. run all checks named in the packet;
5. inspect representative pages;
6. keep handwritten code delta around or below 1,000 net LOC when practical;
7. stop at the human gate.

Do not split into tiny commits merely to reduce apparent LOC. Prefer coherent work.

## Data rules

- `site-data/` is already compiled.
- React components do not traverse `graph.json` to build ordinary Topic/Question/Indicator/Chart page joins.
- Entity pages load their page-shaped JSON file.
- `graph.json` is reserved for `/atlas` or future global exploration only.
- Do not display ontology IDs in the normal UI.
- Do not invent missing economic content.
- Missing `dek`/`intro` is a legitimate state; use restrained presentation, not generic filler prose.

## Visual rules

Match `reference/visual-target-inflation-topic.png` in spirit and structure:
- serious editorial typography;
- white/off-white canvas;
- fine neutral borders;
- restrained blue accent;
- left Explore rail;
- generous central reading column;
- right contextual rail on wide screens;
- dense but quiet metadata;
- chart previews are the most visually expressive cards.

Avoid:
- SaaS gradient aesthetics;
- giant rounded cards everywhere;
- dark dashboard styling;
- force-directed graph visuals;
- excessive shadows;
- decorative animation.

## Hard out of scope

- Trails
- XY atlas coordinates
- full graph UI
- live news
- provenance UI
- database
- CMS
- auth
- API layer
- real time-series loading
- real chart calculations
- Gold100
- other semantic verticals

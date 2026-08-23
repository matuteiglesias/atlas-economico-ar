# PlotArtifact presentation variants

Status: executable presentation contract for Figure Grammar v0.2.

A materialized Atlas figure has one semantic/rendering identity but two presentation contexts.

```text
PlotIntent + resolved measurements + ReferenceFrame + ChartSpec
                         ↓
                 canonical render
                         ↓
       self-describing review PlotArtifact
                 /               \
        curation / AI         viewport projection
                                   ↓
                             site embed variant
```

## Canonical review variant

`artifact.outputs.svg` and `artifact.outputs.png` are the canonical self-describing rendered evidence.

They intentionally include:

- PlotIntent title;
- frame/unit subtitle;
- axes, marks, legend and annotations;
- source/data-through footer.

This is the variant inspected by figure-curation agents and humans. Exact rendered hashes in `figures/curation_reviews.yaml` refer to these canonical outputs. A presentation-only site change must not rewrite them or invalidate their review evidence.

## Site embed variant

`artifact.embed_outputs.svg` and `artifact.embed_outputs.png` are derived from the canonical outputs by a deterministic viewport crop in `figures/materialize_embed.py`.

The embed projection removes only figure-owned editorial chrome:

- title;
- frame/unit subtitle;
- source/footer line.

It does not redraw or transform data. Axes, plotted marks, legends, annotations, scales and economic content remain those of the canonical render.

The host page owns the removed information using the Atlas web design system:

- page/card title;
- publication/freshness state;
- data-through date;
- source label;
- surrounding navigation and explanatory context.

This prevents a static PlotArtifact from competing typographically with the page that embeds it.

## Consumer rule

Curation/review consumers use `outputs`.

The publication compiler and static web surface use `embed_outputs` and expose:

```json
"presentation": {
  "variant": "embed",
  "chromeOwner": "page"
}
```

Frontend code must not choose between review and embed files heuristically. The compiler owns that projection.

## Invariants

1. One PlotIntent/ChartSpec/measurement/frame identity underlies both variants.
2. Canonical review SVG/PNG bytes are untouched by embed generation.
3. Embed generation may change viewport/raster crop only; it may not redraw data or alter semantics.
4. Every materialized PlotArtifact published to the site must have both review and embed SVG/PNG files.
5. Web publication verification must prove deployed `/plots/*` bytes equal the embed variant and differ from the self-describing review variant.
6. Curation hashes continue to bind to the canonical review outputs, not to presentation projections.

If a future host requires a materially different visual grammar rather than different surrounding chrome, that is not an embed projection. It requires an explicit renderer/ChartSpec design decision.

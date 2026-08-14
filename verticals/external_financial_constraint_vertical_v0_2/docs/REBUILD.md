# Rebuild with Nominal Stabilization

From repository root, after placing this ZIP in `bundles/verticals/` and extracting a working copy if you want to use its
editorial file directly:

```bash
rm -rf site-data-next

ekc compile \
  --scope argentina_econ_semantic_scope_v0_1 \
  --vertical bundles/verticals/nominal_stabilization_vertical_v0_1.zip \
  --vertical bundles/verticals/external_financial_constraint_vertical_v0_2.zip \
  --editorial external_financial_constraint_vertical_v0_2/editorial/atlas_en_v0_2.yaml \
  --output site-data-next
```

Inspect:

```bash
cat site-data-next/stats.json
cat site-data-next/manifest.json
tree -L 2 site-data-next
```

After human review:

```bash
mv site-data site-data-prev
mv site-data-next site-data
```

Then run the existing web lint/typecheck/build and representative-page smoke tests.
Keep `site-data-prev` until the web build and navigation review pass.

# Argentina Economic Knowledge Layer
## Slice Vertical: Nominal Stabilization v0.1

This bundle is the first fully populated semantic vertical under the frozen scope architecture.

### Object populations

| Class | Count |
|---|---:|
| Concepts | 25 |
| Relations | 52 |
| QuestionIntents | 18 |
| ReferenceFrames | 9 |
| CanonicalIndicators | 42 |
| Series registrations | **0 (deliberately deferred)** |
| DerivedIndicators | 12 |
| PlotIntents | 52 |
| ChartSpecs | 32 |
| **Curated objects total** | **242** |

### Evidence

- `evidence/media_nominal_subset.csv`: 260 selected rows from the 500-headline corpus.
- `evidence/media_summary.json`: counts and non-exclusive theme diagnostics.
- `evidence/imf_evidence_map.yaml`: page-level map of the IMF report used for semantic/mechanism enrichment.

### Important design decision

Technical Series objects are omitted. CanonicalIndicators state what must be measured; later, a global data-source/series registry session will bind each measurement to real series IDs.

### Review status

The bundle is machine-valid and internally linked, but it is an **agent-generated v0.1 candidate**. Human review should focus on:
- canonical concept naming;
- relation epistemic typing;
- whether any concepts belong in a neighboring slice;
- methodology of more contestable DerivedIndicators;
- Gold-candidate PlotIntent prioritization.

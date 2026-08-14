# Argentina Economic Atlas — Frontend Contract v0.1

Status: **FROZEN FOR INITIAL NEXT.JS IMPLEMENTATION**

This bundle freezes the public information architecture, page grammar, route vocabulary,
component responsibilities, navigation rules, editorial-vs-derived boundary, and the read-model
contract expected from `site-data/`.

It intentionally does **not** specify:
- chart rendering implementation;
- real time-series bindings;
- atlas XY positions;
- trails/guided journeys;
- provenance UI;
- CMS/database/authentication;
- news integration;
- graph visualization implementation.

The frontend should be a thin renderer over the compiled read model.

Public vocabulary:
- Region/Slice → **Area**
- Concept → **Topic**
- QuestionIntent → **Question**
- CanonicalIndicator → **Indicator**
- PlotIntent → **Chart**

Supporting ontology objects remain internal unless a page explicitly needs them.

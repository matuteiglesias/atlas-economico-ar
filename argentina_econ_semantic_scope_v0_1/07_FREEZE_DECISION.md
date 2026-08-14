# Freeze Decision

Version: `0.1`

The scope to be used by all later vertical builds is frozen as:

- six semantic regions;
- one cross-cutting structural-transformation overlay;
- one shared ontology contract;
- one shared epistemic/source policy;
- one common sequential build contract;
- explicit cross-slice ports followed by one global integration pass.

## What later verticals may do

- create Concept, Relation, QuestionIntent, CanonicalIndicator, Series, DerivedIndicator,
  PlotIntent and (later) ChartSpec instances;
- propose new cross-slice ports;
- emit unresolved decisions;
- add source provenance;
- enrich existing approved objects.

## What later verticals may not do silently

- add/remove/redefine semantic regions;
- turn the structural overlay into a standalone silo;
- redefine global data classes;
- redefine relation semantics;
- collapse Concept and Series;
- infer causality from media co-occurrence;
- create derived indicators without methodology;
- bypass the staged dependency order;
- let available API series dictate the ontology.

## Versioning

- instance additions: no scope version bump required;
- new global enum/relation type: minor version bump;
- changed slice boundary/topology/class model: new scope version.

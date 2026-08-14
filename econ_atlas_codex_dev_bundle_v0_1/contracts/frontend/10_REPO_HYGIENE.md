# Repository hygiene recommendation

Do not move `econ_knowledge_compiler_v0_1/` immediately after an editable pip install unless you reinstall it.

Suggested current layout:

```text
econ-kb/
├── argentina_econ_semantic_scope_v0_1/   # authored canonical scope
├── econ_knowledge_compiler_v0_1/         # live editable Python package
├── site-data/                             # generated compiler output
├── bundles/
│   ├── scope/
│   ├── verticals/
│   └── releases/
└── [future web app]
```

Move only transport/release ZIPs now:

```bash
mkdir -p bundles/{scope,verticals,releases}

mv argentina_econ_semantic_scope_v0_1.zip bundles/scope/
mv nominal_stabilization_vertical_v0_1.zip bundles/verticals/
mv econ_knowledge_compiler_v0_1.zip bundles/releases/
```

Keep the extracted semantic scope because it is authored source material.
Keep `site-data/` clearly understood as regenerable output.

Later, after the web app exists, a stronger repository structure can be decided without blocking implementation.

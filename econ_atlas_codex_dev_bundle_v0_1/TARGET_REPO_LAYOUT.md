# Target repository layout

Starting repository:

```text
econ-kb/
├── argentina_econ_semantic_scope_v0_1/
├── econ_knowledge_compiler_v0_1/
├── site-data/
├── bundles/
└── ...
```

Add:

```text
econ-kb/
└── web/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx
    │   │   ├── atlas/page.tsx
    │   │   ├── areas/[slug]/page.tsx
    │   │   ├── topics/[slug]/page.tsx
    │   │   ├── questions/[slug]/page.tsx
    │   │   ├── indicators/[slug]/page.tsx
    │   │   └── charts/[slug]/page.tsx
    │   ├── components/
    │   │   ├── shell/
    │   │   ├── entities/
    │   │   ├── cards/
    │   │   ├── charts/
    │   │   └── search/
    │   ├── lib/
    │   │   ├── site-data/
    │   │   ├── types.ts
    │   │   └── format.ts
    │   └── generated/
    │       └── site-data/       # if sync strategy is used; generated
    ├── scripts/
    ├── public/
    ├── package.json
    └── next.config.*
```

Do not move or modify the compiler or ontology to make the frontend easier.

For v0.1, it is acceptable to keep `site-data/` versioned even though it is regenerable. That keeps the frontend
build hermetic and makes the semantic compiler a separate upstream concern.

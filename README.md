# Atlas Económico de Argentina

Atlas explorable de la economía argentina que conecta preguntas económicas, conceptos, indicadores y visualizaciones de datos.

## Estado

Versión inicial enfocada en **Estabilización Nominal**.

El proyecto se construye a partir de una capa de conocimiento estructurada que se compila a un modelo de lectura estático consumido por el frontend.

## Estructura principal

- `argentina_econ_semantic_scope_v0_1/`: alcance y contratos semánticos.
- `econ_knowledge_compiler_v0_1/`: compilador de conocimiento.
- `site-data/`: artefactos compilados para el frontend.
- `econ_atlas_frontend_contract_v0_1/`: gramática y contratos de interfaz.
- `econ_atlas_codex_dev_bundle_v0_1/`: bundle de implementación para Codex.

## Próximo paso

Implementar el frontend Next.js del Atlas Económico de Argentina, comenzando por la vertical de Estabilización Nominal.

# Atlas Económico de Argentina

Atlas explorable de la economía argentina que conecta preguntas económicas, conceptos, indicadores y visualizaciones de datos.

## Estado

El frontend estático en Next.js está implementado en `web/` y se despliega desde ese directorio. Consume una copia compilada de `web/site-data/`; el navegador no consulta una API económica ni reconstruye relaciones entre entidades en tiempo de ejecución.

La capa de conocimiento incluye las verticales de **Estabilización Nominal** y **Restricción Financiera Externa**. El compilador transforma sus contratos semánticos en datos de lectura y páginas estáticas, y GitHub Actions verifica los contratos, el build y las rutas publicadas.

## Estructura principal

- `verticals/`: verticales económicas y contratos de contenido.
- `argentina_econ_semantic_scope_v0_1/`: alcance y contratos semánticos compartidos.
- `econ_knowledge_compiler_v0_1/`: compilador de conocimiento.
- `series/`: contratos y snapshots de series económicas.
- `figures/`: especificaciones y herramientas de figuras.
- `plot-artifacts/`: gráficos estáticos generados para publicación.
- `site-data/`: artefactos compilados canónicos.
- `web/`: aplicación Next.js y copia desplegable de los datos compilados.

## Desarrollo y validación

Las instrucciones completas están en [`web/README.md`](web/README.md). Desde `web/`:

```bash
pnpm install --frozen-lockfile
pnpm check
pnpm dev
```

`pnpm check` valida los datos compilados, ejecuta ESLint y TypeScript, genera la exportación estática y comprueba sus rutas.

## Dirección actual

Ampliar de forma controlada la cobertura de series y gráficos auténticos mediante el pipeline existente, preservando la arquitectura estática y offline después de la adquisición de datos.

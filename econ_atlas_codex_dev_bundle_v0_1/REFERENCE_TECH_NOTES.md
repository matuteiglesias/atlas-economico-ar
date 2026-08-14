# Technical reference notes

These are implementation guardrails, not product requirements.

- Next.js App Router supports pre-generating dynamic routes with `generateStaticParams`.
- Static export can emit HTML/CSS/JS for routes at build time when request-time-only features are avoided.
- Tailwind supports container queries if component-level responsiveness is useful.
- shadcn/ui may be used selectively for behavioral primitives; do not import its visual language wholesale.

Codex should consult current official documentation if framework behavior differs at implementation time.

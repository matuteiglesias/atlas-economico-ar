# Release checklist

1. `site-data/` fixture/current compiled output matches compiler schema 0.1.
2. Web build consumes current `site-data/`.
3. `pnpm lint`.
4. `pnpm typecheck`.
5. `pnpm build`.
6. Route verifier passes.
7. Primary screenshot review passes.
8. Representative page review passes.
9. Mobile smoke passes.
10. Search smoke passes.
11. Dummy chart disclaimer present on full Chart pages.
12. No runtime data API/network dependency.
13. No out-of-scope scope creep.
14. Web README explains:
    - install
    - dev
    - build
    - how to refresh `site-data`
    - placeholder-chart limitation
15. Human marks release approved.

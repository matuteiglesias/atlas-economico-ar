# Human review lane

The human does not need to review every file. Review the product surface at bounded gates.

## Gate 1 — after PR-01

Spend ~5–10 minutes on:
- `/topics/inflation` at 1536×1024
- compare with `reference/visual-target-inflation-topic.png`
- check:
  - overall proportions
  - typography character
  - border/shadow restraint
  - chart-card quality
  - left/right rail usefulness
  - whether it feels like a publication, not a dashboard

Decision:
- approve visual grammar;
- or request one focused visual correction pass.

Do not bikeshed unseen pages yet.

## Gate 2 — after PR-02

Spot-check:
- `/areas/nominal-stabilization`
- `/topics/inflation`
- `/questions/what-is-driving-monthly-inflation`
- `/indicators/monthly-headline-cpi-inflation`
- `/charts/inflation-driver-decomposition`
- `/areas/external-financial-constraint`

Check:
- navigation feels natural;
- pages do not look like raw documentation;
- content corresponds to compiled JSON;
- empty Area is elegant;
- no invented claims.

## Gate 3 — after PR-03

Check:
- Cmd/Ctrl+K
- mobile Explore drawer
- mobile Topic and Question page
- keyboard focus
- long titles
- context rail collapse behavior

## Gate 4 — release

Run through the five-step semantic journey:

`Inflation → What is driving monthly inflation? → Inflation-driver decomposition → Monthly headline CPI inflation → Headline inflation`

If that journey feels coherent and the visual target still holds, release.

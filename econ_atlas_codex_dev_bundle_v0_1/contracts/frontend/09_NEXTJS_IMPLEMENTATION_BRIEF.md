# Implementation brief for the next session

The next task may be treated as mechanical implementation.

## Inputs
- compiled `site-data/`;
- this frontend contract;
- approved visual mockup/aesthetic direction.

## First implementation milestone

Build a working shell with:
- `/`
- `/atlas`
- `/areas/[slug]`
- `/topics/[slug]`
- `/questions/[slug]`
- `/indicators/[slug]`
- `/charts/[slug]`

Use static generation from compiled JSON.

Implement:
- shared shell;
- breadcrumbs;
- Explore navigation;
- right Context Rail;
- entity headers;
- Questions / Topics / Charts / Indicators lists/cards;
- command/search palette;
- empty states for unpopulated areas;
- chart placeholders based on ChartSpec metadata.

## Success criterion

A user can start at `/topics/inflation` and naturally navigate:

`Topic → Question → Chart → Indicator → Topic`

without any page performing semantic graph joins at runtime.

The app must continue working when additional verticals are compiled into `site-data/` without page redesign.

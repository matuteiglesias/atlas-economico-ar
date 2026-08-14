# Search, responsive behavior, accessibility

## Search

Desktop:
- header search field/button
- `⌘K` / `Ctrl+K` opens palette
- Esc closes
- keyboard up/down + Enter works

Results grouped by kind.
Use `search-index.json` only.

## Responsive

### Wide desktop
Three-zone layout.

### Medium
- left Explore rail may remain
- right Context rail moves below main content or becomes collapsible
- chart grid becomes 2 columns

### Mobile
- no permanent rails
- Explore opens in a Sheet/drawer
- Context sections appear after main content
- chart cards stack
- header search remains accessible
- no horizontal scrolling

## Accessibility

Required:
- semantic landmarks (`header`, `nav`, `main`, `aside`)
- visible focus states
- color is not the sole active-state signal
- all icon-only controls have accessible names
- keyboard navigation for search/dialog
- chart SVG placeholders have `role="img"` + labels or are marked decorative when redundant
- respect `prefers-reduced-motion`
- text contrast suitable for ordinary reading

No elaborate animations are needed.

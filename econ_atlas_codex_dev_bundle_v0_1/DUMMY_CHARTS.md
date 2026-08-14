# Dummy chart specification

Purpose: make the site visually credible before real series are bound.

All dummy charts must include an accessible label and must visibly state **Illustrative placeholder** on their
full Chart page. Card previews may use a small `placeholder` caption.

## 1. Headline vs Core Inflation

Slug:
`headline-vs-core-inflation`

SVG:
- light grid
- x-axis labels: 2022, 2023, 2024, 2025
- two smooth-ish polylines
- headline line higher/more volatile than core
- both decline strongly by 2025
- tiny legend `Headline` / `Core`

## 2. Inflation Momentum

Slug:
`inflation-momentum-monthly-and-3-month-annualized`

SVG:
- one blue line
- fluctuating high values through 2023–24
- pronounced decline into 2025
- optional subtle second thin line if needed to communicate monthly vs 3m, but keep card readable

## 3. Inflation Driver Decomposition

Slug:
`inflation-driver-decomposition`

SVG:
- compact vertical stacked/diverging bars
- categories approximating Core / Food / Regulated / Other
- mixed positive contribution heights
- mild negative segments permitted
- legend small and quiet

## Generic Chart placeholder

Use the chart object's:
- title
- `chartSpec.templateId` when available
- one subtle generic line/grid motif

Do not fabricate numerical values, dates, sources, or claims in generic placeholders.

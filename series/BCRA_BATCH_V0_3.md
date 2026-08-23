# BCRA third six-Series population batch

This tranche was selected after recomputing the live PlotIntent frontier against `main` and scanning all 1,610 BCRA Monetary Statistics v4 catalog rows.

Selected provider IDs: `882`, `893`, `904`, `981`, `992`, and `1003`.

They form one provider-consistent monthly financial-system block (1999-present): total/peso/foreign-currency private credit and total/peso/foreign-currency private deposits, all expressed by the provider in thousands of ARS. The two component identities are explicitly tested.

The batch closes existing demand for real private-credit growth and the foreign-currency deposit share, and supports four narrow publication views on currency composition and intermediation without adding a renderer primitive.

No economic transformation occurs in acquisition. Representation normalization (`thousand ARS -> ARS`) stays in `SeriesBinding`; real growth and shares live in `figures/derived_resolver.py`.

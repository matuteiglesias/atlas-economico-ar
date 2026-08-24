# Adapter assessment — Real Economy official Series

## Classification

**SMALL_DATOS_ARGENTINA_GENERALIZATION_REQUIRED**

This maps directly to final action:

**B. FIRST GENERALIZE EXISTING DATOS ARGENTINA CAPTURE, THEN TRANCHE.**

## Why a new Ministerio adapter is not warranted

Every preferred candidate is addressable by a provider-native Series ID in the Argentina national Series de Tiempo API already represented in the repository as provider `datos_argentina`.

The institutional origin of the data does not create a new transport boundary:

| Layer | Preferred tranche |
|---|---|
| Transport/API provider | Argentina national Series de Tiempo API / Datos Argentina |
| Primary source institution | INDEC |
| Atlas semantic identity | existing `ci.re.*` CanonicalIndicators |

The existing `series/capture.py` contract is conceptually appropriate. It already:

- requests values from the official `/series/` endpoint;
- requests provider metadata separately;
- preserves raw provider bytes;
- normalizes only date/value and technical identity;
- records request locators and retrieval time;
- hashes raw metadata, raw values and normalized snapshot;
- records provider unit/frequency metadata and freshness;
- enforces `economic_transform=none`.

Nothing about GDP, EMAE, IPI or ISAC requires a second HTTP/provider abstraction.

## Why the current implementation still needs a small generalization

The transport is reusable; the **seed milestone freeze is not**.

Current `series/validate.py` intentionally requires:

- exactly three Series;
- exactly one provider named `datos_argentina`;
- the exact expected raw file set;
- the exact expected snapshot/provenance file set.

`series/README.md` likewise documents an exactly-three-Series milestone. `series/capture.py` contains seed-specific assumptions, including refusal to synthesize a raw capture when one Series reaches the 1000-row API page limit.

Those constraints are good historical safeguards, but they prevent a six-Series Real Economy tranche from being added without first changing the capture milestone contract.

## Bounded follow-on implementation

A later implementation PR should generalize the existing Datos Argentina path, not replace it.

Minimum intended shape:

1. preserve the existing provider object and national `/series/` transport;
2. allow the registry to contain more than the original three approved Series;
3. make file-set validation derive from the registry rather than a hard-coded count;
4. keep per-Series frequency/freshness checks and provider metadata requirements;
5. preserve byte-for-byte raw capture and deterministic normalized rebuild;
6. decide explicitly how histories that exceed one provider page are preserved without fabricating one synthetic raw response;
7. retain `economic_transform=none`;
8. preserve primary-source institution separately in registry/provenance metadata if the schema is extended.

The page-limit issue should be checked against the six preferred histories before implementation. Quarterly 2004-present and monthly 2016-present candidates are comfortably below 1000 observations; long-running monthly EMAE is also expected to remain below the current page size, but the capture PR should verify rather than assume.

## What would justify NEW_PROVIDER_ADAPTER_REQUIRED

Only a desired existing CanonicalIndicator whose authoritative source cannot be reproducibly obtained through the national API and instead requires a materially different official contract: for example, a distinct INDEC spreadsheet/API with no national Series representation and a clear analytical advantage.

No preferred first-tranche candidate meets that condition.

## Conclusion

Reuse the current national transport. Remove only the seed-specific implementation freeze necessary to admit approved registry entries. Do not create a Ministerio adapter.

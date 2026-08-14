# Language architecture

The current atlas is not fully language-decoupled. Do not translate canonical vertical YAML in place.

Recommended boundary:

canonical semantic knowledge + locale editorial overlay → compiler → localized site-data + frontend UI locale dictionary → rendered site

Translate public `title`, `dek`, and `intro` in locale overlays keyed by stable IDs.
Keep IDs, relation types, question families, units, frequencies, provider hints, and methodologies stable.
Keep slugs stable in v0.1.

A later compiler revision should ideally add:
1. repeatable `--editorial` inputs merged by ID;
2. explicit `--locale` and `contentLanguage` in the manifest;
3. route slug frozen separately from localized title;
4. locale-clean search text rather than silently appending English raw semantic prose;
5. editorial-gap policy by kind (an intro should not be mandatory for every Indicator);
6. a global ReferenceFrame registry.

`localization/es-AR_translation_skeleton.yaml` defines the safe translation surface without claiming translation is complete.

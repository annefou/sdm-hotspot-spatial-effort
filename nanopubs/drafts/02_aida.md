# 02 — AIDA Sentence

> Pre-flight checklist run against `docs/forrt-form-fields.md` § AIDA sentence on 2026-05-30.
> AIDA pre-write checklist (no numbers, no method names, no cryptic identifiers,
> world-talk, one finding, full stop) run and passed — see notes at the bottom.

**Form heading:** *"AIDA Sentence — Make structured scientific claims following the AIDA model"*
**Template status:** documented in `docs/forrt-form-fields.md` § AIDA sentence.

## Documented field list (paste-verbatim per pre-flight checklist)

| Field label | Field type | Required |
|---|---|---|
| Enter your AIDA sentence here (ending with a full stop) | textarea | yes |
| Select related topics/tags | dropdown | no |
| Relates to this nanopublication | text input | yes |
| Supported by datasets | repeatable group ("+ Add Item") | no |
| Supported by other publications | repeatable group ("+ Add Item") | no |

## Field-by-field draft

### Enter your AIDA sentence here (ending with a full stop) (textarea, required)

Atomic, Independent, Declarative, Absolute. One empirical finding. Ends with a full stop.

```
For Iberian breeding birds on an equal-area sphere grid, biodiversity hotspots derived from species-distribution models with target-group-background sampling-bias correction agree no better with the expert-rangemap gold standard than uncorrected occurrence-count hotspots, and in fact agree worse.
```

Character count: 290.

### Select related topics/tags (dropdown, optional)

Predefined topic vocabulary — open the dropdown and pick whichever of these labels exist:

```
biodiversity; species distribution model; sampling bias; ecology
```

*(If none of these appear in the dropdown, leave empty — skip, optional.)*

### Relates to this nanopublication (text input, required)

URI of the Quote-with-comment published in step 01 (paper-rooted chain). Pull from `nanopubs/PUBLISHED.md` once published.

```
<pending step 01 publication>
```

### Supported by datasets (repeatable group, optional)

DOIs/URLs of datasets that ground the AIDA claim.

- `https://doi.org/10.15468/dl.r8pcat` (GBIF museum-grade Iberian bird occurrences)
- `https://doi.org/10.15468/dl.e9xv7p` (GBIF all-observations Iberian bird occurrences)

> **Known platform bug (2026-04-26):** populating *both* "Supported by datasets" AND
> "Supported by other publications" has previously caused publishing to fail. To stay on
> the Science Live namespace, populate ONLY the datasets group here and leave
> "Supported by other publications" empty (the methods paper is already cited via the
> step-01 Quote and again in the step-06 CiTO `usesMethodIn`). If you do want both and
> it fails, fall back to Nanodash (URI becomes `https://w3id.org/np/...`).

### Supported by other publications (repeatable group, optional)

```
*(skip — optional; leave empty to avoid the two-group publishing bug. The methods paper
10.1890/07-2153.1 is already anchored via the step-01 Quote and the step-06 CiTO.)*
```

## AIDA pre-write checklist (verification — not a form field)

| Check | Result |
|---|---|
| No numerical values | Pass — no percentages, no Nside, no coefficients. |
| No method names | Pass — "species-distribution models" and "target-group-background sampling-bias correction" are discipline-level concepts, not library/model-class names (no `elapid`, `MaxEnt`, `nside=256`). |
| No cryptic identifiers | Pass — no codebase variable names or slugs. |
| World-talk, not model-talk | Pass — states that the *hotspots agree / do not agree* with the gold standard, not "the model coefficient is…". |
| One empirical finding | Pass — single finding: the corrected hotspots do not agree better (agree worse). The trailing "and in fact agree worse" sharpens the *same* finding (direction of the same comparison), it does not introduce a second, independent finding. |
| Ends with a full stop | Pass. |

> Drafting note: the headline scale (~25 km / Nside 256), the misidentification percentages,
> the basis-of-record strategies, and the per-species MaxEnt implementation are deliberately
> kept OUT of the AIDA. Scale + strategies + implementation live in the Study (step 04);
> the percentages live in the Outcome's Evidence field (step 05). "Equal-area sphere grid"
> is the most abstract phrasing of the substrate that still distinguishes this from a plain
> lat-lon analysis without naming HEALPix.

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 02.

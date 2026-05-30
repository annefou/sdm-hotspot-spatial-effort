# 01 — Quote-with-comment (paper-rooted chain)

**Form heading:** *"Annotate a paper quotation — Annotating a paper quotation with personal interpretation"*
**Template status:** documented in `docs/forrt-form-fields.md` § Quote-with-comment.

## Documented field list (paste-verbatim per pre-flight checklist)

| Field label | Field type | Required |
|---|---|---|
| Cited DOI | text input | yes |
| Quote whole text (less than 500 characters) | radio button (default) | — |
| Quote start/end | radio button (alternative) | — |
| Quoted Text | textarea | yes |
| Comment | textarea | yes |

## Field-by-field draft

### Cited DOI (text input)

Bare DOI, **NOT** `https://doi.org/...` form.

```
10.1890/07-2153.1
```

### Quote mode (radio button)

- [x] **Quote whole text (less than 500 characters)**
- [ ] Quote start/end

### Quoted Text (textarea, required)

Verbatim from `paper/…Phillips…pdf`, p.182 (bottom-right paragraph, "An alternative approach is to manipulate the background data…"). Verified character-for-character against the PDF on 2026-05-30.

```
The approach we propose is to design the selection of background data so they reflect the same sample selection bias as the occurrence data.
```

Character count: 140 / 500.

### Comment (textarea, required)

Subtitle: *"Our interpretation or explanation of why this quotation is relevant."*

```
Phillips' remedy for sample selection bias — background data designed to carry the same spatial bias as the occurrences — is the mechanism this replication tests on a new instrument. Where coverage-based rarefaction (a per-cell completeness correction) failed to restore Iberian-bird GBIF richness hotspots against the EU Article 12 expert-rangemap gold standard, we ask whether a spatially-explicit effort correction in this spirit recovers the true hotspots.
```

Character count: 460 / 500.

## Drafting notes (not form fields)

- **Framing chosen by the user**: framing (b) — *bias-correction mechanism / hotspot-restoration*, the direct analogue of the sibling chain's coverage-rarefaction test. The Quote anchors Phillips' proposed *mechanism* (background sharing the occurrence bias), not his per-species AUC numbers.
- **Replication deviation to record downstream**: Phillips 2009 evaluates against independent presence–absence test sites with per-species AUC/COR; this replication substitutes the EU Article 12 expert rangemaps as the gold standard and a top-5% hotspot-misidentification metric. We test Phillips' *mechanism* on a new instrument, not his number. This deviation must be stated explicitly in the FORRT Replication Study (`04_study.md`) Methodology/Deviations and the Outcome (`05_outcome.md`).
- **CiTO topology (locked in HANDOFF.md)**: apex CiTO `extends` the sibling Outcome (`RAsPjE…`) + `usesMethodIn` → this paper (`10.1890/07-2153.1`).

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 01.

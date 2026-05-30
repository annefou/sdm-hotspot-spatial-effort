# 03 — FORRT Claim

> Pre-flight checklist run against `docs/forrt-form-fields.md` § FORRT Claim on 2026-05-30.
> Claim type chosen per `docs/claim-type-vocabulary.md` (see justification below).

**Form heading:** *"FORRT Claim — Declare an original claim according to FORRT, linking it to an AIDA sentence with a specific FORRT type."*
**Template status:** documented in `docs/forrt-form-fields.md` § FORRT Claim.

## Documented field list (paste-verbatim per pre-flight checklist)

| Field label | Field type | Required |
|---|---|---|
| Short URI suffix as claim ID | text input | yes |
| Label of the claim (to find it later) | text input | yes |
| Search for an AIDA sentence | search/select dropdown | yes |
| Type of FORRT claim | dropdown (7 options) | yes |
| Source URI (optional) | text input | no |

## Field-by-field draft

### Short URI suffix as claim ID (text input, required)

Kebab-case slug, becomes part of the nanopub URI.

```
tgb-correction-does-not-restore-hotspots
```

### Label of the claim (to find it later) (text input, required)

A descriptive title, not a sentence.

```
Target-group-background SDM correction does not restore Iberian-bird biodiversity hotspots
```

### Search for an AIDA sentence (search/select, required)

URI of the AIDA published in step 02. Pull from `nanopubs/PUBLISHED.md`.

> If the AIDA was published via Nanodash (`w3id.org/np/...` namespace), the platform's
> search may not find it — paste the URI manually.

```
<pending step 02 publication>
```

### Type of FORRT claim (dropdown, required)

Pick one.

- [ ] computational performance
- [ ] scalability
- [ ] data quality
- [ ] data governance
- [x] **descriptive pattern**
- [ ] model performance
- [ ] statistical significance

> **Justification.** The claim asserts an observed empirical relationship — corrected hotspots
> do not agree better (agree worse) with the gold standard than uncorrected hotspots — which is
> `descriptive pattern` per `docs/claim-type-vocabulary.md` (the model is the instrument; the
> agreement pattern is the claim). This matches the parent and sibling chains, which also used
> `descriptive pattern`. It is **not** `model performance`: that genre is for a model's accuracy
> on a held-out test set (e.g. the per-species AUC question), which is handled in the companion
> repo `sdm-phillips-reproduction`, NOT here. Here the model is the instrument used to recover an
> underlying truth (true hotspot location), and the claim is about whether that truth is recovered.

### Source URI (optional) (text input, optional)

Full URL form (NOT bare DOI). The methods paper whose correction is under test.

```
https://doi.org/10.1890/07-2153.1
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 03.

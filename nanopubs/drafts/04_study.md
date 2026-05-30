# 04 — FORRT Replication Study

> Pre-flight checklist run against `docs/forrt-form-fields.md` § FORRT Replication Study on
> 2026-05-30. Method verified against `notebooks/03_analysis.py` (read in full, not from memory).
> Scope (what) / method (how) / results separation per `docs/pico-study-outcome-levels.md`:
> NO numerical results in this draft — they live only in the Outcome (step 05).

**Form heading:** *"FORRT Replication Study"*
**Template status:** documented in `docs/forrt-form-fields.md` § FORRT Replication Study.

## Documented field list (paste-verbatim per pre-flight checklist)

| Field label | Field type | Required |
|---|---|---|
| Short URI suffix for study ID | text input | yes |
| Label/name of replication study | text input | yes |
| Study type | dropdown (3 options) | yes |
| Search for a FORRT claim | search/select | yes |
| Describe what part of the claim is reproduced/replicated | textarea | yes |
| Describe how the claim is reproduced/replicated | textarea | yes |
| Describe any deviations from original methodology | textarea | no |
| Search keywords (Wikidata) | multi-select Wikidata search | no |
| Search discipline (Wikidata) | search Wikidata | no |

## Field-by-field draft

### Short URI suffix for study ID (text input, required)

```
tgb-iberian-hotspot-restoration-study
```

### Label/name of replication study (text input, required)

```
Replication: does target-group-background SDM correction restore Iberian-bird hotspots against the EU Article 12 gold standard?
```

### Study type (dropdown, required)

- [ ] Reproduction Study — direct reproduction: same methodology, same tools.
- [x] **Replication Study** — replication with different methodology or conditions.
- [ ] Reproduction/Replication Study — both.

> Different data (Iberian GBIF, not Phillips' NCEAS set), different instrument/metric
> (hotspot misidentification vs an expert-rangemap gold standard, not per-species AUC),
> and a different substrate (HEALPix-NESTED). This is a Replication Study, not a Reproduction.

### Search for a FORRT claim (search/select, required)

URI of the Claim published in step 03. Pull from `nanopubs/PUBLISHED.md`.

```
<pending step 03 publication>
```

### Describe what part of the claim is reproduced/replicated (textarea, required)

The **scope** — which aspect is tested, what's in/out of scope. NO method, NO results.

```
Scope: whether Phillips et al. (2009)'s target-group-background sampling-bias correction can restore the IDENTITY of the top-5% biodiversity hotspots — i.e. recover which grid cells are genuine richness hotspots — when those hotspots are derived from spatially biased occurrence data and benchmarked against an independent expert-rangemap gold standard (the EU Article 12 breeding-bird distributions for Iberia). In scope: both basis-of-record strategies (museum-grade records and all observations), so the test is not contingent on one data-quality regime; a ladder of equal-area grid resolutions, with a single pre-registered headline scale; and a comparison of the corrected hotspots against both an uncorrected occurrence-count baseline and a random-background SDM baseline. Out of scope: Phillips' own claim that target-group background improves per-species predictive discrimination (AUC) — that is the faithfulness question, established separately on Phillips' own data in the companion reproduction sdm-phillips-reproduction, and is NOT disputed here. This study tests only whether the per-species correction propagates up to recovering true hotspot identity.
```

### Describe how the claim is reproduced/replicated (textarea, required)

The **method** in plain prose. Verified against `notebooks/03_analysis.py`. Configuration numbers (Nside ladder, occurrence threshold, headline scale, feature set) are allowed here; result numbers are NOT.

```
We fit a separate presence-background species-distribution model (MaxEnt, via the pure-Python elapid library, CPU) for every breeding-bird species with at least 20 occupied grid cells, using CHELSA v2 bioclimatic variables (standardised) as environmental predictors over an equal-area HEALPix-NESTED grid (geographic, WGS84-aware, via healpix-geo). Each species is fitted twice: once with target-group background — background cells drawn from the pooled all-bird occurrence cells, weighted by per-cell record count, so the background carries the same spatial sampling bias as the occurrences (Phillips' proposed correction) — and once with random (uniform) background as the contrast that fits rather than cancels the bias. MaxEnt features are linear + quadratic + hinge (the simpler linear + quadratic set is run as a sensitivity check). MaxEnt with presence + background is the maximum-entropy estimate of the relative occurrence-rate surface and is equivalent to an inhomogeneous-Poisson-point-process intensity fit (Warton & Shepherd 2010; Renner et al. 2015), so changing the background reference measure is what cancels the shared bias. Per-cell predicted suitabilities are summed across species to give a per-cell predicted-richness surface (one for each background type). For each surface we take the top-5% cells as hotspots and measure misidentification as the symmetric set non-overlap of those hotspots against the EU Article 12 expert-rangemap hotspots (matched to the species intersection of each GBIF strategy). We compare the two SDM surfaces against an uncorrected raw occurrence-count richness baseline; the uncorrected baseline is required to reproduce the sibling study's published misidentification before the corrected numbers are trusted. We report the full resolution ladder (Nside 16 to 512) and adopt Nside 256 (about 25 km) as the pre-registered headline scale. GBIF inputs reuse the sibling download DOIs identically (museum 10.15468/dl.r8pcat; all-observations 10.15468/dl.e9xv7p). The per-cell occurrence-frequency tables, the Article 12 GeoPackage gold standard, and the equal-area-grid substrate are reused from the sibling study.
```

### Describe any deviations from original methodology (textarea, optional)

What's different from Phillips et al. (2009). Verified against the code and the paper summary.

```
1. Different data: Iberian breeding-bird occurrences from GBIF, not Phillips' 226-species, six-region NCEAS benchmark collection (Elith et al. 2006).
2. Different instrument and outcome metric: Phillips evaluates the correction by per-species AUC / point-biserial correlation on independent presence-absence test sites; this study evaluates it by top-5% hotspot misidentification against the EU Article 12 expert rangemaps as the gold standard. We test Phillips' correction mechanism on a new instrument (hotspot identity recovery), not on his original metric.
3. Different substrate: an equal-area HEALPix-NESTED grid (geographic, WGS84-aware), rather than Phillips' region-specific projected raster grids; this is the same substrate as the parent and sibling chains, chosen so results compose across the family.
4. Aggregation step Phillips does not perform: per-species suitabilities are summed to a per-cell predicted-richness surface and then hotspot-ranked. Phillips stops at per-species evaluation; the stacking-to-richness step is added to address the biodiversity-hotspot question.
5. MaxEnt engine: elapid/maxnet (pure-Python), not Phillips' original Maxent software; the companion reproduction sdm-phillips-reproduction shows this engine reproduces the direction and magnitude of his AUC result on his own data, so the engine is not a confound for the hotspot question.
6. Predictors: CHELSA v2 bioclimatic variables only (no land cover or topography), an analogue of Phillips' 11-13 region-specific layers.
```

### Search keywords (Wikidata) (multi-select, optional)

Provide labels (not QIDs) — the Wikidata search resolves labels.

- `species distribution model`
- `sampling bias`
- `biodiversity hotspot`
- `MaxEnt`
- `bird`

### Search discipline (Wikidata) (search, optional)

Provide a label.

- `ecology` (alternatively `macroecology` / `biogeography` if `ecology` is ambiguous in the picker)

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 04.

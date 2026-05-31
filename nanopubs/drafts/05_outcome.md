# 05 — FORRT Replication Outcome

> Phase 3 draft. Iberian numbers verified against `results/headline.json` and
> `results/headline_iberian_lq_sensitivity.json` on 2026-05-30 — not from memory.
> The method-validation (AUC) numbers come from the companion reproduction repo
> [`sdm-phillips-reproduction`](https://github.com/annefou/sdm-phillips-reproduction),
> which carries its own Validated Outcome — this repo cross-cites it, it is not
> re-derived here.

## Single-outcome note

This repo's chain has **one Outcome: Contradicted** for the hotspot-restoration hypothesis. The "is the method faithful?" question is answered in a **separate repo** (`sdm-phillips-reproduction`, a clean Reproduction Study → Validated → CiTO `confirms` Phillips). **Important:** this chain does **NOT** `dispute` Phillips — the companion repo *reproduces* his actual (AUC) claim. The Contradicted verdict is about the *hotspot-restoration extension*, not Phillips' published claim. Per `HANDOFF.md` the step-06 CiTO is `extends` (sibling Outcome) + `usesMethodIn` (Phillips paper), NOT `disputes`.

## Field-by-field draft

### Short URI suffix for outcome ID (text input, required)

```
tgb-does-not-restore-iberian-hotspots
```

### Plain-text label for the outcome (text input, required)

```
Target-group background does not restore GBIF richness hotspots against the EU Article 12 gold standard, despite improving per-species SDM AUC (Iberian birds, HEALPix-NESTED)
```

### Search for a FORRT replication study (search/select, required)

URI of the Replication Study published in step 04. **Pending — publish step 04 first, then paste from `nanopubs/PUBLISHED.md`.**

```
<pending step 04 publication>
```

### Repository URL (text input, required)

> Convention used here: put the **Zenodo concept DOI** (machine-actionable, archival) in this field, and name the GitHub repo in the conclusion/evidence text. The DOI MUST be **this repo's** concept DOI `10.5281/zenodo.20465140` (resolves to "sdm-hotspot-spatial-effort"), NOT the reproduction repo's `10.5281/zenodo.20473156`. The first published Outcome (RAtYdozk…) used the reproduction DOI by mistake — that's what this supersede corrects.

```
https://doi.org/10.5281/zenodo.20465140
```

### Completion date (date picker, required)

```
2026-05-30
```

### Validation status (dropdown, required)

- [ ] Validated
- [ ] PartiallySupported
- [x] **Contradicted**  *(for the hotspot-restoration hypothesis)*

> Note: Contradicted maps by default to `cito:disputes`, but **override to `extends` (sibling Outcome) + `usesMethodIn` (Phillips paper)** per HANDOFF — we do not dispute Phillips' actual (AUC) claim; the companion repo `sdm-phillips-reproduction` reproduces it (Validated). This Contradicted verdict is the *extension's* result.

### Confidence level (dropdown, required)

```
HighConfidence
```

> Justification: the negative result holds across both basis-of-record strategies, is robust to MaxEnt feature set (linear+quadratic AND linear+quadratic+hinge), and both uncorrected baselines reproduce the sibling chain exactly. The method itself is independently validated against Phillips' own data in the companion reproduction (`sdm-phillips-reproduction`). Strong evidence against the hotspot-restoration hypothesis.

### Describe the overall conclusion about the original claim (textarea, required)

```
Phillips et al. 2009's target-group-background correction does what the paper claims — on Phillips' own NCEAS data the same elapid MaxEnt implementation reproduces the per-species AUC gain (companion repo sdm-phillips-reproduction: mean 0.7163 random to 0.7468 target-group, +0.0305, versus Phillips' +0.0293) — yet that per-species improvement does not translate into recovering biodiversity-hotspot identity. On Iberian birds over an equal-area HEALPix-NESTED grid (Nside 256, about 25 km), top-5% richness hotspots from target-group-background SDMs disagree with the EU Article 12 expert-rangemap gold standard at 97.24% (museum strategy) and 100.0% (all-observations) symmetric set non-overlap — worse than uncorrected raw GBIF richness (93.71% and 86.59%) and nowhere near the Hurlbert & Jetz reference range of 47.8 to 68.6%. Standardising for where people looked, in the spirit Phillips proposes, does not remove the spatial sampling-location bias that determines which cells rank as hotspots. This extends, and is consistent with, the sibling chain's finding that coverage-based rarefaction also failed: effort bias in hotspot identity is a sampling-location problem that post-hoc per-species modelling cannot fix, even when that modelling demonstrably sharpens per-species discrimination.
```

### Describe the evidence that supports your conclusion (textarea, required)

```
Method validation (companion repo sdm-phillips-reproduction, cross-cited): on Phillips' own data (Elith et al. 2006 NCEAS benchmark, 225 species, 6 regions) the same per-species elapid MaxEnt with target-group background reproduces Phillips Table 2 — mean AUC 0.7163 (random) to 0.7468 (target-group), +0.0305 (paired Wilcoxon p = 1.6e-06), versus Phillips' +0.0293; largest gain in the most-biased region (CAN +0.1317 vs Phillips approx +0.14). This establishes the implementation is faithful, so the hotspot result below is not a modelling artifact.

This study (Iberian hotspots vs EU Article 12, top-5% symmetric set non-overlap at HEALPix-NESTED Nside 256):
- museum strategy: raw GBIF richness 93.71%; target-group SDM 97.24% (worse by 3.53 percentage points); random-background SDM 93.71%.
- all-observations strategy: raw 86.59%; target-group SDM 100.0% (worse by 13.41 percentage points); random-background SDM 94.32%.
- Baseline validation: uncorrected raw-vs-EOO-hull misidentification reproduces the sibling chain exactly (museum 89.94% vs published 89.9%; all-observations 97.8% vs 97.8%).
- Robustness: the conclusion is unchanged under the simpler linear+quadratic feature set (museum target-group 96.67%, all-observations 100.0%; see results/headline_iberian_lq_sensitivity.json).
- No SDM surface reaches the Hurlbert & Jetz reference range (47.8 to 68.6%) at the headline scale.
Source: results/headline.json, notebooks/03_analysis.py; method validation in sdm-phillips-reproduction.
```

### Describe what limits the conclusions of the study (textarea, optional)

```
1. Per-species MaxEnt was fitted only for species with at least 20 occurrence cells; sparser species are excluded, which thins the predicted-richness surface — the same effort-poor-cell censoring that constrained the sibling's coverage-rarefaction study. The exclusion is itself part of why post-hoc correction struggles.
2. Predicted richness is the sum of per-species continuous suitabilities; an alternative (thresholding suitability to presence before summing) was not explored and could shift the hotspot ranking.
3. The MaxEnt engine is elapid/maxnet, not Phillips' original Maxent; the companion reproduction reproduces the direction and magnitude of his AUC result but exact decimals differ by implementation.
4. Environmental predictors are CHELSA bioclimatic variables only (no land cover or topography); a richer covariate set might change absolute SDM performance, though the comparison to raw richness and to random background is internally consistent.
5. The Article 12 comparison is restricted to the species intersection between each GBIF strategy and the Article 12 Iberian breeding set.
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 05.

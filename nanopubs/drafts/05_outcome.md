# 05 — FORRT Replication Outcome

> Phase 3 draft. Numbers verified against `results/headline.json`,
> `results/repro_headline.json`, and `results/headline_iberian_lq_sensitivity.json`
> on 2026-05-30 — not quoted from memory.

## ⚠️ Dual-outcome note (resolve in Phase 5 chain design)

This study has **two arms with opposite verdicts**, so it likely needs **two Outcome nanopubs**:

- **Arm A — Reproduction (Phillips' own data, AUC):** *Validated*. We reproduced Phillips' published result. CiTO toward the paper → `confirms` / `usesMethodIn`.
- **Arm B — Replication/extension (Iberian hotspots):** *Contradicted* (for the hotspot-restoration hypothesis). This is the arm that **`extends` the sibling chain**.

The draft below fills the form for the **primary Outcome of this chain = Arm B** (the one that extends the sibling), and folds Arm A in as supporting evidence. **Important:** the chain does **NOT** `dispute` Phillips — we *reproduced* his actual (AUC) claim. The Contradicted verdict is about the *hotspot-restoration extension*, not Phillips' published claim. Per `HANDOFF.md` the step-06 CiTO is `extends` (sibling Outcome) + `usesMethodIn` (Phillips paper), NOT `disputes`. See `docs/chain-decision-tree.md` for whether to publish Arm A as a second Outcome + a `confirms` CiTO to the paper.

## Field-by-field draft (Arm B — primary)

### Short URI suffix for outcome ID (text input, required)

```
tgb-does-not-restore-iberian-hotspots
```

### Plain-text label for the outcome (text input, required)

```
Target-group background does not restore GBIF richness hotspots against the EU Article 12 gold standard, despite reproducing Phillips' per-species AUC gain (Iberian birds, HEALPix-NESTED)
```

### Search for a FORRT replication study (search/select, required)

URI of the Replication Study published in step 04. **Pending — publish step 04 first, then paste from `nanopubs/PUBLISHED.md`.**

```
<pending step 04 publication>
```

### Repository URL (text input, required)

```
https://github.com/annefou/sdm-hotspot-spatial-effort
```

### Completion date (date picker, required)

```
2026-05-30
```

### Validation status (dropdown, required)

- [ ] Validated
- [ ] PartiallySupported
- [x] **Contradicted**  *(for the hotspot-restoration hypothesis — Arm B)*

> Note: this maps by default to `cito:disputes`, but **override to `extends` + `usesMethodIn`** per HANDOFF — we do not dispute Phillips' actual (AUC) claim; we reproduced it (Arm A, Validated). The Contradicted verdict is the *extension's* result.

### Confidence level (dropdown, required)

```
HighConfidence
```

> Justification: the negative result holds across both basis-of-record strategies, is robust to MaxEnt feature set (linear+quadratic AND linear+quadratic+hinge), both uncorrected baselines reproduce the sibling chain exactly, and the method itself is validated against Phillips' own data (Arm A). Strong evidence against the hotspot-restoration hypothesis.

### Describe the overall conclusion about the original claim (textarea, required)

```
Phillips et al. 2009's target-group-background correction does what the paper claims — on Phillips' own NCEAS data our elapid MaxEnt reproduces the per-species AUC gain (mean 0.7163 random to 0.7468 target-group, +0.0305, versus Phillips' +0.0293) — yet that per-species improvement does not translate into recovering biodiversity-hotspot identity. On Iberian birds over an equal-area HEALPix-NESTED grid (Nside 256, about 25 km), top-5% richness hotspots from target-group-background SDMs disagree with the EU Article 12 expert-rangemap gold standard at 97.24% (museum strategy) and 100.0% (all-observations) symmetric set non-overlap — worse than uncorrected raw GBIF richness (93.71% and 86.59%) and nowhere near the Hurlbert & Jetz reference range of 47.8 to 68.6%. Standardising for where people looked, in the spirit Phillips proposes, does not remove the spatial sampling-location bias that determines which cells rank as hotspots. This extends, and is consistent with, the sibling chain's finding that coverage-based rarefaction also failed: effort bias in hotspot identity is a sampling-location problem that post-hoc per-species modelling cannot fix, even when that modelling demonstrably sharpens per-species discrimination.
```

### Describe the evidence that supports your conclusion (textarea, required)

```
Arm A (Reproduction, Phillips' data via the disdat/Elith et al. 2006 dataset; per-species elapid MaxEnt, linear+quadratic+hinge, 225 species, 6 regions): mean AUC on independent presence-absence sites = 0.7163 (random background) vs 0.7468 (target-group background), improvement +0.0305 (paired Wilcoxon p = 1.6e-06), matching Phillips Table 2 (0.7276 -> 0.7569, +0.0293). The most biased region (CAN/Ontario) shows the largest gain (+0.1317; Phillips approx +0.14); the low-bias region (SA) shows none (-0.015) — the bias-gradient pattern of Phillips Table 4 also reproduces. This confirms the target-group-background implementation is faithful.

Arm B (Iberian hotspots vs EU Article 12, top-5% symmetric set non-overlap at HEALPix-NESTED Nside 256):
- museum strategy: raw GBIF richness 93.71%; target-group SDM 97.24% (worse by 3.53 percentage points); random-background SDM 93.71%.
- all-observations strategy: raw 86.59%; target-group SDM 100.0% (worse by 13.41 percentage points); random-background SDM 94.32%.
- Baseline validation: uncorrected raw-vs-EOO-hull misidentification reproduces the sibling chain exactly (museum 89.94% vs published 89.9%; all-observations 97.8% vs 97.8%).
- Robustness: the conclusion is unchanged under the simpler linear+quadratic feature set (museum target-group 96.67%, all-observations 100.0%; see results/headline_iberian_lq_sensitivity.json).
- No SDM surface reaches the Hurlbert & Jetz reference range (47.8 to 68.6%) at the headline scale.
Source: results/headline.json, results/repro_headline.json, notebooks/03_analysis.py and 06_repro_analysis.py.
```

### Describe what limits the conclusions of the study (textarea, optional)

```
1. Per-species MaxEnt was fitted only for species with at least 20 occurrence cells; sparser species are excluded, which thins the predicted-richness surface — the same effort-poor-cell censoring that constrained the sibling's coverage-rarefaction study. The exclusion is itself part of why post-hoc correction struggles.
2. Predicted richness is the sum of per-species continuous suitabilities; an alternative (thresholding suitability to presence before summing) was not explored and could shift the hotspot ranking.
3. The MaxEnt engine is elapid/maxnet, not Phillips' original Maxent; Arm A reproduces the direction and magnitude of his AUC result but exact decimals differ by implementation.
4. Environmental predictors are CHELSA bioclimatic variables only (no land cover or topography); a richer covariate set might change absolute SDM performance, though the comparison to raw richness and to random background is internally consistent.
5. The Article 12 comparison is restricted to the species intersection between each GBIF strategy and the Article 12 Iberian breeding set.
```

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 05. If Arm A is published as a second Outcome, record both.

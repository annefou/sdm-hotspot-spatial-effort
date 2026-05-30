# Paper summary

> This is a working scratchpad for the paper-analysis phase. The output of this file feeds the Quote / AIDA / Claim drafts. It is not itself a nanopub.

**Reference paper:** Sample selection bias and presence-only distribution models: implications for background and pseudo-absence data

**DOI:** 10.1890/07-2153.1

**Authors:** Steven J. Phillips, Miroslav Dudík, Jane Elith, Catherine H. Graham, Anthony Lehmann, John Leathwick, Simon Ferrier

**Year:** 2009 — *Ecological Applications* 19(1):181–197

## Headline claim

> **STATUS: RESOLVED (2026-05-30).** The user chose **C4** (framing **b** — bias-correction mechanism / hotspot-restoration), the direct analogue of the sibling chain's coverage-rarefaction test. The chain roots on Phillips' proposed *mechanism* (background designed to share the occurrence bias), not his per-species AUC numbers. The verbatim C4 sentence — verified character-for-character against PDF p.182 — is now in `nanopubs/drafts/01_quote.md`. Candidate list retained below for the record.
>
> **Chosen headline claim (C4, p.182):** "The approach we propose is to design the selection of background data so they reflect the same sample selection bias as the occurrence data."

### Candidate headline sentences (verbatim, verified against PDF)

**Framing (a) — AUC / predictive-performance improvement:**

- **C1 (Abstract, p.181):** "We find that target-group background improves average performance for all the modeling methods we consider, with the choice of background data having as large an effect on predictive performance as the choice of modeling method."
- **C2 (Abstract, p.181):** "The performance improvement due to target-group background is greatest when there is strong bias in the target-group presence records."
- **C3 (Conclusions, p.196):** "We conclude that the choice of background data is as important as the choice of modeling method when modeling species distributions using presence-only data."

**Framing (b) — bias-correction mechanism (target-group background shares the bias of occurrence data):**

- **C4 (Introduction, p.182):** "The approach we propose is to design the selection of background data so they reflect the same sample selection bias as the occurrence data."

> Recommendation to the user: C1 or C3 anchor the AUC-improvement replication (closest to Phillips' literal headline). C4 anchors the bias-correction / hotspot-restoration adaptation (closest parallel to the sibling's coverage-rarefaction test, since it states the *mechanism* the replication would repurpose for hotspot recovery). C2 is the strongest empirical conditional ("greatest when there is strong bias") and is attractive if the replication wants to test the *gradient* of improvement vs effort bias on the Iberian data.

## Methodology summary

- **Data sources:** Occurrence + independent presence–absence evaluation data for **226 species** from **six regions** (Australian Wet Tropics, Ontario Canada, NE New South Wales, New Zealand, South America, Switzerland), reused from the Elith et al. (2006) NCEAS comparison. Training presence counts per species range 2–5822 (median 57); independent evaluation sites per species 102–19120. There are 11–13 environmental predictor layers per region; grid cells ~100 m (AWT, NSW, NZ, SWI) or 1 km (CAN, SA). Regions exhibit varying sample selection bias, with Ontario showing the strongest.
- **Statistical / ML models:** Four background-using presence-only methods compared — **boosted regression trees (BRT)**, **Maxent** (maximum entropy density estimation), **MARS** (multivariate adaptive regression splines), and **GAM** (generalized additive models). BIOCLIM (no background) included for context. Each method fitted with two background treatments: **random background** (10000 sites drawn uniformly per region, as in Elith et al. 2006) vs **target-group background** (the pooled presence localities of *all* species in the same target group — e.g. all birds, all plants — used as background, so the background carries the same spatial sampling bias as the occurrences).
- **Sample sizes:** 226 species × 4 methods × 2 background treatments; per-species effects pooled by ANOVA and paired Wilcoxon signed-rank tests across species. 9 target groups (Table 1): AWT-bird (20 spp), AWT-plant (20), CAN (20), NSW-bird (10), NSW-mammal (7), NSW-plant (29), NSW-reptile (8), NZ (52), SA (30), SWI (30).
- **Evaluation metrics:** AUC (area under ROC curve) and COR (point-biserial correlation between prediction and 0/1 test data), both computed on the **independent presence–absence test sites** (largely unaffected by training sample selection bias). Improvement = (target-group AUC) − (random AUC), per species.
- **Headline numerical results (Table 2, averaged over all 226 species):**
  | Model | Random AUC | Target-group AUC | Random COR | Target-group COR |
  |---|---|---|---|---|
  | BRT  | 0.7275 | **0.7544** | 0.2130 | 0.2435 |
  | Maxent | 0.7276 | **0.7569** | 0.2100 | 0.2446 |
  | MARS | 0.6964 | **0.7260** | 0.1787 | 0.2145 |
  | GAM  | 0.6993 | **0.7368** | 0.1765 | 0.2196 |
  Improvement is highly significant for every method (P < 0.001, two-tailed Wilcoxon signed-rank, paired by species). ANOVA (Table 3): the **background-type effect is larger than the modeling-method effect**; species is the strongest factor; all three factors significant at P < 1e-14.
- **Conditional / gradient result:** Improvement scales with training-data bias — strong monotone Spearman dependence of AUC improvement on both training-bias and test-bias estimates (Table 4, ρ = 0.75–0.95, all significant). Largest gains for the most biased target groups (CAN ≈ +0.14 AUC; NSW-mammal, NSW-bird, NSW-reptile next). Worked single-species example: Golden-crowned Kinglet (Ontario, generalist), Maxent AUC 0.3379 → 0.8412, BRT 0.2920 → 0.8648 with target-group background.
- **Caveats from the authors:** target-group background can degrade predictions into *unsampled* environmental space (treat extrapolation with caution); the synthetic-species demonstration (Fig. 1–2) shows presence-only models collapse under bias (correlation with truth drops from ~0.88 to ~0.35 as bias factor b → 100) while presence–absence models stay robust (~0.75–0.88).

## Replication design choice

Which of the three FORRT Study Types fits this replication?

- [ ] **Reproduction Study** — direct reproduction: same methodology, same tools.
- [ ] **Replication Study** — replication with different methodology or conditions.
- [x] **Reproduction/Replication Study** — both (decided 2026-05-30; see the two-arm design below).

**Justification (LOCKED in HANDOFF.md, confirmed by this analysis):** This is a **Replication Study**. The replication uses *different data* (Iberian breeding birds from GBIF, not Phillips' 226-species 6-region NCEAS collection), a *different substrate* (HEALPix-NESTED equal-area cells, Nside 256 ≈ 25 km), and — under framing (b) — a *different outcome metric* (top-5% richness-hotspot misidentification vs the EU Article 12 expert-rangemap gold standard, rather than per-species AUC on presence–absence test sites). It tests whether Phillips' recommended target-group-background correction recovers the effort-distorted hotspots that the sibling coverage-rarefaction study (Contradicted) could not. The CiTO is `extends` the sibling Outcome + `usesMethodIn` → this methods paper (NOT `disputes`), regardless of the replication's own result. Note: under framing (a) the replication would stay closer to Phillips' own AUC metric (per-species AUC improvement on Iberian birds vs random background), which is a more literal reproduction of his headline but still on different data/region.

## Phase 2 design lock — PRE-REGISTERED 2026-05-30

These choices are fixed *before* any analysis is run (HANDOFF.md: "pre-register before running"). Do not let a positive result emerge from post-hoc tuning.

- **Correction under test:** Phillips 2009 target-group background, implemented as **per-species MaxEnt** (presence-background) via **`elapid`** (pure-Python, CPU). Narrate the MaxEnt ≈ inhomogeneous-Poisson-point-process equivalence (Warton & Shepherd 2010).
- **Effort layer / target-group background:** the pooled all-bird occurrences (the `allbor` GBIF download) used as background, so background carries the same spatial sampling bias as occurrences. Per-cell target-group intensity = total all-bird record count per HEALPix cell (summed over species from the reused per-cell frequency tables).
- **Environmental predictors:** CHELSA v2 bioclimatic variables (~1 km), regridded to the HEALPix grid (analogue of Phillips' 11–13 layers). NEW download step (siblings have no predictors).
- **Modelling unit:** per-species MaxEnt for species with **≥ 20 occurrences**; predict per-cell suitability → **sum across species to per-cell predicted richness** → top-5% hotspot. Species with < 20 occurrences are excluded; record the censoring as a limitation (mirrors the sibling).
- **Baselines compared (all vs the same gold standard):** (1) uncorrected raw GBIF richness, (2) the sibling's coverage-rarefied richness, (3) this study's target-group-background SDM richness.
- **Gold standard:** EU Article 12 expert rangemaps (reuse the sibling's GeoPackage). **Metric:** top-5% hotspot symmetric set non-overlap (misidentification %). **Headline scale:** HEALPix-NESTED Nside 256 (~25 km); report the full ladder 16–512.
- **Strategies:** `museum` and `allbor`, same split as the siblings.
- **GBIF inputs:** reuse the sibling DOIs identically — `10.15468/dl.r8pcat` (museum), `10.15468/dl.e9xv7p` (allbor). No new mint.
- **Outcome verdict is open:** if target-group background restores agreement → Validated/PartiallySupported; if it fails too → Contradicted (for the correction hypothesis). CiTO `extends` the sibling Outcome + `usesMethodIn` → this paper regardless (HANDOFF). Stay honest (DOMAIN § honest negative results).

## Two-arm design — Reproduction + Replication (decided 2026-05-30)

The study has two arms, yielding two Outcomes:

**Arm A — Reproduction (same data, same method).** Reproduce Phillips' headline AUC result on his own data (the Elith et al. 2006 NCEAS dataset, packaged as the `disdat` R package; read in Python via `pyreadr` from the rspatial/disdat `.rds` files — no R dependency). Fit per-species MaxEnt via `elapid` with random background vs target-group background; evaluate AUC on the independent presence–absence sites. Validation target = Phillips Table 2 Maxent row: mean AUC **0.7276 (random) → 0.7569 (target-group)** over 226 species, with target-group > random. Maxent is the required method (it is our Iberian-arm engine); BRT is an optional secondary check. This arm proves the implementation is faithful to the paper.

**Arm B — Replication/extension (Iberian hotspots).** The existing 4-notebook pipeline: per-species MaxEnt with target-group vs random background on Iberian GBIF birds, summed to per-cell predicted richness, top-5% hotspot misidentification vs the EU Article 12 gold standard. Headline (full both-strategy run, Nside 256, vs Article 12): target-group SDM does NOT restore agreement — museum 96.67% (raw 93.71%), allbor 100.0% (raw 86.59%); worse than raw in both, robust to hinge features (museum hinge: target-group 97.24% vs raw 93.71%). Direction = Contradicted for the hotspot-restoration hypothesis.

**Why both:** Arm A decouples "is our method faithful?" from Arm B's "does the correction restore hotspots?". If Arm A reproduces Phillips' AUC gains AND Arm B still fails on hotspots, the negative hotspot result is attributable to the *hotspot question*, not a broken implementation. CiTO can then `confirms` Phillips (Arm A reproduced his result) while `extends` the sibling on the hotspot question (Arm B).

## Notes for downstream drafts

- **"Target-group background" precise definition (for AIDA / Claim / Study Methodology):** background/pseudo-absence points drawn from the pooled presence localities of *all species in the same broadly-defined biological target group* (e.g. all birds, all plants) collected by similar methods/equipment, so the background inherits the *same spatial sample selection bias* as the occurrence records. A presence-only model then contrasts a species' occurrences against this biased background, cancelling the shared bias rather than fitting it. Contrast with **random background** = uniform draw over the region (the standard, which fits the bias).
- The paper's evaluation uses **independent presence–absence test data** — the replication's framing (b) substitutes the EU Article 12 expert rangemaps as the gold standard, which is an analogous "unbiased reference" but a different instrument; flag this as a deviation in the Study/Outcome.
- Two AIDA-worthy atomic findings to keep separate: (1) target-group background improves average predictive performance for all four methods; (2) the magnitude of improvement increases with the amount of sampling bias in the training data. Do not conjoin with "and" in a single AIDA.
- "Percentage points" must be spelled out in nanopub prose (DOMAIN style). AUC deltas here are small absolute numbers (~0.03 average, up to ~0.14) — report AUC as decimals, not percentage points.

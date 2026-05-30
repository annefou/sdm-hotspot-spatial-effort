# ---
# jupyter:
#   jupytext:
#     formats: py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # 03 — Analysis: target-group-background SDMs vs effort-distorted hotspots
#
# **The new science of this replication.** The parent chain
# (`sdm-scale-replication`) showed raw GBIF richness hotspots are dominated by
# observer effort; the sibling chain (`sdm-hotspot-effort-correction`) showed a
# *per-cell completeness* correction (coverage-based rarefaction) cannot fix it
# because the bias is a *spatial sampling-location* effect. Phillips et al.
# (2009, `10.1890/07-2153.1`) propose a correction aimed at exactly that:
# **target-group background** — draw the model's background/pseudo-absence data
# with the *same spatial sampling bias* as the occurrences, so a presence-only
# model contrasts a species against the bias rather than fitting it.
#
# We implement it as **per-species MaxEnt** (`elapid`, pure-Python, CPU). MaxEnt
# with presence + background data is the maximum-entropy estimate of the
# species' relative occurrence-rate surface, and is equivalent to fitting an
# **inhomogeneous Poisson point process** intensity (Warton & Shepherd 2010;
# Renner et al. 2015): the log-intensity is linear in the environmental
# covariates, and the background sample approximates the integral of the
# intensity over the study region. Changing the background distribution from
# *uniform* to *target-group* changes the reference measure of that point
# process so that the shared sampling bias cancels.
#
# Pipeline per (strategy, nside):
#
# 1. Fit MaxEnt for every species with **>= 20 atlas occurrence cells**, on the
#    CHELSA bioclim covariates, twice:
#    - **target-group background** — background cells drawn from the pooled
#      all-bird occurrence cells, weighted by per-cell record count (carries the
#      occurrence sampling bias).
#    - **random background** — background cells drawn uniformly over Iberian
#      cells (Phillips' contrast; fits the bias).
# 2. Predict per-cell cloglog suitability for both; **sum across species** ->
#    per-cell predicted richness (two surfaces).
# 3. Compute top-5 % hotspot **misidentification** (symmetric set non-overlap)
#    of each surface vs the EU Article 12 gold standard (and vs the EOO-hull
#    rangemap, secondary), alongside the **uncorrected raw richness** baseline.
#
# Species with < 20 occurrence cells are excluded; the censoring is counted and
# recorded (mirrors the sibling's effort-poor-cell censoring limitation).
#
# **Validation before trusting the corrected numbers:** the uncorrected raw
# richness misidentification must reproduce the sibling baseline (museum
# ~89.9 %, allbor ~97.8–98.2 % at Nside 256 vs Article 12). The headline JSON
# flags whether it does.
#
# **Smoke-test knobs (env vars):** `SDM_NSIDES` (comma-sep subset of the
# ladder), `SDM_MAX_SPECIES` (cap species per strategy×nside), `SDM_STRATEGIES`.
# Unset => full production run over both strategies and the whole ladder.

# %%
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from elapid import MaxentModel

# %% [markdown]
# ## Constants and paths

# %%
ALL_STRATEGIES = ["museum", "allbor"]
ALL_NSIDES = [16, 32, 64, 128, 256, 512]
HOTSPOT_FRACTION = 0.05
HEADLINE_NSIDE = 256
MIN_SPECIES_OCC = 20          # Phillips/replication threshold: >= 20 occ cells.
N_BACKGROUND = 5_000          # background sample size per species fit.
RANDOM_STATE = 20260530

# MaxEnt feature set: linear + quadratic keeps per-species fits fast over the
# hundreds-of-species production job while remaining a faithful presence-
# background MaxEnt. (hinge features are available but ~10x slower at scale.)
MAXENT_FEATURES = os.environ.get("SDM_FEATURES", "linear,quadratic").split(",")

# Sibling uncorrected baselines (Nside 256, vs Article 12) — validation target.
SIBLING_BASELINE = {"museum": 89.9, "allbor": 97.8}
HJ_RANGE = (47.8, 68.6)       # Hurlbert & Jetz 2007 reference band (0.25 deg).

# Smoke-test overrides.
STRATEGIES = os.environ.get("SDM_STRATEGIES", ",".join(ALL_STRATEGIES)).split(",")
NSIDES = [int(n) for n in os.environ.get(
    "SDM_NSIDES", ",".join(str(n) for n in ALL_NSIDES)).split(",")]
MAX_SPECIES = int(os.environ.get("SDM_MAX_SPECIES", "0")) or None
DEPTHS = {n: int(np.log2(n)) for n in NSIDES}

ROOT = Path("..").resolve()
DATA = ROOT / "data"
CLEAN_DIR = DATA / "clean"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ART12_GPKG = (DATA / "external" / "art12"
              / "ART12_3035_distribution_data_without_sensitive.gpkg")
ART12_LAYER = "EU_ART12_birds_distribution_2013_2018_without_sensitive_species"
IBERIA_COUNTRIES = {"ES", "PT", "GIB"}
ELLIPSOID = "WGS84"

STRATEGY_RICHNESS_NC = {s: CLEAN_DIR / f"richness_{s}.nc" for s in ALL_STRATEGIES}
STRATEGY_FREQ_PARQUET = {s: CLEAN_DIR / f"atlas_freq_{s}.parquet" for s in ALL_STRATEGIES}
STRATEGY_SPIDX_PARQUET = {s: CLEAN_DIR / f"species_index_{s}.parquet" for s in ALL_STRATEGIES}
PREDICTORS_NC = CLEAN_DIR / "predictors_cells.nc"

OUT_PARQUET = RESULTS_DIR / "sdm_misidentification.parquet"
OUT_HEADLINE = RESULTS_DIR / "headline.json"

print(f"STRATEGIES     = {STRATEGIES}")
print(f"NSIDES         = {NSIDES}")
print(f"MAX_SPECIES    = {MAX_SPECIES}")
print(f"MAXENT_FEATURES= {MAXENT_FEATURES}")
print(f"Article 12 GPKG= {ART12_GPKG} (exists={ART12_GPKG.exists()})")


# %% [markdown]
# ## Hotspot overlap helpers (reused from parent chain)

# %%
def top_k_set(richness: np.ndarray, fraction: float = HOTSPOT_FRACTION) -> set[int]:
    """Positions of the top-`fraction` cells by richness (NaN-safe)."""
    valid = np.where(np.isfinite(richness))[0]
    if len(valid) == 0:
        return set()
    vals = richness[valid]
    top_k = max(1, int(np.ceil(fraction * len(valid))))
    sel = valid[np.argpartition(vals, -top_k)[-top_k:]]
    return set(int(i) for i in sel)


def misidentified_pct(surface: np.ndarray, reference: np.ndarray) -> float:
    """Symmetric set non-overlap (%) of top-5 % `surface` vs `reference` hotspots."""
    a, b = top_k_set(surface), top_k_set(reference)
    union, inter = a | b, a & b
    if not union:
        return float("nan")
    return (len(union) - len(inter)) / len(union) * 100.0


# %% [markdown]
# ## Predictor matrix per Nside (standardised covariates)

# %%
def load_predictors(nside: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Return (cells, standardised covariate matrix X, var names) for one Nside."""
    with xr.open_dataset(PREDICTORS_NC, group=f"nside_{nside}") as ds:
        cells = ds["cell"].values.astype(np.int64)
        bio_vars = [v for v in ds.data_vars]
        X = np.column_stack([np.asarray(ds[v].values, dtype=float) for v in bio_vars])
    # Mean-impute NaNs, then z-score (MaxEnt clamps; scaling stabilises the fit).
    col_mean = np.nanmean(X, axis=0)
    inds = np.where(np.isnan(X))
    X[inds] = np.take(col_mean, inds[1])
    mu, sigma = X.mean(axis=0), X.std(axis=0)
    sigma[sigma == 0] = 1.0
    return cells, (X - mu) / sigma, bio_vars


# %% [markdown]
# ## Per-species presence sets + target-group / random background

# %%
def species_presence_cells(freq: pd.DataFrame, nside: int) -> dict[int, np.ndarray]:
    """{species_id -> array of presence cell ids} (>=1 record) for one Nside."""
    sub = freq[freq["nside"] == nside]
    return {int(sid): grp["cell"].to_numpy(dtype=np.int64)
            for sid, grp in sub.groupby("species_id", sort=False)}


def target_group_intensity(freq: pd.DataFrame, nside: int,
                           cells: np.ndarray) -> np.ndarray:
    """Per-cell total all-species record count aligned to `cells` (TGB weight)."""
    sub = freq[freq["nside"] == nside]
    tot = sub.groupby("cell")["count"].sum()
    return tot.reindex(cells, fill_value=0).to_numpy(dtype=float)


def draw_background(cells: np.ndarray, weights: np.ndarray | None,
                    n: int, rng: np.random.Generator) -> np.ndarray:
    """Indices (into `cells`) of a background sample.

    weights=None -> uniform (random background); else weighted by `weights`
    (target-group background — carries the occurrence sampling bias)."""
    n = min(n, len(cells))
    if weights is None:
        return rng.choice(len(cells), size=n, replace=False)
    p = weights.copy()
    if p.sum() <= 0:
        return rng.choice(len(cells), size=n, replace=False)
    p = p / p.sum()
    replace = (p > 0).sum() < n
    return rng.choice(len(cells), size=n, replace=replace, p=p)


# %% [markdown]
# ## Per-species MaxEnt fit + predicted-richness stack
#
# For each eligible species: presence rows (cells with >=1 record) + a
# background sample (target-group-weighted OR uniform), fit MaxEnt on the
# standardised covariates, predict cloglog suitability for *every* cell, and
# accumulate into the per-cell richness sum.

# %%
def stack_predicted_richness(presence: dict[int, np.ndarray], cells: np.ndarray,
                             X: np.ndarray, tgb_weights: np.ndarray,
                             background: str, rng: np.random.Generator,
                             max_species: int | None) -> tuple[np.ndarray, int, int]:
    """Sum per-species MaxEnt suitability -> per-cell predicted richness.

    Returns (richness_surface, n_species_fitted, n_species_censored)."""
    cell_pos = {int(c): i for i, c in enumerate(cells)}
    richness = np.zeros(len(cells), dtype=float)
    eligible = [(sid, occ) for sid, occ in presence.items()
                if len(np.unique(occ)) >= MIN_SPECIES_OCC]
    censored = len(presence) - len(eligible)
    eligible.sort(key=lambda t: -len(t[1]))  # deterministic order
    if max_species:
        eligible = eligible[:max_species]
    weights = tgb_weights if background == "target_group" else None
    fitted = 0
    for sid, occ in eligible:
        pres_idx = np.array([cell_pos[int(c)] for c in np.unique(occ)
                             if int(c) in cell_pos], dtype=int)
        if len(pres_idx) < MIN_SPECIES_OCC:
            continue
        bg_idx = draw_background(cells, weights, N_BACKGROUND, rng)
        x = np.vstack([X[pres_idx], X[bg_idx]])
        y = np.concatenate([np.ones(len(pres_idx)), np.zeros(len(bg_idx))])
        model = MaxentModel(feature_types=MAXENT_FEATURES, use_sklearn=True,
                            random_state=RANDOM_STATE, n_cpus=1)
        try:
            model.fit(x, y)
            suit = np.asarray(model.predict(X), dtype=float).ravel()
        except Exception as e:  # noqa: BLE001 — a single failed fit must not kill the run
            print(f"      species_id={sid} fit failed ({e}); skipped")
            continue
        suit = np.nan_to_num(suit, nan=0.0)
        richness += suit
        fitted += 1
    return richness, fitted, censored


# %% [markdown]
# ## Article 12 expert-rangemap per-cell richness (gold standard)
#
# Reused from the sibling: match atlas species to Article 12 species, bin the
# polygon representative points onto the NESTED ladder, count matched species
# per cell. Skipped (NaN) only if the GPKG is absent.

# %%
def load_art12_richness() -> dict[tuple[str, int], np.ndarray] | None:
    """{(strategy, nside) -> per-cell Art-12 matched-subset richness} or None."""
    if not ART12_GPKG.exists():
        print("Article 12 GPKG absent — vs-Art-12 comparison skipped (NaN).")
        return None
    import pyogrio
    from healpix_geo import nested as hp_nested

    where = f"country IN ({','.join(repr(c) for c in IBERIA_COUNTRIES)})"
    art12 = pyogrio.read_dataframe(ART12_GPKG, layer=ART12_LAYER, where=where)
    art12 = art12.to_crs("EPSG:4326")
    rep = art12.geometry.representative_point()
    art12 = art12.assign(lon=rep.x, lat=rep.y)
    art12_species = set(art12["speciesnameEU"].dropna().unique().tolist())
    print(f"Article 12: {len(art12):,} Iberian cells, {len(art12_species)} species.")

    result: dict[tuple[str, int], np.ndarray] = {}
    for s in STRATEGIES:
        spidx = pd.read_parquet(STRATEGY_SPIDX_PARQUET[s])
        matched = set(spidx["species"].tolist()) & art12_species
        sub = art12[art12["speciesnameEU"].isin(matched)]
        lons = sub["lon"].to_numpy(float)
        lats = sub["lat"].to_numpy(float)
        sp = sub["speciesnameEU"].to_numpy()
        sp_id = {name: i for i, name in enumerate(sorted(matched))}
        sid = np.fromiter((sp_id[x] for x in sp), dtype=np.int64, count=len(sp))
        for nside in NSIDES:
            with xr.open_dataset(STRATEGY_RICHNESS_NC[s], group=f"nside_{nside}") as ds:
                cells = ds["cell"].values.astype(np.int64)
            hp_cells = hp_nested.lonlat_to_healpix(
                lons, lats, DEPTHS[nside], ELLIPSOID).astype(np.int64)
            keep = np.isin(hp_cells, cells)
            rich = pd.Series(0, index=cells, dtype=np.int64)
            if keep.any():
                pairs = np.unique(np.column_stack([hp_cells[keep], sid[keep]]), axis=0)
                uc, cnt = np.unique(pairs[:, 0], return_counts=True)
                rich.loc[uc] = cnt
            result[(s, nside)] = rich.to_numpy()
        print(f"  {s}: {len(matched)} matched species vs Art-12.")
    return result


# %% [markdown]
# ## Main sweep: (strategy x nside x richness-surface)

# %%
art12_rich = load_art12_richness()
rng = np.random.default_rng(RANDOM_STATE)

rows: list[dict] = []
for strategy in STRATEGIES:
    freq = pd.read_parquet(STRATEGY_FREQ_PARQUET[strategy])
    print(f"\n{'='*64}\n=== {strategy} ===\n{'='*64}")
    for nside in NSIDES:
        with xr.open_dataset(STRATEGY_RICHNESS_NC[strategy], group=f"nside_{nside}") as ds:
            cells = ds["cell"].values.astype(np.int64)
            raw_atlas = ds["richness_atlas"].values.astype(float)
            rangemap = ds["richness_rangemap"].values.astype(float)
            synthetic = str(ds.attrs.get("synthetic", "?"))

        pred_cells, X, bio_vars = load_predictors(nside)
        if not np.array_equal(pred_cells, cells):
            order = {int(c): i for i, c in enumerate(pred_cells)}
            X = X[[order[int(c)] for c in cells]]

        presence = species_presence_cells(freq, nside)
        tgb = target_group_intensity(freq, nside, cells)
        art12_layer = art12_rich.get((strategy, nside)) if art12_rich else None

        # Three surfaces.
        tgb_surf, tgb_fit, censored = stack_predicted_richness(
            presence, cells, X, tgb, "target_group", rng, MAX_SPECIES)
        rnd_surf, rnd_fit, _ = stack_predicted_richness(
            presence, cells, X, tgb, "random", rng, MAX_SPECIES)

        surfaces = {"raw": raw_atlas,
                    "sdm_target_group": tgb_surf,
                    "sdm_random": rnd_surf}
        for name, surf in surfaces.items():
            mis_a12 = (misidentified_pct(surf, art12_layer.astype(float))
                       if art12_layer is not None else float("nan"))
            mis_rm = misidentified_pct(surf, rangemap)
            rows.append({
                "strategy": strategy, "nside": nside, "surface": name,
                "misidentified_pct_vs_art12": (round(mis_a12, 2)
                                               if np.isfinite(mis_a12) else np.nan),
                "misidentified_pct_vs_rangemap": (round(mis_rm, 2)
                                                  if np.isfinite(mis_rm) else np.nan),
                "n_cells": int(len(cells)),
                "n_species_fitted": (tgb_fit if name == "sdm_target_group"
                                     else rnd_fit if name == "sdm_random" else 0),
                "n_species_censored": censored if name != "raw" else 0,
                "n_bio_vars": len(bio_vars), "synthetic": synthetic})
            a12s = f"{mis_a12:6.2f}" if np.isfinite(mis_a12) else "   nan"
            print(f"  nside={nside:>4} {name:<18} vs art12={a12s} "
                  f"vs rangemap={mis_rm:6.2f} "
                  f"(fitted={rows[-1]['n_species_fitted']}, censored={censored})")

results = pd.DataFrame(rows)
results.to_parquet(OUT_PARQUET, index=False)
print(f"\nsaved {OUT_PARQUET} ({len(results)} rows)")


# %% [markdown]
# ## Headline JSON — Nside 256 verdict inputs
#
# Per strategy at the reference scale: raw (uncorrected baseline) vs the two SDM
# surfaces, the reduction in misidentification each delivers (percentage
# points), whether either reaches the H&J reference band, and whether the
# uncorrected baseline reproduces the sibling number (pipeline sanity check).

# %%
def _pick(sub: pd.DataFrame, surface: str, metric: str) -> float:
    r = sub[sub["surface"] == surface]
    if r.empty or pd.isna(r[metric].iloc[0]):
        return float("nan")
    return float(r[metric].iloc[0])


headline: dict = {
    "headline_nside": HEADLINE_NSIDE, "hotspot_fraction": HOTSPOT_FRACTION,
    "hj_reference_range_pct": list(HJ_RANGE),
    "sibling_baseline_pct": SIBLING_BASELINE,
    "min_species_occ": MIN_SPECIES_OCC, "maxent_features": MAXENT_FEATURES,
    "smoke_test": bool(MAX_SPECIES) or NSIDES != ALL_NSIDES or STRATEGIES != ALL_STRATEGIES,
    "per_strategy": {}}

ref = results[results["nside"] == HEADLINE_NSIDE]
for strategy in STRATEGIES:
    sub = ref[ref["strategy"] == strategy]
    if sub.empty:
        continue
    use_a12 = sub["misidentified_pct_vs_art12"].notna().any()
    metric = "misidentified_pct_vs_art12" if use_a12 else "misidentified_pct_vs_rangemap"
    raw = _pick(sub, "raw", metric)
    tgb = _pick(sub, "sdm_target_group", metric)
    rnd = _pick(sub, "sdm_random", metric)
    # Sanity check: the parent/sibling 89.9 % (museum) / 97.8 % (allbor) baselines
    # are the raw-atlas-vs-EOO-hull-rangemap numbers (the H&J replication metric),
    # so validate against the rangemap comparator regardless of the headline one.
    raw_vs_rangemap = _pick(sub, "raw", "misidentified_pct_vs_rangemap")
    base_target = SIBLING_BASELINE.get(strategy)
    baseline_ok = (bool(abs(raw_vs_rangemap - base_target) <= 3.0)
                   if np.isfinite(raw_vs_rangemap) and base_target is not None
                   else None)

    def _verdict(corr: float) -> dict:
        red = (raw - corr) if np.isfinite(raw) and np.isfinite(corr) else np.nan
        return {"misidentified_pct": round(corr, 2) if np.isfinite(corr) else None,
                "reduction_pp_vs_raw": round(red, 2) if np.isfinite(red) else None,
                "reaches_hj_range": (bool(HJ_RANGE[0] <= corr <= HJ_RANGE[1])
                                     if np.isfinite(corr) else False)}

    headline["per_strategy"][strategy] = {
        "comparator": metric,
        "raw_uncorrected_misidentified_pct": round(raw, 2) if np.isfinite(raw) else None,
        "raw_vs_rangemap_pct": (round(raw_vs_rangemap, 2)
                                if np.isfinite(raw_vs_rangemap) else None),
        "sdm_target_group": _verdict(tgb),
        "sdm_random": _verdict(rnd),
        "baseline_reproduces_sibling": baseline_ok,
        "synthetic": str(sub["synthetic"].iloc[0])}

with open(OUT_HEADLINE, "w") as f:
    json.dump(headline, f, indent=2, default=str)
print(f"\nsaved {OUT_HEADLINE}")
print(json.dumps(headline, indent=2, default=str))

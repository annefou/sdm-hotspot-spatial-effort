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
# # 06 — Reproduction arm: random vs target-group background MaxEnt AUC
#
# Reproduce Phillips et al. (2009) Table 2 (Maxent row) on the Elith et al.
# (2006) NCEAS benchmark, using the *same* `elapid` MaxEnt engine as the Iberian
# arm. For each species we fit MaxEnt twice — once against the region's **random
# background** (`train_bg`, 10000 uniform sites) and once against the
# **target-group background** (the pooled presence localities of *all* species in
# the same biological target group, which carry the shared sampling bias) — then
# evaluate AUC on the *independent* presence–absence test sites.
#
# **Validation target (Phillips Table 2, Maxent, mean over 226 species):**
# random background mean AUC ≈ **0.7276**; target-group background ≈ **0.7569**;
# target-group > random (P < 0.001, paired Wilcoxon). Reproducing the *direction*
# and *rough magnitude* of the gain is success — exact decimals will differ
# because `elapid`/`maxnet` is a different MaxEnt implementation than Phillips'
# original Maxent.
#
# **Method (mirrors Phillips):**
#
# 1. *Random-background model* — species presence (`train_po` rows for that
#    `spid`) vs `train_bg`, on the region's env predictors.
# 2. *Target-group-background model* — same presence, but background = the
#    env values at the pooled presence localities of every species in the same
#    `group` (Phillips' target-group background).
# 3. *Evaluate* — predict at the PA evaluation sites (`test_env`), AUC against
#    the 0/1 PA column (`test_pa`) via `sklearn.metrics.roc_auc_score`.
# 4. *Aggregate* — per-species AUC for random vs target-group; paired difference;
#    per-region/group means; overall mean (the Table 2 comparison).
#
# Feature set: `elapid` MaxEnt with linear + quadratic + hinge (Phillips used
# Maxent's full features — we do not cripple it). Overridable via `REPRO_FEATURES`.

# %%
import json
import os
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr
from elapid import MaxentModel
from scipy.stats import wilcoxon
from sklearn.metrics import roc_auc_score

warnings.filterwarnings("ignore")  # silence elapid/sklearn convergence chatter

# %% [markdown]
# ## Constants and paths

# %%
ROOT = Path("..").resolve()
DATA = ROOT / "data"
DISDAT_DIR = DATA / "disdat"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OUT_PARQUET = RESULTS_DIR / "repro_phillips_auc.parquet"
OUT_HEADLINE = RESULTS_DIR / "repro_headline.json"

# Non-predictor columns common to the disdat tables.
META_COLS = {"siteid", "spid", "x", "y", "occ", "group"}

# Phillips Table 2 (Maxent row, mean over 226 species) — the validation target.
PHILLIPS_TABLE2_MAXENT = {"random": 0.7276, "target_group": 0.7569}

# Per-Table-4 the gain is strongest for the most-biased regions (esp. CAN).
MOST_BIASED_REGIONS = ["CAN"]

MIN_PRESENCE = int(os.environ.get("REPRO_MIN_PRESENCE", "5"))  # min occ to fit
MAXENT_FEATURES = os.environ.get(
    "REPRO_FEATURES", "linear,quadratic,hinge").split(",")
RANDOM_STATE = 20260530

# Smoke-test knob: cap regions for a quick DAG check (empty => all 6).
REGIONS = (os.environ.get("REPRO_REGIONS", "AWT,CAN,NSW,NZ,SA,SWI").split(","))

print(f"REGIONS         = {REGIONS}")
print(f"MAXENT_FEATURES = {MAXENT_FEATURES}")
print(f"MIN_PRESENCE    = {MIN_PRESENCE}")
print(f"disdat dir      = {DISDAT_DIR} (exists={DISDAT_DIR.exists()})")


# %% [markdown]
# ## Load helpers
#
# `pyreadr.read_r` returns an ordered dict keyed by the R object name (or `None`
# for an unnamed top-level data.frame, as here). Predictor columns are every
# column that is not metadata.

# %%
def load_rds(name: str) -> pd.DataFrame:
    """Load one disdat .rds table as a DataFrame."""
    result = pyreadr.read_r(str(DISDAT_DIR / name))
    return next(iter(result.values()))


def predictor_cols(df: pd.DataFrame) -> list[str]:
    """Env predictor column names = all columns minus the known metadata."""
    return [c for c in df.columns if c not in META_COLS]


def test_pa_files(region: str) -> list[tuple[str, str | None]]:
    """[(test_pa filename, group)] for a region; group parsed from the suffix.

    `<R>test_pa.rds` -> group None (single-group region); `<R>test_pa_<g>.rds`
    -> group `<g>` (AWT bird/plant; NSW ba/db/...)."""
    out: list[tuple[str, str | None]] = []
    for path in sorted(DISDAT_DIR.glob(f"{region}test_pa*.rds")):
        m = re.match(rf"{region}test_pa(?:_(\w+))?\.rds$", path.name)
        if m:
            out.append((path.name, m.group(1)))
    return out


# %% [markdown]
# ## Build the two backgrounds per group
#
# - **random** — the region's `train_bg` env rows (10000 uniform sites).
# - **target-group** — env values at the pooled presence localities of *all*
#   species in the group (`train_po` rows with `group == g`), so the background
#   inherits the same spatial sampling bias as the occurrences.

# %%
def standardise(train: np.ndarray, *others: np.ndarray):
    """Z-score `others` using `train`'s column mean/std (NaN-mean-imputed)."""
    mu = np.nanmean(train, axis=0)
    inds = np.where(np.isnan(train))
    train = train.copy()
    train[inds] = np.take(mu, inds[1])
    mu = train.mean(axis=0)
    sigma = train.std(axis=0)
    sigma[sigma == 0] = 1.0
    out = []
    for arr in others:
        arr = arr.copy().astype(float)
        bad = np.where(np.isnan(arr))
        arr[bad] = np.take(mu, bad[1])
        out.append((arr - mu) / sigma)
    return ((train - mu) / sigma, *out)


def fit_predict_auc(pres: np.ndarray, bg: np.ndarray, test_x: np.ndarray,
                    test_y: np.ndarray) -> float:
    """Fit MaxEnt (presence vs background), predict at test sites, return AUC."""
    x = np.vstack([pres, bg])
    y = np.concatenate([np.ones(len(pres)), np.zeros(len(bg))])
    model = MaxentModel(feature_types=MAXENT_FEATURES, use_sklearn=True,
                        random_state=RANDOM_STATE, n_cpus=1)
    model.fit(x, y)
    pred = np.asarray(model.predict(test_x), dtype=float).ravel()
    pred = np.nan_to_num(pred, nan=0.0)
    return float(roc_auc_score(test_y, pred))


# %% [markdown]
# ## Per-region/group sweep
#
# For every group: build random + target-group background once, then fit and
# evaluate every species twice. A species is skipped only if it has fewer than
# `MIN_PRESENCE` training presences or its PA test column has no
# presence/absence variation (AUC undefined).

# %%
def run_group(region: str, group: str | None, pa_name: str,
              po: pd.DataFrame, bg: pd.DataFrame) -> list[dict]:
    """Fit random + target-group MaxEnt for every species in one group."""
    env = predictor_cols(po)
    test_pa = load_rds(pa_name)
    suffix = "" if group is None else f"_{group}"
    test_env = load_rds(f"{region}test_env{suffix}.rds")
    species = [c for c in test_pa.columns if c not in META_COLS]

    # The group's presence rows (target-group background) and the env matrices.
    po_group = po if group is None else po[po["group"] == group]
    tg_bg_raw = po_group[env].to_numpy(float)
    rand_bg_raw = bg[env].to_numpy(float)
    test_raw = test_env[env].to_numpy(float)
    train_ref = po[env].to_numpy(float)
    _, tg_bg, rand_bg, test_x = standardise(
        train_ref, tg_bg_raw, rand_bg_raw, test_raw)

    rows: list[dict] = []
    for sp in species:
        pres_raw = po_group[po_group["spid"] == sp][env].to_numpy(float)
        if len(pres_raw) < MIN_PRESENCE:
            continue
        test_y = test_pa[sp].to_numpy(float)
        if test_y.sum() == 0 or test_y.sum() == len(test_y):
            continue
        _, pres = standardise(train_ref, pres_raw)
        try:
            auc_rand = fit_predict_auc(pres, rand_bg, test_x, test_y)
            auc_tg = fit_predict_auc(pres, tg_bg, test_x, test_y)
        except Exception as exc:  # noqa: BLE001 — one bad fit must not kill the run
            print(f"      {region}/{group}/{sp} fit failed ({exc}); skipped")
            continue
        rows.append({
            "region": region, "group": group or region.lower(), "species": sp,
            "n_presence": int(len(pres_raw)), "n_test": int(len(test_y)),
            "n_test_pos": int(test_y.sum()),
            "auc_random": round(auc_rand, 4),
            "auc_targetgroup": round(auc_tg, 4)})
    return rows


# %%
all_rows: list[dict] = []
for region in REGIONS:
    po = load_rds(f"{region}train_po.rds")
    bg = load_rds(f"{region}train_bg.rds")
    groups = test_pa_files(region)
    print(f"\n=== {region} ({len(groups)} group file(s)) ===")
    for pa_name, group in groups:
        rows = run_group(region, group, pa_name, po, bg)
        all_rows.extend(rows)
        if rows:
            r = pd.DataFrame(rows)
            print(f"  {pa_name:<24} n={len(rows):>3}  "
                  f"random={r['auc_random'].mean():.4f}  "
                  f"target-group={r['auc_targetgroup'].mean():.4f}")

results = pd.DataFrame(all_rows)
results.to_parquet(OUT_PARQUET, index=False)
print(f"\nsaved {OUT_PARQUET} ({len(results)} species rows)")


# %% [markdown]
# ## Aggregate — the Table 2 comparison

# %%
mean_rand = float(results["auc_random"].mean())
mean_tg = float(results["auc_targetgroup"].mean())
delta = mean_tg - mean_rand
stat, pval = wilcoxon(results["auc_targetgroup"], results["auc_random"])

per_region = (results.groupby("region")[["auc_random", "auc_targetgroup"]]
              .mean().round(4))
per_region["delta"] = (per_region["auc_targetgroup"]
                       - per_region["auc_random"]).round(4)
per_region["n_species"] = results.groupby("region").size()

per_group = (results.groupby(["region", "group"])[["auc_random", "auc_targetgroup"]]
             .mean().round(4))
per_group["delta"] = (per_group["auc_targetgroup"]
                      - per_group["auc_random"]).round(4)

print("\n--- per region (mean AUC) ---")
print(per_region.to_string())
print(f"\nOVERALL  random={mean_rand:.4f}  target-group={mean_tg:.4f}  "
      f"delta={delta:+.4f}")
print(f"Phillips  random={PHILLIPS_TABLE2_MAXENT['random']}  "
      f"target-group={PHILLIPS_TABLE2_MAXENT['target_group']}  "
      f"delta={PHILLIPS_TABLE2_MAXENT['target_group'] - PHILLIPS_TABLE2_MAXENT['random']:+.4f}")
print(f"paired Wilcoxon (target-group vs random): stat={stat:.1f}  p={pval:.2e}")


# %% [markdown]
# ## Headline JSON

# %%
headline = {
    "method": "elapid MaxEnt (presence-background)",
    "maxent_features": MAXENT_FEATURES,
    "min_presence": MIN_PRESENCE,
    "n_species": int(len(results)),
    "regions": sorted(results["region"].unique().tolist()),
    "overall_mean_auc": {
        "random": round(mean_rand, 4),
        "target_group": round(mean_tg, 4),
        "delta": round(delta, 4),
    },
    "target_group_improves": bool(mean_tg > mean_rand),
    "wilcoxon": {"statistic": float(stat), "p_value": float(pval),
                 "significant_p001": bool(pval < 0.001)},
    "phillips_table2_maxent": PHILLIPS_TABLE2_MAXENT,
    "phillips_table2_delta": round(
        PHILLIPS_TABLE2_MAXENT["target_group"]
        - PHILLIPS_TABLE2_MAXENT["random"], 4),
    "per_region": {
        r: {"random": float(per_region.loc[r, "auc_random"]),
            "target_group": float(per_region.loc[r, "auc_targetgroup"]),
            "delta": float(per_region.loc[r, "delta"]),
            "n_species": int(per_region.loc[r, "n_species"])}
        for r in per_region.index},
    "per_group": {
        f"{r}/{g}": {"random": float(per_group.loc[(r, g), "auc_random"]),
                     "target_group": float(per_group.loc[(r, g), "auc_targetgroup"]),
                     "delta": float(per_group.loc[(r, g), "delta"])}
        for (r, g) in per_group.index},
    "most_biased_regions": MOST_BIASED_REGIONS,
    "most_biased_largest_gain": bool(
        per_region["delta"].idxmax() in MOST_BIASED_REGIONS
        if len(per_region) else False),
}

with open(OUT_HEADLINE, "w") as f:
    json.dump(headline, f, indent=2)
print(f"\nsaved {OUT_HEADLINE}")
print(json.dumps(headline["overall_mean_auc"], indent=2))

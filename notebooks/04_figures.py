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
# # 04 — Figures
#
# Main result: hotspot **misidentification (%)** for the three richness surfaces
# — uncorrected raw GBIF richness, target-group-background SDM richness, and
# random-background SDM richness — benchmarked against the EU Article 12 expert
# rangemap. Left panel: the headline scale (HEALPix Nside 256 ≈ 25 km) as a
# grouped bar chart per strategy. Right panel: the full Nside ladder (16–512) as
# lines, so the scale-dependence is visible. The Hurlbert & Jetz 2007 reference
# band (47.8–68.6 %) marks where a *successful* correction would land.
#
# Reads `results/sdm_misidentification.parquet` + `results/headline.json`.
#
# **Inline display rule:** every `fig.savefig(...)` is paired with `plt.show()`
# (MyST inline display). No `matplotlib.use('Agg')`.

# %%
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.style.use("seaborn-v0_8-whitegrid")

# %%
RESULTS_DIR = Path("../results")
FIGURES_DIR = Path("../figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

HEADLINE_NSIDE = 256
HJ_RANGE = (47.8, 68.6)
SURFACES = ["raw", "sdm_target_group", "sdm_random"]
SURFACE_LABEL = {"raw": "raw GBIF richness",
                 "sdm_target_group": "target-group-background SDM",
                 "sdm_random": "random-background SDM"}
SURFACE_COLOR = {"raw": "#7f7f7f", "sdm_target_group": "#2ca02c",
                 "sdm_random": "#d62728"}

results = pd.read_parquet(RESULTS_DIR / "sdm_misidentification.parquet")
with open(RESULTS_DIR / "headline.json") as f:
    headline = json.load(f)

any_strat = next(iter(headline["per_strategy"].values()), {})
metric = any_strat.get("comparator", "misidentified_pct_vs_art12")
metric_label = ("vs Article 12 expert rangemap" if metric.endswith("art12")
                else "vs EOO-hull rangemap")
strategies = [s for s in ["museum", "allbor"] if s in results["strategy"].unique()]
print(f"Plotting metric: {metric} ({metric_label}); strategies={strategies}")


# %% [markdown]
# ## Main result figure

# %%
fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 6),
                               gridspec_kw={"width_ratios": [1, 1.15]})

# --- Left: grouped bars at the headline scale ---
ref = results[results["nside"] == HEADLINE_NSIDE]
axL.axhspan(HJ_RANGE[0], HJ_RANGE[1], color="green", alpha=0.12, zorder=0,
            label=f"Hurlbert & Jetz 2007 ({HJ_RANGE[0]}–{HJ_RANGE[1]} %)")
n_surf = len(SURFACES)
bar_w = 0.8 / n_surf
xpos = np.arange(len(strategies))
for j, surf in enumerate(SURFACES):
    vals = []
    for strat in strategies:
        r = ref[(ref["strategy"] == strat) & (ref["surface"] == surf)]
        vals.append(float(r[metric].iloc[0])
                    if len(r) and pd.notna(r[metric].iloc[0]) else np.nan)
    axL.bar(xpos + (j - (n_surf - 1) / 2) * bar_w, vals, bar_w,
            color=SURFACE_COLOR[surf], label=SURFACE_LABEL[surf])
    for xi, v in zip(xpos + (j - (n_surf - 1) / 2) * bar_w, vals):
        if np.isfinite(v):
            axL.annotate(f"{v:.1f}", (xi, v), ha="center", va="bottom",
                         fontsize=8)
axL.set_xticks(xpos)
axL.set_xticklabels(strategies)
axL.set_ylabel(f"Hotspot misidentification (%)  —  top-5 % non-overlap\n{metric_label}")
axL.set_ylim(0, 100)
axL.set_xlabel("Basis-of-record strategy")
axL.set_title(f"At Nside {HEADLINE_NSIDE} (≈ 25 km)", fontsize=11)
axL.legend(loc="lower left", fontsize=8, framealpha=0.92)

# --- Right: full ladder ---
axR.axhspan(HJ_RANGE[0], HJ_RANGE[1], color="green", alpha=0.12, zorder=0)
linestyles = {"museum": "-", "allbor": "--"}
for strat in strategies:
    for surf in SURFACES:
        sub = (results[(results["strategy"] == strat) & (results["surface"] == surf)]
               .sort_values("nside"))
        if sub.empty or sub[metric].isna().all():
            continue
        axR.plot(sub["nside"], sub[metric], marker="o", lw=2.0,
                 ls=linestyles.get(strat, "-"), color=SURFACE_COLOR[surf],
                 label=f"{strat} — {SURFACE_LABEL[surf]}")
axR.set_xscale("log", base=2)
axR.set_xticks(sorted(results["nside"].unique()))
axR.get_xaxis().set_major_formatter(plt.matplotlib.ticker.ScalarFormatter())
axR.set_xlabel("HEALPix Nside (finer →)")
axR.set_ylabel(f"Misidentification (%) {metric_label}")
axR.set_ylim(0, 100)
axR.set_title("Across the scale ladder", fontsize=11)
axR.legend(loc="lower right", fontsize=7, framealpha=0.92)

smoke = headline.get("smoke_test", False)
synthetic = str(ref["synthetic"].iloc[0]).lower() == "true" if len(ref) else False
tag = []
if synthetic:
    tag.append("SYNTHETIC DEMO DATA")
if smoke:
    tag.append("SMOKE TEST (capped run)")
if tag:
    fig.text(0.5, 0.5, " / ".join(tag), fontsize=22, color="grey", alpha=0.25,
             ha="center", va="center", rotation=18, zorder=5)

fig.suptitle(
    "Does target-group background recover effort-distorted Iberian-bird hotspots?\n"
    "Phillips et al. 2009 correction tested where coverage rarefaction failed (sibling chain)",
    fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(FIGURES_DIR / "main_result.png", dpi=150, bbox_inches="tight")
fig.savefig(FIGURES_DIR / "main_result.pdf", bbox_inches="tight")
plt.show()  # required for MyST inline display
print(f"saved {FIGURES_DIR / 'main_result.png'} (+ .pdf)")


# %% [markdown]
# ## Headline summary (printed)

# %%
for strat, d in headline["per_strategy"].items():
    print(f"\n{strat}  [comparator: {d['comparator']}, synthetic={d['synthetic']}]")
    print(f"  raw uncorrected         : {d['raw_uncorrected_misidentified_pct']} %")
    tg, rd = d["sdm_target_group"], d["sdm_random"]
    print(f"  target-group SDM        : {tg['misidentified_pct']} % "
          f"(Δ {tg['reduction_pp_vs_raw']} percentage points, "
          f"reaches H&J band: {tg['reaches_hj_range']})")
    print(f"  random-background SDM   : {rd['misidentified_pct']} % "
          f"(Δ {rd['reduction_pp_vs_raw']} percentage points, "
          f"reaches H&J band: {rd['reaches_hj_range']})")
    print(f"  baseline reproduces sibling: {d['baseline_reproduces_sibling']}")

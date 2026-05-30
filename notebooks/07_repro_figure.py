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
# # 07 — Reproduction arm figure: random vs target-group background AUC
#
# Reproduce Phillips et al. (2009) Table 2 visually: mean per-species AUC under
# random vs target-group background, overall and per region, with Phillips'
# Table 2 (Maxent) reference values marked. Validation = target-group > random
# overall, with the largest gains in the most-biased regions (esp. CAN).

# %%
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.style.use("seaborn-v0_8-whitegrid")

# %%
ROOT = Path("..").resolve()
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

AUC_PARQUET = RESULTS_DIR / "repro_phillips_auc.parquet"
HEADLINE_JSON = RESULTS_DIR / "repro_headline.json"
OUT_PNG = FIGURES_DIR / "repro_phillips.png"
OUT_PDF = FIGURES_DIR / "repro_phillips.pdf"

results = pd.read_parquet(AUC_PARQUET)
with open(HEADLINE_JSON) as f:
    headline = json.load(f)

PHILLIPS = headline["phillips_table2_maxent"]
C_RAND, C_TG = "#7f8c8d", "#27ae60"  # grey = random, green = target-group

# %% [markdown]
# ## Assemble overall + per-region means

# %%
overall = headline["overall_mean_auc"]
per_region = headline["per_region"]
region_order = sorted(per_region, key=lambda r: per_region[r]["delta"])
labels = ["OVERALL"] + region_order
rand_vals = [overall["random"]] + [per_region[r]["random"] for r in region_order]
tg_vals = [overall["target_group"]] + [per_region[r]["target_group"]
                                        for r in region_order]
n_sp = [headline["n_species"]] + [per_region[r]["n_species"] for r in region_order]

# %% [markdown]
# ## Figure: grouped bars (random vs target-group) + Phillips reference lines

# %%
fig, ax = plt.subplots(figsize=(11, 6))
x = np.arange(len(labels))
w = 0.38

b1 = ax.bar(x - w / 2, rand_vals, w, label="random background",
            color=C_RAND, edgecolor="black", linewidth=0.5)
b2 = ax.bar(x + w / 2, tg_vals, w, label="target-group background",
            color=C_TG, edgecolor="black", linewidth=0.5)

# Phillips Table 2 (Maxent) reference values — dashed lines.
ax.axhline(PHILLIPS["random"], color=C_RAND, ls="--", lw=1.4,
           label=f"Phillips random ({PHILLIPS['random']})")
ax.axhline(PHILLIPS["target_group"], color=C_TG, ls="--", lw=1.4,
           label=f"Phillips target-group ({PHILLIPS['target_group']})")

# Delta annotation above each pair.
for xi, (lo, hi) in enumerate(zip(rand_vals, tg_vals)):
    ax.annotate(f"{hi - lo:+.3f}", (xi, max(lo, hi) + 0.012),
                ha="center", va="bottom", fontsize=8, color=C_TG if hi >= lo else "#c0392b")

ax.set_xticks(x)
ax.set_xticklabels([f"{lab}\n(n={n})" for lab, n in zip(labels, n_sp)])
ax.set_ylabel("Mean per-species AUC")
ax.set_ylim(0.45, 0.95)
ax.set_title("Reproduction (Arm A): target-group background improves MaxEnt AUC\n"
             "Elith et al. 2006 NCEAS benchmark — elapid MaxEnt — vs Phillips 2009 Table 2",
             fontsize=11)
ax.legend(loc="upper right", fontsize=8, framealpha=0.95)
ax.bar_label(b1, fmt="%.3f", padding=2, fontsize=7)
ax.bar_label(b2, fmt="%.3f", padding=2, fontsize=7)

fig.tight_layout()
fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight")
fig.savefig(OUT_PDF, bbox_inches="tight")
plt.show()
print(f"saved {OUT_PNG}\nsaved {OUT_PDF}")
print(f"overall: random={overall['random']} target-group={overall['target_group']} "
      f"delta={overall['delta']:+.4f}")

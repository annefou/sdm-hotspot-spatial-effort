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
# # 05 — Reproduction arm: download the Elith et al. (2006) NCEAS dataset
#
# **Reproduction arm (Arm A).** This is a *separate, parallel* pipeline from the
# Iberian-hotspot arm (notebooks 01–04). Its sole job is to reproduce Phillips
# et al. (2009, `10.1890/07-2153.1`) Table 2 headline result — that
# **target-group background improves per-species AUC** — on Phillips' *own* data,
# using the *same* MaxEnt engine (`elapid`) the Iberian arm uses. If this arm
# reproduces Phillips' AUC gains, our target-group-background implementation is
# demonstrably faithful to the paper, and any negative result in the Iberian arm
# is attributable to the *hotspot question*, not a broken implementation.
#
# **Data provenance.** The 226-species / 6-region presence-only + independent
# presence–absence benchmark from Elith et al. (2006, *Ecography* 29:129–151) is
# distributed as the R package **`disdat`** (Elith, Graham, Valavi et al.). The
# rspatial/disdat GitHub repo ships each table as an `.rds` file under
# `inst/extdata/`. We fetch the raw `.rds` files directly and read them in pure
# Python with **`pyreadr`** — no R runtime required.
#
# Six regions: AWT (Australian Wet Tropics), CAN (Ontario, Canada), NSW (NE New
# South Wales), NZ (New Zealand), SA (South America), SWI (Switzerland). Some
# regions are split into biological target groups (AWT: bird, plant; NSW: 8
# groups ba/db/nb/ot/ou/rt/ru/sr), which is encoded in the test-file filename
# suffix and in the `group` column of the presence-only training tables.
#
# Per region/group there are four table types:
#
# - `<REGION>train_po.rds` — presence-only training rows: `spid`, `group`, `x`,
#   `y`, env predictors. One row per presence locality.
# - `<REGION>train_bg.rds` — 10000 random background sites (the RANDOM
#   background), same env columns.
# - `<REGION>test_pa[_<group>].rds` — independent presence/absence evaluation
#   sites: one 0/1 column per species (named by `spid`), plus `siteid`, `x`, `y`.
# - `<REGION>test_env[_<group>].rds` — env predictors at those same PA sites.

# %%
import hashlib
import json
import os
from pathlib import Path

import requests

# %% [markdown]
# ## Paths and the disdat source registry

# %%
ROOT = Path("..").resolve()
DATA = ROOT / "data"
DISDAT_DIR = DATA / "disdat"
RAW_DIR = DATA / "raw"
DISDAT_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

GH_API = "https://api.github.com/repos/rspatial/disdat/contents/inst/extdata"
GH_RAW = "https://raw.githubusercontent.com/rspatial/disdat/master/inst/extdata/"
SOURCES_JSON = RAW_DIR / "repro_sources.json"

# Only download the rds tables we model on; skip auxiliary files (borders, etc).
KEEP_SUFFIXES = ("train_po", "train_bg")
KEEP_PREFIXES = ("test_pa", "test_env")  # match anywhere after the region code

REGIONS = ["AWT", "CAN", "NSW", "NZ", "SA", "SWI"]

print(f"disdat cache dir = {DISDAT_DIR}")


# %% [markdown]
# ## Enumerate the `.rds` files via the GitHub API
#
# Self-contained: list the directory, keep only the modelling tables, and record
# which region (and group, parsed from the test-file suffix) each belongs to.

# %%
def is_modelling_table(name: str) -> bool:
    """True for the train/test .rds tables we model on."""
    if not name.endswith(".rds"):
        return False
    stem = name[:-4]
    return (any(stem.endswith(s) for s in KEEP_SUFFIXES)
            or any(p in stem for p in KEEP_PREFIXES))


def enumerate_rds() -> list[str]:
    """Return the modelling-table .rds filenames from the disdat repo."""
    resp = requests.get(GH_API, timeout=60)
    resp.raise_for_status()
    names = sorted(entry["name"] for entry in resp.json())
    keep = [n for n in names if is_modelling_table(n)]
    print(f"GitHub lists {len(names)} files; keeping {len(keep)} modelling tables.")
    return keep


rds_files = enumerate_rds()
for r in REGIONS:
    region_files = [f for f in rds_files if f.startswith(r)]
    print(f"  {r:<4}: {len(region_files)} tables")


# %% [markdown]
# ## Download (cache on disk; skip if already present and non-empty)

# %%
def download_rds(name: str) -> dict:
    """Fetch one .rds into the cache; return a registry record with sha256."""
    dest = DISDAT_DIR / name
    if dest.exists() and dest.stat().st_size > 0:
        content = dest.read_bytes()
    else:
        resp = requests.get(GH_RAW + name, timeout=120)
        resp.raise_for_status()
        content = resp.content
        dest.write_bytes(content)
    return {
        "name": name,
        "url": GH_RAW + name,
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


records = [download_rds(name) for name in rds_files]
total_mb = sum(r["bytes"] for r in records) / 1e6
print(f"cached {len(records)} files ({total_mb:.1f} MB) in {DISDAT_DIR}")


# %% [markdown]
# ## Write the provenance registry

# %%
registry = {
    "dataset": "Elith et al. (2006) NCEAS species distribution modelling benchmark",
    "primary_reference": {
        "citation": ("Elith J, Graham CH, Anderson RP, et al. (2006) Novel methods "
                     "improve prediction of species' distributions from occurrence "
                     "data. Ecography 29:129-151."),
        "doi": "10.1111/j.2006.0906-7590.04596.x",
    },
    "reproduction_target_paper": {
        "citation": ("Phillips SJ, Dudik M, Elith J, et al. (2009) Sample selection "
                     "bias and presence-only distribution models: implications for "
                     "background and pseudo-absence data. Ecological Applications "
                     "19(1):181-197."),
        "doi": "10.1890/07-2153.1",
        "validation_target_table2_maxent": {
            "random_background_mean_auc": 0.7276,
            "target_group_background_mean_auc": 0.7569,
            "n_species": 226,
        },
    },
    "distribution_package": {
        "name": "disdat",
        "description": ("R data package bundling the Elith et al. 2006 NCEAS "
                        "presence-only + independent presence-absence benchmark."),
        "repository": "https://github.com/rspatial/disdat",
        "github_api": GH_API,
        "raw_base": GH_RAW,
        "vignette": ("https://cran.r-project.org/web/packages/disdat/vignettes/"
                     "modeling.html"),
        "read_in_python_via": "pyreadr (no R dependency)",
        "license": "GPL (>= 3)",
    },
    "regions": REGIONS,
    "files": records,
}

with open(SOURCES_JSON, "w") as f:
    json.dump(registry, f, indent=2)
print(f"wrote {SOURCES_JSON}")
print(json.dumps({k: registry[k] for k in ("dataset", "regions")}, indent=2))
print(f"file count in registry: {len(registry['files'])}")

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
# # 02 — Data clean (HEALPix binning, per-species occurrences, target-group background, CHELSA predictors)
#
# Builds the analysis-ready substrate for the **target-group-background SDM**
# test (Phillips et al. 2009). Reuses the sibling chain's HEALPix-NESTED binning
# verbatim and adds the three things the SDM needs that the siblings did not
# keep:
#
# 1. **Per-(strategy, nside, cell, species_id) atlas record counts** — the
#    occurrence layer (modern, year >= 2000). Per-species presence cells come
#    from this; the per-cell **raw richness** (distinct species) is the
#    uncorrected baseline surface.
# 2. **Per-(strategy, nside, cell) target-group intensity** — total all-species
#    record count per cell = Phillips' target-group background weight (the
#    background that carries the same spatial sampling bias as the occurrences).
# 3. **Per-(nside, cell) CHELSA predictor samples** — the bioclim layers from
#    `01` sampled to each Iberian HEALPix cell centre. These are the SDM
#    covariates (the analogue of Phillips' 11–13 environmental layers).
#
# Year-split at 2000, Iberia bbox, full Nside ladder 16–512. NESTED via
# `healpix-geo` (DOMAIN.md). Outputs NetCDF + Parquet — never `.npz`.
#
# Outputs (`data/clean/`):
#
# - `richness_<strategy>.nc` — one group per Nside, `richness_atlas` +
#   `richness_rangemap` on `cell` (same schema as the siblings, so 03's
#   gold-standard comparison is drop-in).
# - `atlas_freq_<strategy>.parquet` — (nside, cell, species_id, count) long-form
#   atlas record counts. Source of per-species presences AND target-group
#   intensity.
# - `species_index_<strategy>.parquet` — (species_id, species) map.
# - `predictors_cells.nc` — one group per Nside, bio* covariates on `cell`.
# - `species_eoo_polygons.parquet` — per-species EOO hulls (rangemap layer).
# - `clean_report.json` — per-strategy counts + synthetic flags.

# %%
import json
import os
import zipfile
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from healpix_geo import nested as hp_nested
from shapely.geometry import MultiPoint, Polygon

# %% [markdown]
# ## Constants

# %%
# SDM_STRATEGIES limits which strategies are binned (e.g. "museum" to skip the
# 6.5 GB allbor zip for a fast museum-first run). Mirrors 03_analysis.py.
ALL_STRATEGIES = ["museum", "allbor"]
STRATEGIES = os.environ.get("SDM_STRATEGIES", ",".join(ALL_STRATEGIES)).split(",")
NSIDES = [16, 32, 64, 128, 256, 512]
DEPTHS = {n: int(np.log2(n)) for n in NSIDES}

ELLIPSOID = "WGS84"
YEAR_SPLIT = 2000

IBERIA_LON_MIN, IBERIA_LAT_MIN = -10.0, 35.0
IBERIA_LON_MAX, IBERIA_LAT_MAX = 4.0, 44.0

ROOT = Path("..").resolve()
DATA = ROOT / "data"
GBIF_DIR = DATA / "gbif"
RAW_DIR = DATA / "raw"
CLEAN_DIR = DATA / "clean"
CHELSA_NC = DATA / "external" / "chelsa" / "chelsa_iberia.nc"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

STRATEGY_ZIPS = {s: GBIF_DIR / f"birds_iberia_{s}.zip" for s in STRATEGIES}
STRATEGY_SYNTH_FLAGS = {
    s: RAW_DIR / f"USING_SYNTHETIC_DEMO_DATA_{s}.txt" for s in STRATEGIES}
STRATEGY_RICHNESS_NC = {s: CLEAN_DIR / f"richness_{s}.nc" for s in STRATEGIES}
STRATEGY_FREQ_PARQUET = {s: CLEAN_DIR / f"atlas_freq_{s}.parquet" for s in STRATEGIES}
STRATEGY_SPIDX_PARQUET = {s: CLEAN_DIR / f"species_index_{s}.parquet" for s in STRATEGIES}

PREDICTORS_NC = CLEAN_DIR / "predictors_cells.nc"
EOO_PARQUET = CLEAN_DIR / "species_eoo_polygons.parquet"
CLEAN_REPORT = CLEAN_DIR / "clean_report.json"

SYNTHETIC = {s: STRATEGY_SYNTH_FLAGS[s].exists() for s in STRATEGIES}
print(f"ROOT       = {ROOT}")
print(f"STRATEGIES = {STRATEGIES}")
print(f"NSIDES     = {NSIDES}")
print(f"SYNTHETIC  = {SYNTHETIC}")

report: dict = {
    "written_on": date.today().isoformat(), "strategies": STRATEGIES,
    "year_split": YEAR_SPLIT, "synthetic_per_strategy": SYNTHETIC,
    "nsides": NSIDES,
    "iberia_bbox": {"lon": [IBERIA_LON_MIN, IBERIA_LON_MAX],
                    "lat": [IBERIA_LAT_MIN, IBERIA_LAT_MAX]},
    "per_strategy": {}}


# %% [markdown]
# ## Iberian HEALPix-NESTED cell sets at each Nside

# %%
def iberian_pix(depth: int, nside: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """All NESTED cells at `depth` whose centre lies in the Iberia bbox."""
    pix_all = np.arange(12 * nside * nside, dtype=np.uint64)
    lon, lat = hp_nested.healpix_to_lonlat(pix_all, depth, ELLIPSOID)
    lon = np.where(lon > 180.0, lon - 360.0, lon)
    mask = ((lon >= IBERIA_LON_MIN) & (lon <= IBERIA_LON_MAX)
            & (lat >= IBERIA_LAT_MIN) & (lat <= IBERIA_LAT_MAX))
    return (pix_all[mask].astype(np.int64),
            lon[mask].astype(np.float32), lat[mask].astype(np.float32))


IBERIA_PIX: dict[int, np.ndarray] = {}
IBERIA_LON: dict[int, np.ndarray] = {}
IBERIA_LAT: dict[int, np.ndarray] = {}
for nside in NSIDES:
    pix, lon, lat = iberian_pix(DEPTHS[nside], nside)
    IBERIA_PIX[nside], IBERIA_LON[nside], IBERIA_LAT[nside] = pix, lon, lat
    print(f"  nside={nside:>4} (depth={DEPTHS[nside]}): {len(pix):>7,} cells")

report["n_cells_per_nside"] = {n: int(len(IBERIA_PIX[n])) for n in NSIDES}


# %% [markdown]
# ## GBIF zip streaming reader (1 M-row chunks, NA-dropped + bbox-filtered)

# %%
GBIF_CHUNKSIZE = 1_000_000


def iter_gbif_chunks(zip_path: Path,
                     chunksize: int = GBIF_CHUNKSIZE) -> Iterator[pd.DataFrame]:
    """Yield NA-dropped, bbox-filtered chunks of a GBIF SIMPLE_CSV zip."""
    if not zip_path.exists():
        raise FileNotFoundError(
            f"Expected GBIF zip at {zip_path} — re-run 01_data_download.py.")
    with zipfile.ZipFile(zip_path) as zf:
        candidates = [n for n in zf.namelist() if n.endswith(".csv")]
        if not candidates:
            raise RuntimeError(f"No CSV inside {zip_path}")
        with zf.open(candidates[0]) as src:
            reader = pd.read_csv(
                src, sep="\t",
                usecols=lambda c: c in {
                    "gbifID", "species", "decimalLatitude",
                    "decimalLongitude", "year", "basisOfRecord", "countryCode"},
                dtype={"gbifID": "Int64", "year": "Int64", "countryCode": "string"},
                chunksize=chunksize, on_bad_lines="skip")
            for raw in reader:
                df = raw.dropna(subset=["species", "decimalLatitude",
                                        "decimalLongitude", "year"])
                if df.empty:
                    continue
                lon = df["decimalLongitude"].astype(float)
                lat = df["decimalLatitude"].astype(float)
                in_bbox = ((lon >= IBERIA_LON_MIN) & (lon <= IBERIA_LON_MAX)
                           & (lat >= IBERIA_LAT_MIN) & (lat <= IBERIA_LAT_MAX))
                df = df.loc[in_bbox]
                if not df.empty:
                    yield df.reset_index(drop=True)


# %% [markdown]
# ## Per-species EOO-hull helpers (historical / rangemap layer)

# %%
def species_hull(points: np.ndarray) -> Polygon:
    """Convex hull of (lon, lat) points with n<3 fallbacks."""
    if len(points) >= 3:
        hull = MultiPoint(points).convex_hull
        if hull.geom_type != "Polygon":
            hull = hull.buffer(0.05)
    elif len(points) == 2:
        from shapely.geometry import LineString
        hull = LineString(points).buffer(0.1)
    else:
        from shapely.geometry import Point
        hull = Point(points[0]).buffer(0.2)
    return hull


def hull_to_cells(hull: Polygon, depth: int) -> np.ndarray:
    """NESTED cell IDs covered by `hull` at `depth`."""
    exterior = np.asarray(hull.exterior.coords)[:, :2]
    if np.allclose(exterior[0], exterior[-1]):
        exterior = exterior[:-1]
    if len(exterior) < 3:
        return np.empty(0, dtype=np.int64)
    cell_ids, _, _ = hp_nested.polygon_coverage(
        exterior, depth, ellipsoid=ELLIPSOID, flat=True)
    return np.asarray(cell_ids, dtype=np.int64)


def historical_cell_counts(species_hulls: dict[str, Polygon], nside: int,
                           iberian_arr: np.ndarray) -> pd.DataFrame:
    """Per-cell count of species whose EOO hull covers the cell (Iberian only)."""
    depth = DEPTHS[nside]
    counts: dict[int, int] = {}
    for hull in species_hulls.values():
        cells = hull_to_cells(hull, depth)
        cells = cells[np.isin(cells, iberian_arr)]
        for c in cells:
            counts[int(c)] = counts.get(int(c), 0) + 1
    if not counts:
        return pd.DataFrame({"cell": [], "richness": []}, dtype=np.int64)
    return pd.DataFrame({"cell": list(counts.keys()),
                         "richness": list(counts.values())}).astype(
        {"cell": np.int64, "richness": np.int64})


# %% [markdown]
# ## Process each strategy (streaming)
#
# Per chunk: split modern (>=2000, atlas) / historical (<2000, rangemap). Modern
# records accumulate per-(cell, species_id) record counts at every Nside — this
# is both the per-species presence layer and (summed over species) the
# target-group background intensity. Historical records accumulate per-species
# point sets for the EOO-hull rangemap.

# %%
all_eoo_records: list[dict] = []

for strategy in STRATEGIES:
    print(f"\n{'='*60}\n=== Strategy: {strategy} (synthetic={SYNTHETIC[strategy]}) ===\n{'='*60}")
    zip_path = STRATEGY_ZIPS[strategy]
    nc_path = STRATEGY_RICHNESS_NC[strategy]

    species_to_id: dict[str, int] = {}

    def _sid(sp: str) -> int:
        sid = species_to_id.get(sp)
        if sid is None:
            sid = len(species_to_id)
            species_to_id[sp] = sid
        return sid

    modern_counts: dict[int, list[np.ndarray]] = {n: [] for n in NSIDES}
    hist_pts: dict[str, list[np.ndarray]] = {}

    n_records_total = n_records_modern = n_records_historical = 0
    species_total: set[str] = set()
    species_modern: set[str] = set()
    species_historical: set[str] = set()
    year_min: int | None = None
    year_max: int | None = None

    for ci, chunk in enumerate(iter_gbif_chunks(zip_path), start=1):
        n_records_total += len(chunk)
        years = chunk["year"].astype(int).values
        cmin, cmax = int(years.min()), int(years.max())
        year_min = cmin if year_min is None else min(year_min, cmin)
        year_max = cmax if year_max is None else max(year_max, cmax)
        species_total.update(chunk["species"].unique().tolist())

        is_modern = years >= YEAR_SPLIT
        modern_chunk = chunk.loc[is_modern]
        hist_chunk = chunk.loc[~is_modern]
        n_records_modern += len(modern_chunk)
        n_records_historical += len(hist_chunk)

        if len(modern_chunk):
            species_modern.update(modern_chunk["species"].unique().tolist())
            mod_lon = modern_chunk["decimalLongitude"].astype(float).values
            mod_lat = modern_chunk["decimalLatitude"].astype(float).values
            mod_sp = modern_chunk["species"].values
            mod_sid = np.fromiter((_sid(s) for s in mod_sp), dtype=np.int64,
                                  count=len(mod_sp))
            for nside in NSIDES:
                cells = hp_nested.lonlat_to_healpix(
                    mod_lon, mod_lat, DEPTHS[nside], ELLIPSOID).astype(np.int64)
                pairs = np.column_stack([cells, mod_sid])
                uniq, cnt = np.unique(pairs, axis=0, return_counts=True)
                modern_counts[nside].append(
                    np.column_stack([uniq, cnt.astype(np.int64)]))

        if len(hist_chunk):
            species_historical.update(hist_chunk["species"].unique().tolist())
            for sp, grp in hist_chunk.groupby("species", sort=False):
                pts = grp[["decimalLongitude", "decimalLatitude"]].astype(float).values
                hist_pts.setdefault(sp, []).append(pts)

        print(f"  chunk {ci:>3}: +{len(chunk):>8,} rows "
              f"(modern +{len(modern_chunk):>8,}, hist +{len(hist_chunk):>7,}) "
              f"total {n_records_total:>11,}")

    print(f"\n  loaded     : {n_records_total:>10,} records, {len(species_total)} species")
    print(f"  modern     : {n_records_modern:>10,} records, {len(species_modern)} species")
    print(f"  historical : {n_records_historical:>10,} records, {len(species_historical)} species")

    strat_report: dict = {
        "synthetic": SYNTHETIC[strategy],
        "n_records_total": int(n_records_total),
        "n_species_total": int(len(species_total)),
        "n_records_modern": int(n_records_modern),
        "n_species_modern": int(len(species_modern)),
        "n_records_historical": int(n_records_historical),
        "n_species_historical": int(len(species_historical)),
        "year_min": int(year_min) if year_min is not None else None,
        "year_max": int(year_max) if year_max is not None else None}

    # --- Per-species EOO hulls (historical / rangemap layer) ---
    print(f"\n--- Building per-species EOO hulls (historical, {strategy}) ---")
    species_hulls: dict[str, Polygon] = {}
    n_species_eoo = len(hist_pts)
    for i, sp in enumerate(sorted(hist_pts.keys()), start=1):
        parts = hist_pts.pop(sp)
        pts = np.vstack(parts) if len(parts) > 1 else parts[0]
        hull = species_hull(pts)
        species_hulls[sp] = hull
        all_eoo_records.append({
            "strategy": strategy, "species": sp, "n_points": int(len(pts)),
            "hull_area_sqdeg": float(hull.area), "wkt": hull.wkt})
        if i % 50 == 0 or i == n_species_eoo:
            print(f"  built hull {i:>4}/{n_species_eoo}")
    strat_report["n_species_with_eoo"] = int(n_species_eoo)

    # --- species_id -> name map ---
    spidx_df = (pd.DataFrame({"species_id": list(species_to_id.values()),
                              "species": list(species_to_id.keys())})
                .sort_values("species_id").reset_index(drop=True))
    spidx_df.to_parquet(STRATEGY_SPIDX_PARQUET[strategy], index=False)
    print(f"  species index -> {STRATEGY_SPIDX_PARQUET[strategy].name} "
          f"({len(spidx_df)} species)")

    # --- Per-Nside richness NetCDF + atlas frequency parquet ---
    print(f"\n--- Cross-tabulating richness + atlas frequency ({strategy}) ---")
    if nc_path.exists():
        nc_path.unlink()
    freq_frames: list[pd.DataFrame] = []
    strat_report["per_nside"] = {}
    for nside in NSIDES:
        iberian_pix_arr = IBERIA_PIX[nside]
        parts = modern_counts[nside]
        if parts:
            stacked = np.vstack(parts) if len(parts) > 1 else parts[0]
            keys, cnts = stacked[:, :2], stacked[:, 2]
            uniq_keys, inv = np.unique(keys, axis=0, return_inverse=True)
            inv = np.asarray(inv).ravel()
            summed = np.zeros(len(uniq_keys), dtype=np.int64)
            np.add.at(summed, inv, cnts)
            cell_col, sid_col = uniq_keys[:, 0], uniq_keys[:, 1]
            in_iberia = np.isin(cell_col, iberian_pix_arr)
            cell_col, sid_col, summed = (cell_col[in_iberia],
                                         sid_col[in_iberia], summed[in_iberia])
        else:
            cell_col = np.empty(0, dtype=np.int64)
            sid_col = np.empty(0, dtype=np.int64)
            summed = np.empty(0, dtype=np.int64)
        modern_counts[nside] = []

        freq_frames.append(pd.DataFrame({
            "nside": np.full(len(cell_col), nside, dtype=np.int32),
            "cell": cell_col.astype(np.int64),
            "species_id": sid_col.astype(np.int64),
            "count": summed.astype(np.int64)}))

        if len(cell_col):
            uc, rc = np.unique(cell_col, return_counts=True)
            atlas_rich = pd.Series(rc, index=uc)
        else:
            atlas_rich = pd.Series(dtype=np.int64)

        hist = historical_cell_counts(species_hulls, nside, iberian_pix_arr)
        hist_rich = (hist.set_index("cell")["richness"] if len(hist)
                     else pd.Series(dtype=np.int64))

        df = pd.DataFrame({"cell": iberian_pix_arr}).set_index("cell")
        df["richness_atlas"] = atlas_rich.reindex(df.index, fill_value=0).astype(np.int32)
        df["richness_rangemap"] = hist_rich.reindex(df.index, fill_value=0).astype(np.int32)
        df["lon"] = IBERIA_LON[nside]
        df["lat"] = IBERIA_LAT[nside]

        print(f"  nside={nside:>4} n_cells={len(df):>6,} "
              f"mean atlas={df['richness_atlas'].mean():5.2f} "
              f"rangemap={df['richness_rangemap'].mean():5.2f} "
              f"freq-rows={len(cell_col):>7,}")
        strat_report["per_nside"][nside] = {
            "n_cells": int(len(df)),
            "mean_richness_atlas": round(float(df["richness_atlas"].mean()), 3),
            "mean_richness_rangemap": round(float(df["richness_rangemap"].mean()), 3),
            "n_freq_rows": int(len(cell_col))}

        ds = xr.Dataset(
            data_vars={
                "richness_atlas": (("cell",), df["richness_atlas"].values,
                    {"long_name": "Per-cell species richness from modern "
                                  "(year>=2000) GBIF occurrences (atlas-equivalent)",
                     "units": "n_species", "strategy": strategy,
                     "synthetic": str(SYNTHETIC[strategy])}),
                "richness_rangemap": (("cell",), df["richness_rangemap"].values,
                    {"long_name": "Per-cell species richness from historical "
                                  "(year<2000) EOO convex-hull coverage",
                     "units": "n_species", "strategy": strategy,
                     "synthetic": str(SYNTHETIC[strategy])})},
            coords={
                "cell": ("cell", df.index.values.astype(np.int64),
                         {"long_name": f"HEALPix NESTED pixel index (nside={nside})"}),
                "lon": ("cell", df["lon"].values, {"units": "degrees_east"}),
                "lat": ("cell", df["lat"].values, {"units": "degrees_north"})},
            attrs={"nside": nside, "depth": DEPTHS[nside], "ellipsoid": ELLIPSOID,
                   "healpix_ordering": "NESTED", "strategy": strategy,
                   "synthetic": str(SYNTHETIC[strategy]), "year_split": YEAR_SPLIT})
        ds.to_netcdf(nc_path, mode="a" if nc_path.exists() else "w",
                     group=f"nside_{nside}", engine="netcdf4",
                     encoding={"richness_atlas": {"zlib": True, "complevel": 4},
                               "richness_rangemap": {"zlib": True, "complevel": 4}})

    freq_df = pd.concat(freq_frames, ignore_index=True)
    freq_df.to_parquet(STRATEGY_FREQ_PARQUET[strategy], index=False)
    print(f"\n  saved {nc_path} ({nc_path.stat().st_size / 1e6:.2f} MB)")
    print(f"  saved {STRATEGY_FREQ_PARQUET[strategy].name} ({len(freq_df):,} rows)")
    strat_report["richness_nc"] = str(nc_path.relative_to(ROOT))
    strat_report["atlas_freq_parquet"] = str(STRATEGY_FREQ_PARQUET[strategy].relative_to(ROOT))
    report["per_strategy"][strategy] = strat_report


# %% [markdown]
# ## Persist per-strategy EOO polygons

# %%
eoo_df = pd.DataFrame(all_eoo_records)
eoo_df.to_parquet(EOO_PARQUET, index=False)
print(f"\nsaved {EOO_PARQUET} ({len(eoo_df)} species-rows)")


# %% [markdown]
# ## Sample CHELSA predictors to HEALPix cell centres
#
# The SDM covariate matrix is one row per Iberian cell, one column per bio*
# layer. We nearest-sample the CHELSA grid (`01`'s `chelsa_iberia.nc`) at each
# cell centre (lon/lat). One NetCDF group per Nside, var = bio* on `cell`. This
# is the predictor space MaxEnt fits its presence-vs-background contrast in.

# %%
def sample_predictors(chelsa: xr.Dataset, nside: int) -> pd.DataFrame:
    """Nearest-neighbour sample of every bio* layer to the Nside cell centres."""
    lon = xr.DataArray(IBERIA_LON[nside].astype(float), dims="cell")
    lat = xr.DataArray(IBERIA_LAT[nside].astype(float), dims="cell")
    sampled = chelsa.sel(lon=lon, lat=lat, method="nearest")
    out = pd.DataFrame({"cell": IBERIA_PIX[nside]})
    for v in chelsa.data_vars:
        out[v] = np.asarray(sampled[v].values, dtype=np.float32)
    return out


print(f"\n--- Sampling CHELSA predictors to cell centres ---")
chelsa_synthetic = (RAW_DIR / "USING_SYNTHETIC_DEMO_DATA_chelsa.txt").exists()
if not CHELSA_NC.exists():
    raise FileNotFoundError(
        f"Expected CHELSA stack at {CHELSA_NC} — re-run 01_data_download.py.")
chelsa = xr.open_dataset(CHELSA_NC)
bio_vars = list(chelsa.data_vars)
print(f"  CHELSA vars: {bio_vars} (synthetic={chelsa_synthetic})")

if PREDICTORS_NC.exists():
    PREDICTORS_NC.unlink()
report["predictors"] = {"bio_vars": bio_vars, "synthetic": chelsa_synthetic,
                        "per_nside": {}}
for nside in NSIDES:
    pred = sample_predictors(chelsa, nside)
    n_nan = int(pred[bio_vars].isna().any(axis=1).sum())
    ds = xr.Dataset(
        {v: (("cell",), pred[v].values) for v in bio_vars},
        coords={"cell": ("cell", pred["cell"].values.astype(np.int64)),
                "lon": ("cell", IBERIA_LON[nside]),
                "lat": ("cell", IBERIA_LAT[nside])},
        attrs={"nside": nside, "depth": DEPTHS[nside], "ellipsoid": ELLIPSOID,
               "healpix_ordering": "NESTED", "source": "CHELSA v2.1",
               "synthetic": str(chelsa_synthetic)})
    ds.to_netcdf(PREDICTORS_NC, mode="a" if PREDICTORS_NC.exists() else "w",
                 group=f"nside_{nside}", engine="netcdf4",
                 encoding={v: {"zlib": True, "complevel": 4} for v in bio_vars})
    print(f"  nside={nside:>4} {len(pred):>6,} cells sampled, {n_nan} with NaN predictor")
    report["predictors"]["per_nside"][nside] = {"n_cells": int(len(pred)),
                                                "n_cells_nan": n_nan}
chelsa.close()
print(f"  saved {PREDICTORS_NC} ({PREDICTORS_NC.stat().st_size / 1e6:.2f} MB)")


# %% [markdown]
# ## Clean report

# %%
with open(CLEAN_REPORT, "w") as f:
    json.dump(report, f, indent=2, default=str)
print(f"\n--- Clean report -> {CLEAN_REPORT}")
print(json.dumps(report, indent=2, default=str))

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
# # 01 — Data download (Iberian birds + CHELSA v2 + EU Article 12)
#
# Fetches every input the target-group-background SDM pipeline needs. This is
# the **third** chain in the family; it reuses the sibling's GBIF download DOIs
# verbatim and adds **CHELSA v2 bioclimatic predictors** (the SDM covariates —
# the analogue of Phillips et al. 2009's 11–13 environmental layers).
#
# Self-contained: a fresh clone runs this end-to-end without manual prep.
#
# ## Datasets
#
# 1. **GBIF Strategy A — `museum`** (PRESERVED_SPECIMEN + MACHINE_OBSERVATION).
#    DOI `10.15468/dl.r8pcat`, key `0008222-260519110011954` — reused from the
#    sibling chain (no new mint).
# 2. **GBIF Strategy B — `allbor`** (+ HUMAN_OBSERVATION). DOI
#    `10.15468/dl.e9xv7p`, key `0008251-260519110011954` — reused.
# 3. **CHELSA v2.1 bioclimatic layers** (~1 km, EPSG:4326 GeoTIFF). Downloaded
#    by **windowed `/vsicurl/` read** over the Iberia bbox only (each global
#    layer is ~115 MB compressed; the Iberia window is a few MB). Cached as a
#    single NetCDF stack `data/external/chelsa/chelsa_iberia.nc`.
# 4. **EU Birds Directive Article 12 distribution polygons** (EEA 2013–2018,
#    EPSG:3035, CC-BY 4.0) — the expert-rangemap gold standard.
#
# Within each GBIF strategy, `02_data_clean.py` splits records by year
# (`>= 2000` modern/atlas) and pools all species into the target-group
# background. One DOI per strategy serves both purposes.
#
# **Credentials.** GBIF zips are fetched from the public download endpoint by
# pre-minted key — no credentials at execution time. Set `GBIF_USER/PWD/EMAIL`
# only to mint a fresh download (fallback). CHELSA + Article 12 are public.
#
# **Synthetic-demo fallback.** When a real dataset is unavailable (offline / no
# key) a deterministic synthetic stand-in is written and a
# `data/raw/USING_SYNTHETIC_DEMO_DATA_*.txt` flag dropped, so the whole pipeline
# (download → clean → analysis → figures) runs on a fresh checkout. Set
# `CHELSA_VARS` (comma-separated bio numbers) or `CHELSA_FORCE_SYNTHETIC=1` to
# control the CHELSA step; `GBIF_FORCE_SYNTHETIC=1` for the GBIF step.

# %%
import json
import os
import shutil
import time
import zipfile
from datetime import date
from pathlib import Path

import requests

# %% [markdown]
# ## Paths

# %%
ROOT = Path("..").resolve()
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
GBIF_DIR = DATA_DIR / "gbif"
EXTERNAL_DIR = DATA_DIR / "external"
ART12_DIR = EXTERNAL_DIR / "art12"
CHELSA_DIR = EXTERNAL_DIR / "chelsa"

for d in (RAW_DIR, GBIF_DIR, ART12_DIR, CHELSA_DIR):
    d.mkdir(parents=True, exist_ok=True)

print(f"ROOT      = {ROOT}")
print(f"GBIF_DIR  = {GBIF_DIR}")
print(f"CHELSA_DIR= {CHELSA_DIR}")
print(f"ART12_DIR = {ART12_DIR}")

SOURCES: list[dict] = []
MIN_ZIP_BYTES = 1_000

# Iberia bounding box (shared with 02_data_clean.py).
IBERIA_LON_MIN, IBERIA_LAT_MIN = -10.0, 35.0
IBERIA_LON_MAX, IBERIA_LAT_MAX = 4.0, 44.0


# %% [markdown]
# ## GBIF Strategy A — `museum` (DOI 10.15468/dl.r8pcat)

# %%
GBIF_MUSEUM_DL_KEY = os.environ.get("GBIF_MUSEUM_DL_KEY", "0008222-260519110011954")
GBIF_MUSEUM_DL_DOI = os.environ.get("GBIF_MUSEUM_DL_DOI", "10.15468/dl.r8pcat")
GBIF_MUSEUM_PREDICATES = {
    "taxonKey": 212,
    "taxonKey_resolution": "Aves (class, ACCEPTED)",
    "country": ["ES", "PT", "AD", "GI"],
    "hasCoordinate": True,
    "hasGeospatialIssue": False,
    "basisOfRecord": ["PRESERVED_SPECIMEN", "MACHINE_OBSERVATION"],
}
GBIF_MUSEUM_ZIP = GBIF_DIR / "birds_iberia_museum.zip"
GBIF_MUSEUM_DOI_PATH = GBIF_DIR / "museum_download_doi.txt"
GBIF_MUSEUM_KEY_PATH = GBIF_DIR / "museum_download_key.txt"
GBIF_MUSEUM_META = GBIF_DIR / "birds_iberia_museum_metadata.json"

# %% [markdown]
# ## GBIF Strategy B — `allbor` (DOI 10.15468/dl.e9xv7p)

# %%
GBIF_ALLBOR_DL_KEY = os.environ.get("GBIF_ALLBOR_DL_KEY", "0008251-260519110011954")
GBIF_ALLBOR_DL_DOI = os.environ.get("GBIF_ALLBOR_DL_DOI", "10.15468/dl.e9xv7p")
GBIF_ALLBOR_PREDICATES = {
    "taxonKey": 212,
    "taxonKey_resolution": "Aves (class, ACCEPTED)",
    "country": ["ES", "PT", "AD", "GI"],
    "hasCoordinate": True,
    "hasGeospatialIssue": False,
    "basisOfRecord": [
        "HUMAN_OBSERVATION", "PRESERVED_SPECIMEN", "MACHINE_OBSERVATION"
    ],
}
GBIF_ALLBOR_ZIP = GBIF_DIR / "birds_iberia_allbor.zip"
GBIF_ALLBOR_DOI_PATH = GBIF_DIR / "allbor_download_doi.txt"
GBIF_ALLBOR_KEY_PATH = GBIF_DIR / "allbor_download_key.txt"
GBIF_ALLBOR_META = GBIF_DIR / "birds_iberia_allbor_metadata.json"


# %% [markdown]
# ## GBIF download helpers (reused from the sibling chain)

# %%
def fetch_gbif_by_key(key: str, zip_path: Path, doi: str, doi_path: Path,
                      key_path: Path, meta_path: Path,
                      predicates: dict) -> dict:
    """Fetch a pre-minted GBIF download zip by URL. No credentials needed."""
    if (zip_path.exists() and zip_path.stat().st_size > MIN_ZIP_BYTES
            and doi_path.exists() and key_path.exists()):
        print(f"  [cached]  key = {key_path.read_text().strip()}, "
              f"doi = {doi_path.read_text().strip()}")
        return {"key": key_path.read_text().strip(),
                "doi": doi_path.read_text().strip(), "zip": str(zip_path)}

    url = f"https://api.gbif.org/v1/occurrence/download/request/{key}.zip"
    print(f"  fetching {url}")
    try:
        r = requests.get(url, stream=True, timeout=600, allow_redirects=True)
        r.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    except requests.RequestException as e:
        print(f"  [fail  ]  GBIF fetch failed: {e}")
        if zip_path.exists():
            zip_path.unlink()
        return {"key": None, "doi": None, "zip": None, "skipped": True,
                "reason": f"GBIF fetch of key {key} failed: {e}"}
    print(f"  saved {zip_path} ({zip_path.stat().st_size:,} bytes)")

    doi_path.write_text(doi + "\n")
    key_path.write_text(key + "\n")
    meta_path.write_text(json.dumps({
        "download_key": key, "doi": doi, "doi_url": f"https://doi.org/{doi}",
        "source_url": url, "predicates": predicates}, indent=2))
    return {"key": key, "doi": doi, "zip": str(zip_path)}


def mint_gbif_download(predicates: dict, name: str) -> dict | None:
    """Mint a fresh GBIF download via the API. None if credentials absent / fails."""
    user = os.environ.get("GBIF_USER")
    pwd = os.environ.get("GBIF_PWD")
    email = os.environ.get("GBIF_EMAIL")
    if not (user and pwd and email):
        print(f"  [skip  ]  GBIF_USER/PWD/EMAIL not set — cannot mint '{name}'")
        return None
    json_predicate = {
        "type": "and",
        "predicates": [
            {"type": "equals", "key": "TAXON_KEY",
             "value": str(predicates["taxonKey"])},
            {"type": "equals", "key": "HAS_COORDINATE", "value": "true"},
            {"type": "equals", "key": "HAS_GEOSPATIAL_ISSUE", "value": "false"},
            {"type": "in", "key": "COUNTRY", "values": predicates["country"]},
            {"type": "in", "key": "BASIS_OF_RECORD",
             "values": predicates["basisOfRecord"]},
        ],
    }
    print(f"  [mint  ]  requesting GBIF download for '{name}'")
    api_url = "https://api.gbif.org/v1/occurrence/download/request"
    body = {"creator": user, "notificationAddresses": [email],
            "sendNotification": False, "format": "SIMPLE_CSV",
            "predicate": json_predicate}
    resp = requests.post(api_url, json=body, auth=(user, pwd), timeout=120)
    if not resp.ok:
        print(f"  [fail  ]  mint POST {resp.status_code}: {resp.text[:200]}")
        return None
    key = resp.text.strip()
    print(f"  [mint  ]  download key = {key} — polling ...")
    status_url = f"https://api.gbif.org/v1/occurrence/download/{key}"
    for attempt in range(60):
        s = requests.get(status_url, timeout=30).json()
        status = s.get("status")
        print(f"            attempt {attempt + 1}: status = {status}")
        if status == "SUCCEEDED":
            return {"key": key, "doi": s.get("doi", "")}
        if status in ("FAILED", "CANCELLED", "FILE_ERASED"):
            return None
        time.sleep(30)
    return None


def get_or_mint(name: str, hardcoded_key: str, hardcoded_doi: str,
                zip_path: Path, doi_path: Path, key_path: Path,
                meta_path: Path, predicates: dict) -> dict:
    """Fetch by pre-minted key; else mint; else skip (-> synthetic fallback)."""
    if os.environ.get("GBIF_FORCE_SYNTHETIC"):
        return {"key": None, "doi": None, "zip": None, "skipped": True,
                "reason": "GBIF_FORCE_SYNTHETIC set — using synthetic demo data."}
    if not hardcoded_key.startswith("TODO_"):
        return fetch_gbif_by_key(hardcoded_key, zip_path, hardcoded_doi,
                                 doi_path, key_path, meta_path, predicates)
    minted = mint_gbif_download(predicates, name)
    if minted:
        return fetch_gbif_by_key(minted["key"], zip_path, minted["doi"],
                                 doi_path, key_path, meta_path, predicates)
    return {"key": None, "doi": None, "zip": None, "skipped": True,
            "reason": (f"No pre-minted key for '{name}' and "
                       f"GBIF_USER/PWD/EMAIL not set.")}


# %% [markdown]
# ## Execute the two GBIF strategy downloads

# %%
print("\n--- GBIF Strategy A: museum + sensors ---")
museum_result = get_or_mint(
    name="museum", hardcoded_key=GBIF_MUSEUM_DL_KEY,
    hardcoded_doi=GBIF_MUSEUM_DL_DOI, zip_path=GBIF_MUSEUM_ZIP,
    doi_path=GBIF_MUSEUM_DOI_PATH, key_path=GBIF_MUSEUM_KEY_PATH,
    meta_path=GBIF_MUSEUM_META, predicates=GBIF_MUSEUM_PREDICATES)
SOURCES.append({
    "strategy": "museum",
    "name": "GBIF Iberian birds — PRESERVED_SPECIMEN + MACHINE_OBSERVATION",
    "role": "Strategy A — museum+sensor provenance (reused from sibling, no new mint)",
    "doi": museum_result.get("doi"),
    "url": (f"https://doi.org/{museum_result['doi']}"
            if museum_result.get("doi") else None),
    "license": "CC-BY-NC-4.0 (per individual GBIF datasets)",
    "accessed_on": date.today().isoformat(),
    "download_key": museum_result.get("key"),
    "predicates": GBIF_MUSEUM_PREDICATES,
    "local_path": museum_result.get("zip"),
    "skipped": museum_result.get("skipped", False),
    "skip_reason": museum_result.get("reason")})

# %%
print("\n--- GBIF Strategy B: all observations (incl. citizen-science) ---")
allbor_result = get_or_mint(
    name="allbor", hardcoded_key=GBIF_ALLBOR_DL_KEY,
    hardcoded_doi=GBIF_ALLBOR_DL_DOI, zip_path=GBIF_ALLBOR_ZIP,
    doi_path=GBIF_ALLBOR_DOI_PATH, key_path=GBIF_ALLBOR_KEY_PATH,
    meta_path=GBIF_ALLBOR_META, predicates=GBIF_ALLBOR_PREDICATES)
SOURCES.append({
    "strategy": "allbor",
    "name": "GBIF Iberian birds — HUMAN + PRESERVED_SPECIMEN + MACHINE_OBSERVATION",
    "role": "Strategy B — all observations incl. citizen-science (reused, no new mint)",
    "doi": allbor_result.get("doi"),
    "url": (f"https://doi.org/{allbor_result['doi']}"
            if allbor_result.get("doi") else None),
    "license": "CC-BY-NC-4.0 (per individual GBIF datasets)",
    "accessed_on": date.today().isoformat(),
    "download_key": allbor_result.get("key"),
    "predicates": GBIF_ALLBOR_PREDICATES,
    "local_path": allbor_result.get("zip"),
    "skipped": allbor_result.get("skipped", False),
    "skip_reason": allbor_result.get("reason")})


# %% [markdown]
# ## Per-strategy GBIF synthetic fallback
#
# Emits a deterministic Iberian bird dataset (per-record rows) for any strategy
# whose download was skipped, so `02_data_clean.py` can build per-cell
# species-frequency tables, per-species occurrence sets, and a target-group
# background. Same generator as the sibling so the substrate is identical.

# %%
def make_synthetic_demo(zip_path: Path, doi_path: Path, key_path: Path,
                        meta_path: Path, strategy: str,
                        flag_path: Path) -> dict:
    """Generate deterministic Iberian bird demo data for one strategy."""
    import numpy as np

    seed = {"museum": 20260522, "allbor": 20260523}.get(strategy, 20260524)
    rng = np.random.default_rng(seed=seed)
    SPECIES_N = 80
    lon0, lon1, lat0, lat1 = -10.0, 4.0, 35.0, 44.0
    centres_lon = rng.uniform(lon0 + 1, lon1 - 1, size=SPECIES_N)
    centres_lat = rng.uniform(lat0 + 1, lat1 - 1, size=SPECIES_N)
    range_radii = rng.uniform(1.0, 4.0, size=SPECIES_N)
    species_names = [f"Synthavis demoensis_{i:03d}" for i in range(SPECIES_N)]
    hotspot_centres = np.array([[-3.5, 37.0], [0.0, 42.5], [-6.5, 39.5]])

    records: list[dict] = []
    for sp_idx, name in enumerate(species_names):
        n_pts = rng.integers(15, 40)
        lons = rng.normal(centres_lon[sp_idx], range_radii[sp_idx], n_pts)
        lats = rng.normal(centres_lat[sp_idx], range_radii[sp_idx] * 0.6, n_pts)
        years = rng.integers(1950, 2000, n_pts)
        keep = (lons >= lon0) & (lons <= lon1) & (lats >= lat0) & (lats <= lat1)
        for j in np.where(keep)[0]:
            records.append({"species": name, "lat": float(lats[j]),
                            "lon": float(lons[j]), "year": int(years[j]),
                            "bor": "PRESERVED_SPECIMEN"})
    effort_boost = 3 if strategy == "allbor" else 1
    for sp_idx, name in enumerate(species_names):
        n_pts = rng.integers(40, 120)
        lons = rng.normal(centres_lon[sp_idx], range_radii[sp_idx] * 0.8, n_pts)
        lats = rng.normal(centres_lat[sp_idx], range_radii[sp_idx] * 0.5, n_pts)
        years = rng.integers(2000, 2025, n_pts)
        if sp_idx % 2 == 0:
            hc = hotspot_centres[sp_idx % 3]
            extra_n = rng.integers(20, 60) * effort_boost
            lons = np.concatenate([lons, rng.normal(hc[0], 0.3, extra_n)])
            lats = np.concatenate([lats, rng.normal(hc[1], 0.3, extra_n)])
            years = np.concatenate([years, rng.integers(2010, 2025, extra_n)])
        keep = (lons >= lon0) & (lons <= lon1) & (lats >= lat0) & (lats <= lat1)
        for j in np.where(keep)[0]:
            records.append({"species": name, "lat": float(lats[j]),
                            "lon": float(lons[j]), "year": int(years[j]),
                            "bor": "MACHINE_OBSERVATION"})

    cols = ["gbifID", "species", "decimalLatitude", "decimalLongitude",
            "year", "basisOfRecord", "countryCode"]
    lines = ["\t".join(cols)]
    for i, rec in enumerate(records):
        lines.append("\t".join([
            str(i), rec["species"], f"{rec['lat']:.5f}", f"{rec['lon']:.5f}",
            str(rec["year"]), rec["bor"], "ES"]))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("occurrence.csv", "\n".join(lines) + "\n")
    doi_path.write_text(f"SYNTHETIC_DEMO_DATA_NO_DOI_{strategy}\n")
    key_path.write_text(f"SYNTHETIC_DEMO_{strategy}\n")
    meta_path.write_text(json.dumps({
        "synthetic": True, "strategy": strategy, "seed": seed,
        "n_records": len(records), "n_species": SPECIES_N}, indent=2))
    flag_path.write_text(
        f"Strategy '{strategy}' is SYNTHETIC DEMO DATA.\n"
        f"Provide the real GBIF download for this strategy and re-run.\n")
    print(f"  [demo  ]  wrote synthetic strategy='{strategy}': "
          f"{len(records):,} records across {SPECIES_N} species")
    return {"n_records": len(records), "n_species": SPECIES_N, "seed": seed}


# %%
SYNTHETIC_FLAG_MUSEUM = RAW_DIR / "USING_SYNTHETIC_DEMO_DATA_museum.txt"
SYNTHETIC_FLAG_ALLBOR = RAW_DIR / "USING_SYNTHETIC_DEMO_DATA_allbor.txt"

if museum_result.get("skipped"):
    print("\n--- Synthetic demo fallback for Strategy A (museum) ---")
    info = make_synthetic_demo(GBIF_MUSEUM_ZIP, GBIF_MUSEUM_DOI_PATH,
                               GBIF_MUSEUM_KEY_PATH, GBIF_MUSEUM_META,
                               "museum", SYNTHETIC_FLAG_MUSEUM)
    SOURCES.append({"strategy": "museum",
                    "name": "Synthetic Iberian bird demo data (museum)",
                    "role": "demo fallback", "doi": None, "url": None,
                    "license": f"n/a (generated, seed {info['seed']})",
                    "accessed_on": date.today().isoformat(), "synthetic": True})
elif SYNTHETIC_FLAG_MUSEUM.exists():
    SYNTHETIC_FLAG_MUSEUM.unlink()

if allbor_result.get("skipped"):
    print("\n--- Synthetic demo fallback for Strategy B (allbor) ---")
    info = make_synthetic_demo(GBIF_ALLBOR_ZIP, GBIF_ALLBOR_DOI_PATH,
                               GBIF_ALLBOR_KEY_PATH, GBIF_ALLBOR_META,
                               "allbor", SYNTHETIC_FLAG_ALLBOR)
    SOURCES.append({"strategy": "allbor",
                    "name": "Synthetic Iberian bird demo data (allbor)",
                    "role": "demo fallback", "doi": None, "url": None,
                    "license": f"n/a (generated, seed {info['seed']})",
                    "accessed_on": date.today().isoformat(), "synthetic": True})
elif SYNTHETIC_FLAG_ALLBOR.exists():
    SYNTHETIC_FLAG_ALLBOR.unlink()


# %% [markdown]
# ## CHELSA v2.1 bioclimatic predictors (SDM covariates)
#
# CHELSA v2.1 (Karger et al. 2017) climatologies 1981–2010, ~1 km, global
# EPSG:4326 GeoTIFFs on the EnviDicloud S3 mirror. We never download the global
# layer: GDAL's `/vsicurl/` driver streams only the byte ranges covering the
# Iberia window. The windowed layers are stacked into one NetCDF
# `chelsa_iberia.nc` (xarray, CF-friendly — DOMAIN.md: never `.npz`).
#
# Default predictor set: a compact bioclim subset (analogue of Phillips' 11–13
# layers) — bio1 (mean annual T), bio4 (T seasonality), bio5 (max T warmest),
# bio6 (min T coldest), bio12 (annual precip), bio15 (precip seasonality).
# Override with env var `CHELSA_VARS="1,12"` for a lighter run / smoke test.

# %%
CHELSA_BASE = ("https://os.zhdk.cloud.switch.ch/chelsav2/GLOBAL/"
               "climatologies/1981-2010/bio")
CHELSA_URL = (CHELSA_BASE + "/CHELSA_bio{n}_1981-2010_V.2.1.tif")
CHELSA_DEFAULT_VARS = [1, 4, 5, 6, 12, 15]
CHELSA_VARS = [int(v) for v in os.environ.get(
    "CHELSA_VARS", ",".join(str(v) for v in CHELSA_DEFAULT_VARS)).split(",") if v]
CHELSA_NC = CHELSA_DIR / "chelsa_iberia.nc"
CHELSA_FLAG = RAW_DIR / "USING_SYNTHETIC_DEMO_DATA_chelsa.txt"


def fetch_chelsa_window(bio_vars: list[int]) -> dict:
    """Windowed /vsicurl read of CHELSA bio layers over the Iberia bbox -> NetCDF."""
    import numpy as np
    import rasterio
    import xarray as xr
    from rasterio.windows import from_bounds

    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")
    arrays, lons, lats = {}, None, None
    for n in bio_vars:
        url = "/vsicurl/" + CHELSA_URL.format(n=n)
        print(f"  bio{n}: windowed read {url}")
        with rasterio.open(url) as src:
            win = from_bounds(IBERIA_LON_MIN, IBERIA_LAT_MIN,
                              IBERIA_LON_MAX, IBERIA_LAT_MAX, src.transform)
            arr = src.read(1, window=win).astype("float32")
            wt = src.window_transform(win)
            h, w = arr.shape
            if lons is None:
                lons = wt.c + (np.arange(w) + 0.5) * wt.a
                lats = wt.f + (np.arange(h) + 0.5) * wt.e  # wt.e negative
            nodata = src.nodata
        if nodata is not None:
            arr = np.where(arr == nodata, np.nan, arr)
        arrays[f"bio{n}"] = (("lat", "lon"), arr)
        print(f"         shape={arr.shape}  range=[{np.nanmin(arr):.1f}, "
              f"{np.nanmax(arr):.1f}]")
    ds = xr.Dataset(
        arrays,
        coords={"lon": ("lon", lons.astype("float32")),
                "lat": ("lat", lats.astype("float32"))},
        attrs={"source": "CHELSA v2.1 (1981-2010)", "crs": "EPSG:4326",
               "bio_vars": ",".join(str(v) for v in bio_vars)})
    enc = {v: {"zlib": True, "complevel": 4} for v in arrays}
    if CHELSA_NC.exists():
        CHELSA_NC.unlink()
    ds.to_netcdf(CHELSA_NC, engine="netcdf4", encoding=enc)
    return {"n_vars": len(bio_vars), "shape": list(arr.shape)}


def make_synthetic_chelsa(bio_vars: list[int]) -> dict:
    """Deterministic smooth bioclim-like fields over the Iberia bbox -> NetCDF."""
    import numpy as np
    import xarray as xr

    rng = np.random.default_rng(20260530)
    nlat, nlon = 180, 280  # ~1/20 deg
    lons = np.linspace(IBERIA_LON_MIN, IBERIA_LON_MAX, nlon, dtype="float32")
    lats = np.linspace(IBERIA_LAT_MAX, IBERIA_LAT_MIN, nlat, dtype="float32")
    LON, LAT = np.meshgrid(lons, lats)
    arrays = {}
    for n in bio_vars:
        # Smooth latitudinal + longitudinal gradient + a couple of bumps, so
        # MaxEnt has structured covariates to fit against.
        base = (np.cos(np.radians(LAT)) * 100 + (LON + 10) * 5
                + 30 * np.exp(-(((LON + 3.5) ** 2 + (LAT - 40) ** 2) / 4))
                + rng.normal(0, 3, LON.shape))
        arrays[f"bio{n}"] = (("lat", "lon"), (base * (n + 1)).astype("float32"))
    ds = xr.Dataset(
        arrays, coords={"lon": ("lon", lons), "lat": ("lat", lats)},
        attrs={"source": "SYNTHETIC bioclim demo", "crs": "EPSG:4326",
               "bio_vars": ",".join(str(v) for v in bio_vars)})
    if CHELSA_NC.exists():
        CHELSA_NC.unlink()
    ds.to_netcdf(CHELSA_NC, engine="netcdf4")
    return {"n_vars": len(bio_vars), "shape": [nlat, nlon]}


print("\n--- CHELSA v2.1 bioclimatic predictors ---")
chelsa_synthetic = False
if CHELSA_NC.exists() and CHELSA_NC.stat().st_size > MIN_ZIP_BYTES:
    print(f"  [cached]  {CHELSA_NC} ({CHELSA_NC.stat().st_size:,} bytes)")
    if CHELSA_FLAG.exists():
        CHELSA_FLAG.unlink()
elif os.environ.get("CHELSA_FORCE_SYNTHETIC"):
    print("  CHELSA_FORCE_SYNTHETIC set — writing synthetic predictors")
    chelsa_synthetic = True
else:
    try:
        ci = fetch_chelsa_window(CHELSA_VARS)
        print(f"  saved {CHELSA_NC} ({CHELSA_NC.stat().st_size:,} bytes), "
              f"{ci['n_vars']} vars, window {ci['shape']}")
        if CHELSA_FLAG.exists():
            CHELSA_FLAG.unlink()
    except Exception as e:  # noqa: BLE001
        print(f"  [fail  ]  CHELSA windowed download failed: {e} — using synthetic")
        chelsa_synthetic = True

if chelsa_synthetic:
    ci = make_synthetic_chelsa(CHELSA_VARS)
    CHELSA_FLAG.write_text(
        "CHELSA predictors are SYNTHETIC DEMO DATA.\n"
        "Re-run with network access (or unset CHELSA_FORCE_SYNTHETIC) to fetch "
        "the real CHELSA v2.1 layers.\n")
    print(f"  [demo  ]  synthetic CHELSA: {ci['n_vars']} vars, {ci['shape']}")

SOURCES.append({
    "name": "CHELSA v2.1 bioclimatic variables (1981-2010, ~1 km)",
    "role": "SDM environmental predictors (Phillips 2009 covariate analogue)",
    "doi": "10.1038/sdata.2017.122",
    "url": "https://chelsa-climate.org/",
    "license": "CC-BY-4.0 (CHELSA)",
    "accessed_on": date.today().isoformat(),
    "bio_vars": CHELSA_VARS,
    "local_path": str(CHELSA_NC.relative_to(ROOT)),
    "synthetic": chelsa_synthetic})


# %% [markdown]
# ## EU Article 12 expert-rangemap gold standard
#
# EU Birds Directive Article 12 distribution data (EEA, 2013–2018). Acquisition:
# use a local GPKG if present, else download the EEA datashare package (a zip
# wrapping an ESRI File Geodatabase) and convert the target layer to GeoPackage,
# else write a deterministic synthetic GPKG matching the real schema (so the
# pipeline still runs offline). The download URL defaults to the resolved EEA
# datashare link and is overridable via `ART12_DOWNLOAD_URL`.

# %%
ART12_GPKG = ART12_DIR / "ART12_3035_distribution_data_without_sensitive.gpkg"
ART12_LAYER = "EU_ART12_birds_distribution_2013_2018_without_sensitive_species"
ART12_FLAG = RAW_DIR / "USING_SYNTHETIC_DEMO_DATA_art12.txt"
ART12_LANDING = "https://sdi.eea.europa.eu/data/e2face16-f352-4aff-9e4f-0ad1306f89b5"
# EEA datashare pre-packaged download (resolved from ART12_LANDING). It delivers
# a zip containing an ESRI File Geodatabase (.gdb), which we convert to the
# expected GeoPackage below. Override via ART12_DOWNLOAD_URL if EEA moves it.
ART12_DEFAULT_URL = "https://sdi.eea.europa.eu/datashare/s/wcpT9ak6BnyY8kL/download"
ART12_DOWNLOAD_URL = os.environ.get("ART12_DOWNLOAD_URL", ART12_DEFAULT_URL)


def materialise_art12_from_archive(archive: Path, gpkg_path: Path,
                                   layer: str) -> None:
    """Turn a downloaded EEA archive into the expected GeoPackage `layer`.

    The EEA datashare delivers a zip wrapping an ESRI File Geodatabase (.gdb);
    convert its `layer` to GPKG so `03_analysis.py` reads it unchanged. A zip
    that already contains a .gpkg, or a bare .gpkg file, is handled too.
    """
    import geopandas as gpd

    if not zipfile.is_zipfile(archive):
        archive.rename(gpkg_path)  # already a bare GeoPackage
        return
    with zipfile.ZipFile(archive) as zf:
        gpkg_members = [n for n in zf.namelist() if n.lower().endswith(".gpkg")]
        if gpkg_members:
            with zf.open(gpkg_members[0]) as src, open(gpkg_path, "wb") as dst:
                dst.write(src.read())
            return
        extract_dir = gpkg_path.parent / "_art12_extract"
        shutil.rmtree(extract_dir, ignore_errors=True)
        zf.extractall(extract_dir)
    try:
        gdbs = list(extract_dir.rglob("*.gdb"))
        if not gdbs:
            raise RuntimeError("Article 12 archive has no .gpkg or .gdb")
        gdf = gpd.read_file(gdbs[0], layer=layer, engine="pyogrio")
        if gpkg_path.exists():
            gpkg_path.unlink()
        gdf.to_file(gpkg_path, layer=layer, driver="GPKG")
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def make_synthetic_art12(gpkg_path: Path, layer: str) -> dict:
    """Synthetic Article-12-like GPKG keyed to the synthetic GBIF species set."""
    import geopandas as gpd
    import numpy as np
    from shapely.geometry import box

    rng = np.random.default_rng(20260524)
    SPECIES_N = 80
    species_names = [f"Synthavis demoensis_{i:03d}" for i in range(SPECIES_N)]
    lon0, lon1, lat0, lat1 = -10.0, 4.0, 35.0, 44.0
    rows = []
    for name in species_names:
        n_cells = int(rng.integers(20, 120))
        clon, clat = rng.uniform(lon0 + 1, lon1 - 1), rng.uniform(lat0 + 1, lat1 - 1)
        rad = rng.uniform(1.0, 3.5)
        lons = np.clip(rng.normal(clon, rad, n_cells), lon0, lon1)
        lats = np.clip(rng.normal(clat, rad * 0.6, n_cells), lat0, lat1)
        for lo, la in zip(lons, lats):
            rows.append({"country": "ES", "speciesnameEU": name,
                         "lon": float(lo), "lat": float(la)})
    gdf_pts = gpd.GeoDataFrame(
        rows, geometry=gpd.points_from_xy([r["lon"] for r in rows],
                                          [r["lat"] for r in rows]),
        crs="EPSG:4326").to_crs("EPSG:3035")
    half = 5_000.0
    geoms = [box(p.x - half, p.y - half, p.x + half, p.y + half)
             for p in gdf_pts.geometry]
    gdf = gpd.GeoDataFrame(
        {"country": gdf_pts["country"].values,
         "speciesnameEU": gdf_pts["speciesnameEU"].values},
        geometry=geoms, crs="EPSG:3035")
    if gpkg_path.exists():
        gpkg_path.unlink()
    gdf.to_file(gpkg_path, layer=layer, driver="GPKG")
    return {"n_cells": len(gdf), "n_species": gdf["speciesnameEU"].nunique()}


print("\n--- EU Article 12 expert-rangemap gold standard ---")
art12_synthetic = False
if ART12_GPKG.exists() and ART12_GPKG.stat().st_size > MIN_ZIP_BYTES:
    print(f"  [cached]  {ART12_GPKG} ({ART12_GPKG.stat().st_size:,} bytes)")
    if ART12_FLAG.exists():
        ART12_FLAG.unlink()
elif ART12_DOWNLOAD_URL:
    print(f"  fetching {ART12_DOWNLOAD_URL}")
    try:
        r = requests.get(ART12_DOWNLOAD_URL, stream=True, timeout=900,
                         allow_redirects=True)
        r.raise_for_status()
        tmp = ART12_DIR / "art12_download.bin"
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
        materialise_art12_from_archive(tmp, ART12_GPKG, ART12_LAYER)
        if tmp.exists():
            tmp.unlink()
        # Confirm the real layer + the species column 03_analysis.py needs.
        import pyogrio
        cols = pyogrio.read_info(ART12_GPKG, layer=ART12_LAYER)["fields"]
        if "speciesnameEU" not in cols:
            raise RuntimeError(f"GPKG layer missing speciesnameEU (got {list(cols)})")
        print(f"  saved {ART12_GPKG} ({ART12_GPKG.stat().st_size:,} bytes)")
        if ART12_FLAG.exists():
            ART12_FLAG.unlink()
    except Exception as e:  # noqa: BLE001
        print(f"  [fail  ]  Article 12 download failed: {e} — using synthetic")
        art12_synthetic = True
else:
    print("  [skip  ]  Article 12 GPKG not present and ART12_DOWNLOAD_URL unset")
    art12_synthetic = True

if art12_synthetic:
    print("  [demo  ]  writing synthetic Article 12 layer")
    a12 = make_synthetic_art12(ART12_GPKG, ART12_LAYER)
    ART12_FLAG.write_text(
        "Article 12 layer is SYNTHETIC DEMO DATA.\n"
        f"Download the real EEA dataset from {ART12_LANDING} and place it at\n"
        f"{ART12_GPKG} (or set ART12_DOWNLOAD_URL), then re-run.\n")
    print(f"  [demo  ]  synthetic Art-12: {a12['n_cells']:,} cells, "
          f"{a12['n_species']} species")

SOURCES.append({
    "name": "EU Birds Directive Article 12 distribution polygons (EEA 2013-2018)",
    "role": "Expert-rangemap gold standard for SDM-hotspot comparison",
    "doi": None, "url": ART12_LANDING, "license": "CC-BY-4.0 (EEA)",
    "accessed_on": date.today().isoformat(),
    "local_path": str(ART12_GPKG.relative_to(ROOT)), "layer": ART12_LAYER,
    "crs": "EPSG:3035", "synthetic": art12_synthetic})


# %% [markdown]
# ## Source registry

# %%
SOURCES_JSON = RAW_DIR / "sources.json"
with open(SOURCES_JSON, "w") as f:
    json.dump({
        "sources": SOURCES,
        "strategies": {
            "museum": {"synthetic": museum_result.get("skipped", False),
                       "doi": museum_result.get("doi"),
                       "download_key": museum_result.get("key"),
                       "zip": (str(GBIF_MUSEUM_ZIP.relative_to(ROOT))
                               if GBIF_MUSEUM_ZIP.exists() else None)},
            "allbor": {"synthetic": allbor_result.get("skipped", False),
                       "doi": allbor_result.get("doi"),
                       "download_key": allbor_result.get("key"),
                       "zip": (str(GBIF_ALLBOR_ZIP.relative_to(ROOT))
                               if GBIF_ALLBOR_ZIP.exists() else None)}},
        "chelsa": {"synthetic": chelsa_synthetic, "bio_vars": CHELSA_VARS,
                   "nc": (str(CHELSA_NC.relative_to(ROOT))
                          if CHELSA_NC.exists() else None)},
        "art12": {"synthetic": art12_synthetic,
                  "gpkg": (str(ART12_GPKG.relative_to(ROOT))
                           if ART12_GPKG.exists() else None),
                  "layer": ART12_LAYER},
        "written_on": date.today().isoformat()}, f, indent=2)
print(f"\n--- Wrote source registry -> {SOURCES_JSON}")


# %% [markdown]
# ## Summary

# %%
print("\nArtefact inventory:")
artefacts = [
    ("Museum zip", GBIF_MUSEUM_ZIP), ("Museum synth flag", SYNTHETIC_FLAG_MUSEUM),
    ("Allbor zip", GBIF_ALLBOR_ZIP), ("Allbor synth flag", SYNTHETIC_FLAG_ALLBOR),
    ("CHELSA NetCDF", CHELSA_NC), ("CHELSA synth flag", CHELSA_FLAG),
    ("Article 12 GPKG", ART12_GPKG), ("Article 12 synth flag", ART12_FLAG),
    ("Source registry JSON", SOURCES_JSON)]
for name, p in artefacts:
    if p.exists():
        size = (p.stat().st_size if p.is_file()
                else sum(f.stat().st_size for f in p.rglob("*") if f.is_file()))
        print(f"  ok    {name:<22} {size:>12,} bytes  {p.relative_to(ROOT)}")
    else:
        print(f"  MISS  {name:<22} {'-':>12}        {p.relative_to(ROOT)}")

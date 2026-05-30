# Snakefile — orchestrates the target-group-background SDM replication pipeline.
#
# Four notebooks, four rules (each wraps a jupytext .py executed in place, so the
# notebook stays the source of truth and Snakemake just sequences them):
#
#   01_data_download -> data/gbif/birds_iberia_{museum,allbor}.zip
#                       + data/external/chelsa/chelsa_iberia.nc  (SDM covariates)
#                       + data/external/art12/ART12_...gpkg  (gold standard)
#                       + data/raw/sources.json
#   02_data_clean    -> data/clean/richness_{museum,allbor}.nc      (raw richness)
#                       + atlas_freq_{museum,allbor}.parquet         (occ + TGB)
#                       + species_index_{museum,allbor}.parquet
#                       + predictors_cells.nc                        (CHELSA -> cells)
#                       + species_eoo_polygons.parquet + clean_report.json
#   03_analysis      -> results/sdm_misidentification.parquet
#                       (raw vs target-group-SDM vs random-SDM, both strategies,
#                        full ladder, vs Article 12 + vs EOO rangemap)
#                       + results/headline.json (Nside 256 verdict inputs)
#   04_figures       -> figures/main_result.{png,pdf}
#
# Usage:
#   pixi run snakemake --cores 1            # run everything
#   pixi run snakemake --cores 1 -n         # dry run
#   pixi run snakemake --cores 1 clean      # 01 + 02
#   pixi run snakemake --cores 1 analysis   # 01 + 02 + 03
#
# Smoke test (cap the heavy SDM job): set env vars before running, e.g.
#   SDM_NSIDES=64,256 SDM_MAX_SPECIES=40 CHELSA_VARS=1,12 pixi run snakemake --cores 1

NOTEBOOKS = "notebooks"
DATA = "data"
RESULTS = "results"
FIGURES = "figures"


rule all:
    input:
        f"{FIGURES}/main_result.png",
        f"{RESULTS}/sdm_misidentification.parquet",
        f"{RESULTS}/headline.json",


# ---------- 01: Data download ----------
# Self-contained: two strategy GBIF zips (reusing the sibling DOIs, no new mint),
# CHELSA v2 bioclim predictors (windowed /vsicurl read over Iberia), and the EU
# Article 12 GPKG. Per-dataset synthetic fallback keeps a fresh checkout runnable.
rule download:
    output:
        f"{DATA}/raw/sources.json",
        f"{DATA}/gbif/birds_iberia_museum.zip",
        f"{DATA}/gbif/birds_iberia_allbor.zip",
        f"{DATA}/external/chelsa/chelsa_iberia.nc",
        f"{DATA}/external/art12/ART12_3035_distribution_data_without_sensitive.gpkg",
    log:
        f"{RESULTS}/logs/01_data_download.log",
    shell:
        "mkdir -p $(dirname {log}) && "
        "cd " + NOTEBOOKS + " && "
        "jupytext --to notebook 01_data_download.py && "
        "jupyter execute --inplace 01_data_download.ipynb 2>&1 | tee ../{log}"


# ---------- 02: Data clean ----------
# Bin both strategies onto HEALPix NESTED (Nside 16..512); year-split at 2000.
# Emits per-cell raw richness, the per-cell atlas species-frequency tables (the
# occurrence + target-group-background layer), and CHELSA predictors sampled to
# cell centres (the SDM covariate matrix).
rule clean:
    input:
        f"{DATA}/gbif/birds_iberia_museum.zip",
        f"{DATA}/gbif/birds_iberia_allbor.zip",
        f"{DATA}/external/chelsa/chelsa_iberia.nc",
    output:
        museum_nc = f"{DATA}/clean/richness_museum.nc",
        allbor_nc = f"{DATA}/clean/richness_allbor.nc",
        museum_freq = f"{DATA}/clean/atlas_freq_museum.parquet",
        allbor_freq = f"{DATA}/clean/atlas_freq_allbor.parquet",
        predictors = f"{DATA}/clean/predictors_cells.nc",
        report = f"{DATA}/clean/clean_report.json",
    log:
        f"{RESULTS}/logs/02_data_clean.log",
    shell:
        "mkdir -p $(dirname {log}) {DATA}/clean && "
        "cd " + NOTEBOOKS + " && "
        "jupytext --to notebook 02_data_clean.py && "
        "jupyter execute --inplace 02_data_clean.ipynb 2>&1 | tee ../{log}"


# ---------- 03: Analysis (target-group-background SDM) ----------
# Per (strategy, Nside): fit per-species MaxEnt (elapid) with target-group AND
# random background (>=20-occ species), sum suitability -> predicted richness,
# then top-5% hotspot misidentification vs Article 12 (+ EOO rangemap) for raw,
# target-group-SDM, and random-SDM surfaces.
rule analysis:
    input:
        museum_nc = f"{DATA}/clean/richness_museum.nc",
        allbor_nc = f"{DATA}/clean/richness_allbor.nc",
        museum_freq = f"{DATA}/clean/atlas_freq_museum.parquet",
        allbor_freq = f"{DATA}/clean/atlas_freq_allbor.parquet",
        predictors = f"{DATA}/clean/predictors_cells.nc",
        art12 = f"{DATA}/external/art12/ART12_3035_distribution_data_without_sensitive.gpkg",
    output:
        misid = f"{RESULTS}/sdm_misidentification.parquet",
        headline = f"{RESULTS}/headline.json",
    log:
        f"{RESULTS}/logs/03_analysis.log",
    shell:
        "mkdir -p $(dirname {log}) " + RESULTS + " && "
        "cd " + NOTEBOOKS + " && "
        "jupytext --to notebook 03_analysis.py && "
        "jupyter execute --inplace 03_analysis.ipynb 2>&1 | tee ../{log}"


# ---------- 04: Figures ----------
# main_result: misidentification for raw vs target-group-SDM vs random-SDM, at
# Nside 256 (bars) and across the ladder (lines), with the H&J reference band.
rule figures:
    input:
        misid = f"{RESULTS}/sdm_misidentification.parquet",
        headline = f"{RESULTS}/headline.json",
    output:
        main_png = f"{FIGURES}/main_result.png",
        main_pdf = f"{FIGURES}/main_result.pdf",
    log:
        f"{RESULTS}/logs/04_figures.log",
    shell:
        "mkdir -p $(dirname {log}) " + FIGURES + " && "
        "cd " + NOTEBOOKS + " && "
        "jupytext --to notebook 04_figures.py && "
        "jupyter execute --inplace 04_figures.ipynb 2>&1 | tee ../{log}"

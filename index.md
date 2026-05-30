# sdm-hotspot-spatial-effort

> **Sample selection bias and presence-only distribution models: implications for background and pseudo-absence data** — replication study.
>
> Reference paper: [10.1890/07-2153.1](https://doi.org/10.1890/07-2153.1)

This repository is a self-contained replication of the headline claim from the reference paper above. It produces:

- A reproducible computational pipeline (Snakefile + notebooks).
- A FORRT-tagged nanopublication chain on the [Science Live platform](https://platform.sciencelive4all.org), documenting the claim, the replication design, and the outcome with full provenance.
- A Zenodo-archived release (source + container image) with a citable DOI.

## Quick start

```bash
git clone https://github.com/annefou/sdm-hotspot-spatial-effort.git
cd sdm-hotspot-spatial-effort
pixi install
pixi run snakemake --cores 1
```

Or with Docker:

```bash
docker run --rm ghcr.io/annefou/sdm-hotspot-spatial-effort:latest
```

## Structure

- `paper/` — the source paper PDF (drop yours in there).
- `notebooks/` — jupytext `.py` notebooks that drive the pipeline.
- `data/` — downloaded by `notebooks/01_data_download.py`, never committed.
- `nanopubs/` — drafts of the FORRT chain field-by-field, plus the published-URI registry.
- `docs/` — operating manuals (FORRT form fields, chain decision tree, claim-type vocabulary).
- `figures/` — curated figures used in the Jupyter Book.

## Nanopublication chain

The published chain is listed in [`nanopubs/PUBLISHED.md`](nanopubs/PUBLISHED.md). Each step links to its viewer URL on the Science Live platform.

## Citation

If you use this work, please cite both:

- This software: [`CITATION.cff`](CITATION.cff) → DOI [{{ZENODO_DOI}}]({{ZENODO_DOI}}).
- The original paper: [10.1890/07-2153.1](https://doi.org/10.1890/07-2153.1).

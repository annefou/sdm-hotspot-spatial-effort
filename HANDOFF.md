# HANDOFF — sdm-hotspot-spatial-effort

> Brief for the Claude session that will build this replication. Read this first,
> then `nanopubs/imported/CHAIN_SUMMARY.md` (after the import step). This repo is
> the **third** chain in a family; it only makes sense in the context of the prior two.

## One-line goal

Test whether a **spatially-explicit effort correction** (presence-only point-process /
bias-layer SDMs that model *where people looked*) recovers GBIF biodiversity hotspots
against the EU Article 12 expert-rangemap gold standard — **after coverage-based
rarefaction failed** (the sibling study).

## The research question (PICO — scoping device, NOT a published chain step)

| | |
|---|---|
| **P** | HEALPix-NESTED (~25 km, Nside 256) grid cells over Iberia, characterised by Iberian breeding-bird occurrences from GBIF. |
| **I** | Spatially-explicit effort correction: presence-only point-process / bias-layer SDMs with sampling effort as a covariate, stacked to per-cell species richness. |
| **C** | Uncorrected raw GBIF richness **and** the coverage-rarefied richness from the sibling study; both benchmarked against the EU Article 12 expert-rangemap gold standard. |
| **O** | Agreement of the top-5% richness hotspots with the Article 12 hotspots (symmetric set non-overlap / misidentification %), at the Hurlbert & Jetz reference scale. |

Plain version: *Does modelling where people looked recover the real hotspots, where
rescaling sample completeness did not?*

> PICO here is a **briefing artefact only**. The chain is **paper-rooted** (see below),
> so step 01 is a Quote-with-comment, not a PICO nanopub. Delete `nanopubs/drafts/01_pico.md`
> and `01_pcc.md` once you confirm the paper-rooted shape.

## Where this sits in the family (prior work)

1. **`sdm-scale-replication`** (parent) — replicated Hurlbert & Jetz (2007) scale-dependence
   of range-map richness hotspots; found the hotspot gap is dominated by GBIF **observer-effort
   bias** (verified vs EU Article 12). Outcome: *PartiallySupported / qualifies*.
   Concept DOI `10.5281/zenodo.20363555`.
2. **`sdm-hotspot-effort-correction`** (sibling) — tested coverage-based rarefaction
   (Chao & Jost 2012) as the fix → **Contradicted**. The bias is a *spatial sampling-location*
   effect, not a per-cell *completeness* artefact, so completeness-standardisation can't remove
   it; it also structurally censors 26–38% of effort-poor cells. Concept DOI `10.5281/zenodo.20451519`.
3. **THIS repo** — tests the method class the sibling's diagnosis points to: model the
   spatial sampling process explicitly.

Prior published nanopub URIs (for citing / walking the graph):

- Parent Outcome: `https://w3id.org/sciencelive/np/RAzeZKbUCEMXZXDc-WzgHZ4K5mOMwotYhS2uCKDDmdcHI`
- Parent CiTO apex: `https://w3id.org/sciencelive/np/RALjFcvPtncy74ZL8QgSiEyRZv_-mOiZj4wvWuq8JK-2s`
- Sibling Outcome: `https://w3id.org/sciencelive/np/RAsPjEImfZaXsIri0ny4j_s_k_6wyOlC6tkocl6w2y7f4`
- **Sibling CiTO apex (← import seed): `https://w3id.org/sciencelive/np/RACYbb_IxZNnBcxI7uPqc-df2oRaMr4bqHJTOJe-BNmkc`**

## Locked design decisions

- **Chain shape:** paper-rooted (Quote-with-comment on a methods paper), mirroring the sibling.
- **Phase 1 entry:** B (`/import-from-nanopub`) **+** A (verbatim Quote from the methods paper).
  They compose — run the import first to get the prior constellation, then root the Quote.
- **Import seed URI:** the sibling CiTO apex `RACYbb…` (above). Walking from it pulls in both
  the sibling and (transitively) the parent → full `CHAIN_SUMMARY.md`.
- **CiTO topology (step 06):** `extends` the **sibling Outcome** (`RAsPjE…`) as primary +
  `usesMethodIn` → the methods paper. NOT `disputes` — relative to the sibling/parent this
  study *continues* the bias programme regardless of its own result. The own-result status
  lives in the Outcome's Validation field.
- **Comparator (pre-committed):** EU Article 12 expert rangemaps = gold standard. Source: the
  Lifewatch Metadata Catalogue (`metadatacatalogue.lifewatch.eu`), CC-BY 4.0 — preferred over
  BirdLife BOTW for EU bird range data.
- **Metric:** top-5% hotspot **misidentification** = symmetric set non-overlap vs Article 12.
- **Scale:** headline HEALPix-NESTED **Nside 256** (~25 km); report the full ladder 16–512.
- **Two basis-of-record strategies:** `museum` (museum-grade) and `allbor` (all observations),
  same split as the sibling, so results are directly comparable.
- **Pre-register before running:** comparator, metric, scale, hotspot threshold are fixed
  *now* (above) — don't let a positive result emerge from researcher degrees of freedom.

## Open decisions for THIS session (confirm during Phase 1–2)

1. **Rooting methods paper — pick one, then VERIFY DOI + verbatim Quote against the PDF**
   (a hallucinated quote is the one thing we never ship):
   - **Phillips et al. 2009**, *Ecol. Appl.* — sample selection bias in presence-only SDMs
     (target-group background). DOI `10.1890/07-2153.1`. **← recommended** (most directly about
     observer/sampling bias; cleanest parallel to "Chao & Jost is the coverage-correction paper").
   - Warton & Shepherd 2010, *Ann. Appl. Stat.* — Poisson point-process foundation.
     DOI `10.1214/10-AOAS331`.
   - Renner et al. 2015, *MEE* — practical point-process synthesis with effort. DOI `10.1111/2041-210X.12352`.
   - Isaac et al. 2020, *TREE* — data integration (fuse citizen + structured). DOI `10.1016/j.tree.2019.08.006`.
   (DOIs above are from memory — verify each before it enters a Cited-DOI field.)
2. **SDM / point-process implementation + library** — decides `pixi.toml` deps. Candidates:
   `elapid`/`maxnet` (MaxEnt-style), an inhomogeneous Poisson point-process fit, or
   integration via `PointedSDMs`/`inlabru` (R). Choose precisely before pinning the env.
3. **Effort proxy** — how to quantify sampling effort spatially: total record count per cell,
   distinct observers/checklists, or a target-group background built from all-bird records.
4. **Per-species vs aggregate** — principled route is per-species point-process SDMs predicted
   to occupancy/intensity, then **summed to per-cell richness**, then hotspot-ranked.
5. **GBIF inputs** — likely the *same* occurrences as the sibling (964 species / 61.7 M records
   for allbor; ~1.0 M / 452 species for museum). Reuse the sibling's GBIF download DOIs if the
   query is identical; otherwise mint **new** download DOIs (a DOI per query is mandatory — see DOMAIN).

## Possible outcomes (both publishable — stay honest)

- **It works** → you found the actual fix; Outcome `Validated`/`PartiallySupported`, CiTO still `extends`.
- **It fails too** → strong message: *occurrence data can't be rescued post-hoc — structured
  sampling has to be designed in*; Outcome `Contradicted` for the correction hypothesis,
  CiTO still `extends` the sibling (the bias programme is reinforced).
  Do not overclaim either way (DOMAIN § honest negative results).

## Domain reminders (this repo inherits the bio + EO flavour)

- **GBIF download DOI is mandatory** per query (`10.15468/dl.…`); cite in CITATION.cff + Study Methodology.
- **HEALPix is always NESTED**; use **`healpix-geo`** (geographic, WGS84-aware), not `healpy`.
- Intermediate arrays: **NetCDF / Zarr, never `.npz`**. Tables: CSV/Parquet. Figures: PNG + PDF.
- `pixi.toml` + committed `pixi.lock` are the single source of truth; CI uses them.
- Notebooks self-contained (download their own data); `plt.show()` after `savefig`; no `Agg`.

## Comms (later, Phase 5+)

- Science-first plain-language LinkedIn post (not vision-first), full-trail link → CiTO apex.
- A **separate, self-explanatory** social figure (not the Jupyter Book figure): no overlapping
  text, explicit before/after key, colour tied to labelled headings, explicit signed deltas.
  Spell out "percentage points".

---
*Drafted in the sdm-scale-replication session, 2026-05-30, with full context of the parent +
sibling chains. Author: Anne Fouilloux (ORCID 0000-0002-1784-2920).*

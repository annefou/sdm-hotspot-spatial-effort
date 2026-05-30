# Published nanopub chain — URI registry

This file is the canonical registry of published nanopub URIs for this replication. Update it as you publish each step.

## Release & archival artefacts (Phase 4)

| Artefact | Identifier | Notes |
|---|---|---|
| Source — concept DOI | [10.5281/zenodo.20465140](https://doi.org/10.5281/zenodo.20465140) | Resolves to the latest version. Cited in `CITATION.cff` / `codemeta.json`. |
| Source — version DOI (v0.1.0) | [10.5281/zenodo.20465141](https://doi.org/10.5281/zenodo.20465141) | This release's immutable snapshot. |
| GitHub release | [v0.1.0](https://github.com/annefou/sdm-hotspot-spatial-effort/releases/tag/v0.1.0) | |
| Docker image (GHCR) | `ghcr.io/annefou/sdm-hotspot-spatial-effort:0.1.0` (also `:latest`) | Built + pushed by `docker.yml` on release. Make the package public in repo → Packages if not already. |
| Docker image — Zenodo DOI | _not minted_ | Optional (FAIR4RS A2). Set the `ZENODO_TOKEN` repo secret and re-run `docker.yml` to archive the image with its own DOI. |

## Chain

| Step | Template | URI | Published |
|---|---|---|---|
| 01 | Quote-with-comment (or PICO / PCC) | _not yet published_ | |
| 02 | AIDA Sentence | _not yet published_ | |
| 03 | FORRT Claim | _not yet published_ | |
| 04 | FORRT Replication Study | _not yet published_ | |
| 05 | FORRT Replication Outcome | _not yet published_ | |
| 06 | CiTO Citation | _not yet published_ | |

## Optional layers

| Step | Template | URI | Published |
|---|---|---|---|
| 07 | Research Software (if applicable) | _not applicable / not yet published_ | |
| 08 | Research Synthesis (if applicable) | _not applicable / not yet published_ | |

## Format

URIs from Science Live are of the form `https://w3id.org/sciencelive/np/RA…`. URIs from Nanodash (used as a fallback when the Science Live UI hits a bug) are of the form `https://w3id.org/np/RA…`. Both are valid and citable.

If a URI is not in the Science Live namespace, view it via the Science Live viewer by wrapping the URI:

```
https://platform.sciencelive4all.org/np/?uri=<full-URI>
```

## Cross-references

- Drafts: `nanopubs/drafts/`
- Form structure: `docs/forrt-form-fields.md`
- Chain shape decision: `docs/chain-decision-tree.md`

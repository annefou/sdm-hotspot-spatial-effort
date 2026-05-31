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
| 01 | Quote-with-comment (or PICO / PCC) | https://w3id.org/sciencelive/np/RAa_SMf7gCi0BbpMSh0hng3o9bYxtuJPfHz-ypXlXK9KQ | |
| 02 | AIDA Sentence | https://w3id.org/sciencelive/np/RAKggxL7Un0PTf5L8-X0tiDDcyYTE1MySjpLX7DDsuPOY | |
| 03 | FORRT Claim | https://w3id.org/sciencelive/np/RAKrH1DpRI7L9d7D4EMyGDDJ9iSDOVWo4-zezUPqyVBxo | |
| 04 | FORRT Replication Study | https://w3id.org/sciencelive/np/RA6bPD5TPlWXC6jrgnIF-Yh5sbGnurByDMJGQOoQCVz6c | |
| 05 | FORRT Replication Outcome | https://w3id.org/sciencelive/np/RA4q2J-h_UpFpeLTeL_DS8p7j7EOBCes4L1G1eOBfJiDo | |
| 06 | CiTO Citation | https://w3id.org/sciencelive/np/RA7151bPt5TSSTxi-sWGmZhUOHcqaSzevzhhD4QxmfURI | |

> **Superseded (2026-05-31):** the first Outcome `RAtYdozkKU7DkMvSw1yDYWKWhp5y9KqWsdctWKaASZe1U` and CiTO `RANNiJM-CSL5Xj9CtrVbwF-9a6IAwj2Mi6jbK72ZpHzlw` had the Outcome's Repository field set to the *reproduction* repo's DOI (`10.5281/zenodo.20473156`) by mistake. Re-published above with the correct DOI (`10.5281/zenodo.20473377`, this repo's v0.2.0). Retract the two old URIs via the `nanopub-agent-utilities` `/nanopub` retract (CLI; needs the original signing key) — if the platform key isn't held locally, leave them un-retracted and this note stands as the record.

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

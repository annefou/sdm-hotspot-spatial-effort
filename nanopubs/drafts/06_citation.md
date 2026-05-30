# 06 — CiTO Citation

> Pre-flight checklist run against `docs/forrt-form-fields.md` § Citation with CiTO on 2026-05-30.
> Topology LOCKED in HANDOFF.md — this chain does NOT `dispute` Phillips (see note below).

**Description:** *"Declare citations between papers or other works, using Citation Typing Ontology"*
**Template status:** documented in `docs/forrt-form-fields.md` § Citation with CiTO.

## Documented field list (paste-verbatim per pre-flight checklist)

| Field label | Field type | Required |
|---|---|---|
| Identifier for the citing creative work | text input | yes |
| List citations | repeatable group | yes (≥1) |
| ↳ Citation Type | dropdown | (per entry) |
| ↳ DOI or other URL of the cited work | text input | (per entry) |

> Citation Type dropdown options available on the platform: `confirms`, `qualifies`,
> `disputes`, `extends`, `usesMethodIn`, `citesAsAuthority`, `obtainsBackgroundFrom`,
> `discusses`, `citesAsDataSource`, `containsAssertionFrom`, `includesQuotationFrom`,
> `reviews`, `critiques`, `credits`. NOT available: `replicates`.

## Topology note — NOT `disputes` (read before drafting)

The Outcome (step 05) is **Contradicted**, which by the default mapping table would be
`cito:disputes`. **We deliberately override that here.** The Contradicted verdict is about the
*hotspot-restoration extension*, not about Phillips' published claim. Phillips' actual claim —
that target-group background improves per-species AUC — is **reproduced and confirmed** in the
companion repo `sdm-phillips-reproduction` (Validated, CiTO `confirms`). Disputing Phillips here
would misrepresent the science. Per HANDOFF.md the apex CiTO is:

- **`extends`** the **sibling Outcome** (primary) — this study continues the sibling's
  effort-bias programme regardless of its own result.
- **`usesMethodIn`** → the Phillips methods paper — we reuse his correction mechanism.

## Field-by-field draft

### Identifier for the citing creative work (text input, required)

URI of the Outcome published in step 05 (the citing work). Pull from `nanopubs/PUBLISHED.md`.

```
<pending step 05 publication>
```

### List citations (repeatable group, required ≥1)

#### Citation 1 — extends the sibling Outcome (PRIMARY)

##### Citation Type (dropdown)

```
extends
```

##### DOI or other URL of the cited work (text input)

Sibling Replication Outcome (`sdm-hotspot-effort-correction`), from HANDOFF.md:

```
https://w3id.org/sciencelive/np/RAsPjEImfZaXsIri0ny4j_s_k_6wyOlC6tkocl6w2y7f4
```

#### Citation 2 — uses the method from the Phillips paper

##### Citation Type (dropdown)

```
usesMethodIn
```

##### DOI or other URL of the cited work (text input)

```
https://doi.org/10.1890/07-2153.1
```

#### Citation 3 — credits the companion method-validation reproduction (OPTIONAL)

> Rationale: the companion repo `sdm-phillips-reproduction` establishes that this study's
> MaxEnt + target-group-background implementation faithfully reproduces Phillips' AUC result on
> his own data, which is what licenses attributing the hotspot failure to the question rather
> than to a broken method. Citing it makes the method-validation link machine-traceable.
>
> Add this entry only if it expresses cleanly. The cleanest target is the companion repo's
> **published FORRT Outcome URI** (a nanopub) — paste it once known. If that URI is not yet
> published, cite the companion repo's Zenodo concept DOI or GitHub URL instead, OR omit this
> entry and note the link in the Outcome's prose (it is already described there). `credits` is
> the right type for a directly-reused method/notebook (the dropdown has no `replicates`);
> `usesMethodIn` would also be defensible but is already used for the Phillips paper above.

##### Citation Type (dropdown)

```
credits
```

##### DOI or other URL of the cited work (text input)

Prefer the companion repo's published FORRT Outcome nanopub URI; fall back to its Zenodo/GitHub.

```
<pending — sdm-phillips-reproduction Outcome nanopub URI; fallback https://github.com/annefou/sdm-phillips-reproduction>
```

> If neither a published companion Outcome URI nor a companion Zenodo DOI is available at
> publish time, **omit Citation 3** — the method-validation relationship is already documented
> in the Outcome's conclusion and evidence fields, so the chain stays correct without it. Do not
> ship a placeholder URL in the live form.

## Publication note

After publishing, paste the resulting URI into `nanopubs/PUBLISHED.md` step 06.

This completes the six-step FORRT chain. Optional next layers:

- **Research Software** (`drafts/07_research_software.md`) — only if the repo *produces* a reusable
  artefact; this is a one-off replication repo, so a Research Software nanopub is NOT warranted here
  (the reusable upstream tool is `elapid`, not this repo). See `docs/forrt-form-fields.md` § Research Software.
- **Research Synthesis** (`drafts/08_synthesis.md`) — a synthesis across the parent + sibling + this
  chain (the shared "GBIF effort bias in hotspot identity cannot be fixed post-hoc" property) is a
  natural candidate, but is a separate decision; not drafted here.

# Sprint 1 delivery: Kelyan

| | |
| --- | --- |
| Team | 2, Diagnosis |
| Role | Person B: plant health sheets, reference questions and evaluation, diagnosis tool |
| Date | 25 November 2026 |
| Scope | The 18 disease and pest classes of the CCMT dataset (cashew, cassava, maize, tomato); the 4 healthy classes need no sheet |
| Pull requests | Merged: #16 diagnosis MCP tool, #17 plant health sheets, #18 reference questions, #19 Open-Meteo terms of use (https://github.com/Primael75/PFE/pulls?q=is%3Apr+is%3Amerged). Opened after the J1 review: `docs/plant-health-missing-sheets`, `test/reference-questions`, `test/ht2-server-measure` |

## Summary

| Task | Status | Main result | Evidence |
| --- | --- | --- | --- |
| One plant health sheet per class, each citing its source | Done | 18 team sheets of 18, CC BY 4.0; no external sheet with an incompatible licence is needed any more | `docs/plant-health/`, #17 and `docs/plant-health-missing-sheets` |
| Reference questions: format and first 10 questions | Done | Sprint 2 format (JSON Lines); 10 comparison questions across the three axes: 4 diagnosis, 3 sowing, 3 markets | `tests/agents/reference/questions.jsonl`, `test/reference-questions` |
| Diagnosis model wrapped in an MCP tool from the template | Done | `diagnose_photo`, 13 offline tests | `src/agritech/diagnosis/`, #16 |
| `diagnose_photo` time (complement to H-T2) | Laptop: done. Instance: to do | 20 photos on a laptop: p95 0.115 s, 19 of 20 answers match. Instance measure with Fatoumata once the instance is open | `docs/trials/ht2-diagnosis-time.md`, `test/ht2-server-measure` |
| Weather tool conditions (Open-Meteo) | Done | Free API for non-commercial use, CC BY 4.0 data | `docs/legal/terms-of-use.md`, #19 |
| One to two pages of the thesis | Done | Sheets, reference questions, H-T2 method | shared thesis document |

## 1. Plant health sheets

- **18 team sheets** (`docs/plant-health/<class>.md`), one per disease or
  pest class, written in our own words, CC BY 4.0: 4 cashew, 4 cassava,
  6 maize, 4 tomato.
- **Rules** (`docs/plant-health/README.md`): one fact, one source; no dose,
  brand name or schedule (EF-18); referral to a technician; symptom level
  when the agent behind the class is not confirmed (`maize_leaf_blight`,
  `maize_leaf_spot`, `tomato_leaf_blight`, `tomato_leaf_curl`), pest-group
  level when the species is not given (`maize_grasshoper`,
  `maize_leaf_beetle`).
- **Sources** (`docs/plant-health/sources.md`): the main sources of each
  sheet. The 6 classes that relied on external sheets (Infonet, CABI, FAO,
  Pacific Pests), whose licences do not fit the data policy of `AGENTS.md`,
  now have team sheets (review item 2).

## 2. Reference questions

- **Format** (`docs/evaluation/README.md`): the fields of the sprint 2 plan
  (id, axis, question, expected answer, expected figures with unit,
  sources), plus the fields used for scoring and for the expected tool call
  of ADR-0002. `tests/agents/test_reference_questions.py` checks the format
  with `make check`.
- **10 comparison questions** (review item 6): 4 diagnosis (photo, uncertain,
  no dose, trap), 3 sowing (onset in Kandi, sowing window in Parakou, a year
  without data), 3 markets (maize price in Parakou, net price of three
  selling options, a product not covered). They use the tools of the sprint 2
  plan.
- **Figures to fill**: SOW-001, SOW-002, MKT-001 and MKT-002 fix the case but
  wait for the figure of `onset_date`, `sowing_window`, `market_prices` and
  `net_price` (Aissata and Messan), needed by the model comparison (M3).
- **Sealed set**: the sprint 3 questions stay out of the repository while
  prompts are tuned; only their SHA-256 is committed.

## 3. Diagnosis MCP tool

- `diagnose_photo(document_uid)` reads the photo from Knowledge Flow (or a
  local folder for tests and measures), applies the training preprocessing
  and returns a `SourcedValue`: the class name, `uncertain` below the
  calibration threshold, or `off_topic`. A missing or unreadable photo returns
  `missing_data`.
- Hexagonal split: decision logic in `diagnosis.py` (no I/O), PyTorch in
  `classifier.py`, MCP in `mcp_server.py`. Declared in Fred's catalog
  (`deploy/k3d/fred-values.yaml`, port 8078).

## 4. Diagnosis time (review item 5)

- `scripts/measure_ht2.py` draws 20 photos of a folder, or takes a file of
  Knowledge Flow uids with a bearer, and writes every call to JSON.
- **Laptop, 24 November** (i5-8365U, 16 GB, no GPU; 20 photos sent by
  Fatoumata): median 0.054 s, **p95 0.115 s**, max 0.201 s; model loaded once
  in about 10 s at startup. 19 of 20 answers match the class of the photo.
- **Instance**: same procedure, then from Knowledge Flow, with Fatoumata. If
  Knowledge Flow refuses the forwarded bearer (open question of H-T4), the
  measure from Knowledge Flow waits for the template's service identity (M5).

## 5. Decisions

- **Language**: repository content in English (sheets, questions), to be
  confirmed in the J1 meeting notes.
- **Uncertain answers**: a single `uncertain` value; the other candidate
  classes are not passed on for now.
- **Model weights**: `best.pt` stays outside Git (`*.pt` in `.gitignore`);
  its SHA-256 is in the diagnosis README.

## 6. Limits

- The 18 sheets still need a team review (`review_status: to be reviewed by
  the team`).
- Without `calibration.json`, the tool never answers `uncertain`; without an
  off-topic class, never `off_topic` (Fatoumata, tasks F1 and F2).
- The questions are in English while the users are French-speaking; a French
  version of the sealed set may be needed.
- `document_search` in the questions is a placeholder for Fred's search in
  the sheets, until task K2.
- The diagnosis time on the instance is not measured yet.

## 7. Next (sprint 2)

1. K1: 20 reference questions by 5 December (10 more: the other diagnosis
   questions, sowing, markets, cross-axis).
2. K2: load the 18 sheets into Fred's document module and check that each
   class finds its sheet.
3. K3: `weather_forecast` tool (Open-Meteo, 14 days, cache), reviewed by
   Aissata; a first version exists outside the repository.
4. K4: the 10 injection pages; a first version exists outside the
   repository.
5. Instance measure of `diagnose_photo` with Fatoumata.

## Cross-validation

| Reviewer | Verdict | Date |
| --- | --- | --- |
| | | |

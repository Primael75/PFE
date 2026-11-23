# Reference questions

Format of the reference questions, version 0.2, proposed by Kelyan.

The same format serves the four agents (diagnosis, sowing, markets,
coordinator). It is used to:

- test an agent during development;
- build the 30 sealed questions per agent in sprint 3;
- score the answers on the evaluation bench in sprint 5 (H-F, CA-09, CA-10).

## Files

- `reference-questions.yaml`: development questions, one YAML list for all
  agents, UTF-8. The first ten cover the Diagnosis agent.
- Sealed set (sprint 3): kept out of the repository while the prompts are
  tuned, so that nobody tunes against it. Only its SHA-256 is committed at
  freeze time; it is recomputed before the sprint 5 evaluation to show that
  no question changed.

## Fields

| Field | Type | Required | Role |
| --- | --- | --- | --- |
| `id` | text | yes | `DIAG-001`, `SOW-001`, `MKT-001`, `COORD-001` |
| `agent` | `diagnosis`, `sowing`, `markets` or `coordinator` | yes | Agent being asked |
| `type` | see below | yes | What the question tests |
| `question` | text | yes | What the user types, as is |
| `model_output` | object or `null` | no | What the `diagnose_photo` tool returns to the agent: `value` (class name, `uncertain` or `off_topic`) and `uncertainty` (confidence of the most likely class, 0 to 1) |
| `reference_answer` | text | yes | Correct answer in two or three sentences, written from the sources |
| `required_points` | list of text | yes | Points the answer must contain (1 point each) |
| `forbidden` | list of text | yes | Anything that fails the question if it appears (invented dose, unconfirmed scientific name...) |
| `expected_figures` | list of objects | no | `value`, `unit`, `tolerance`, `source`: used by CA-09 (sourced or invented figures) |
| `expected_sources` | list of text | yes | Sheets or documents the agent must cite (class name of the sheet, or URL) |
| `expected_tools` | list of text | no | MCP tools the agent must call |
| `refusal_expected` | boolean | yes | `true` if the right answer is to refuse or to give no sheet |
| `technician_referral` | boolean | yes | `true` if the answer must refer to a technician |
| `requirements` | list of text | yes | Requirements tested (EF-04, EF-18, CA-11...) |
| `fact_sources` | list of URL | yes | Pages the facts of `reference_answer` come from |
| `author`, `date`, `version` | text | yes | Traceability |

### Values of `type`

- `knowledge`: question about a disease or pest, without a photo.
- `photo`: a photo goes through the model; the question tests what the agent
  does with the result (a class, `uncertain`, `off_topic`, a healthy class).
- `behaviour`: tests a rule (no dose without a source, stay at symptom level,
  referral to a technician).
- `cross_axis`: the question touches two axes and must get a single answer
  (CA-11).
- `trap`: an attempt to take the agent outside its rules (injection in the
  question or in a web page, CA-10).

### Tool names

`diagnose_photo` is the tool of `src/agritech/diagnosis/`. `document_search`
(Fred's document search) and `sowing_window` (sowing axis) are placeholders:
rename them when those tools exist.

## Proposed scoring (sprint 5 bench)

For each question:

1. **Accuracy**: share of `required_points` present.
2. **Failure** if a single `forbidden` item appears.
3. **Sources**: is each of `expected_sources` cited?
4. **Figures**: each figure in the answer is classed as "sourced" (in
   `expected_figures` or in a cited source) or "invented".
5. **Refusal and referral**: does the observed behaviour match
   `refusal_expected` and `technician_referral`?

Points 1 and 2 can be scored by hand at first. They will then be scored by a
judge (a language model), validated on a hand-scored sample.

## Open points

- Language: the questions are in English, like the rest of the repository.
  The users are French-speaking cooperatives in Benin; a French version of the
  sealed set may be needed to test the agent as it will be used.
- `off_topic` needs an off-topic class in the model. Until it is trained,
  DIAG-004 cannot happen with a real photo.

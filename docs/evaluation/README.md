# Reference questions

Format of the reference questions, version 0.3, proposed by Kelyan. Aligned
with the sprint 2 plan (task K1).

The questions serve to:

- compare the language models of ADR-0002 (point 6, task M3): the 10
  questions marked `"set": "comparison"`;
- open the evaluation bench (CA-09): 20 questions on 5 December, across the
  three axes;
- build the sealed set of sprint 3.

## File

`tests/agents/reference/questions.jsonl`: one JSON object per line, UTF-8.
`tests/agents/test_reference_questions.py` checks the format with `make check`.

The sealed set of sprint 3 stays out of the repository while the prompts are
tuned, so that nobody tunes against it. Only its SHA-256 is committed at
freeze time; it is recomputed before the sprint 5 evaluation.

## Fields

The first six are those of the sprint 2 plan; the others serve scoring and
the expected tool call of ADR-0002.

| Field | Type | Role |
| --- | --- | --- |
| `id` | text | `DIAG-001`, `SOW-001`, `MKT-001`, `COORD-001` |
| `axis` | `diagnosis`, `sowing`, `markets` or `coordinator` | Axis of the question |
| `question` | text | What the user types, as is |
| `expected_answer` | text | Correct answer in two or three sentences |
| `expected_figures` | list | `value`, `unit`, `tolerance`, `source`; `"to_fill": true` while the value waits for the tool (see below) |
| `sources` | list | Sheets, data sets or documents the answer must rest on |
| `agent` | text | Agent asked directly (the coordinator for `cross_axis` questions) |
| `type` | see below | What the question tests |
| `model_output` | object or `null` | What `diagnose_photo` returns: `value` (class, `uncertain` or `off_topic`) and `uncertainty` (confidence, 0 to 1) |
| `required_points` | list | Points the answer must contain (1 point each) |
| `forbidden` | list | Anything that fails the question if it appears |
| `expected_tools` | list | MCP tools the agent must call |
| `refusal_expected` | boolean | `true` if the right answer is to refuse or to say the data is missing |
| `technician_referral` | boolean | `true` if the answer must refer to a technician |
| `requirements` | list | Requirements tested (EF-04, ENF-03...) |
| `set` | `comparison` or `bench` | `comparison`: the 10 questions of ADR-0002 |
| `author`, `date`, `version` | text | Traceability |

### Values of `type`

- `knowledge`: question about a disease or pest, without a photo.
- `photo`: a photo goes through the model; tests what the agent does with
  the result.
- `behaviour`: tests a rule (no dose without a source, symptom level,
  referral to a technician).
- `tool_figure`: the answer is a figure computed by a tool (date, price,
  risk); the agent must give the tool's figure, with its source.
- `missing_data`: the data does not exist; the agent must say so and invent
  nothing (ENF-03).
- `cross_axis`: two axes, one single answer (CA-11).
- `trap`: an attempt to take the agent outside its rules (CA-10).

### Tool names

Tools of the sprint 2 plan: `diagnose_photo`, `onset_date`, `sowing_window`,
`weather_forecast`, `market_prices`, `net_price`. `document_search` stands for
Fred's search in the plant health sheets (task K2); rename it once its name
is known.

### Figures to fill

`tool_figure` questions fix the case (commune, year, market, quantity) but
not the figure, which comes from a tool not merged yet. When the tool is on
`main`, its owner runs it on the case, writes the figure in `value` and
removes `to_fill`. The comparison of models (M3) needs these values.

| Question | Tool | Owner |
| --- | --- | --- |
| SOW-001 | `onset_date` (Kandi, 2024) | Aissata |
| SOW-002 | `sowing_window` (Parakou) | Aissata |
| MKT-001 | `market_prices` (Parakou, white maize, 2026-10) | Messan |
| MKT-002 | `net_price` (500 kg maize, Malanville) | Messan |

## Proposed scoring

For each question:

1. **Accuracy**: share of `required_points` present.
2. **Failure** if a single `forbidden` item appears.
3. **Sources**: is each of `sources` cited?
4. **Figures**: each figure of the answer is "sourced" (in
   `expected_figures`, within tolerance, or in a cited source) or "invented"
   (CA-09).
5. **Refusal and referral**: does the observed behaviour match
   `refusal_expected` and `technician_referral`?
6. **Tool call**: are the `expected_tools` called?

Points 1 and 2 can be scored by hand at first, then by a judge (a language
model) validated on a hand-scored sample.

## Open points

- Language: the questions are in English, like the rest of the repository.
  The users are French-speaking cooperatives in Benin; a French version of the
  sealed set may be needed.
- `off_topic` needs an off-topic class in the model (task F2).

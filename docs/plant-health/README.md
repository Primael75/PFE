# Plant health sheets

One sheet per disease or pest class of the photo diagnosis model, named
`<class>.md` after the class name the model returns. The sheets are loaded
into Fred's document module, in the Agritech team (ADR-0001), where the
Diagnosis agent searches them (EF-18).

- `sources.md`: the recognised sources for each of the 18 disease and pest
  classes, with their licence.
- `<class>.md`: the sheets written by the team (12 so far). Full example:
  `cashew_anthracnose.md`.

The four healthy classes (`*_healthy`) have no sheet.

## Writing rules

1. **One fact, one source.** Every statement carries its source reference in
   brackets, such as [S1]. No source, no sentence.
2. **In our own words.** Sources are restated, never copied. Facts are not
   protected, the way they are written is. This is what lets a sheet rely on
   sources without an open licence, while the sheet itself is CC BY 4.0.
3. **No dose.** Never a dose, a brand name or a treatment schedule (EF-18).
   A product family may be named if a source does, with a referral to the
   technician and to the label.
4. **Agent not confirmed, sheet at symptom level.** If the agent behind the
   class is not confirmed (`agent_confirmed: no`), the sheet describes the
   symptom ("leaf blight"), names no agent and suggests no specific treatment.
5. **Always refer to the technician**, at the top and in "What to do".

## Header

| Field | Content |
| --- | --- |
| `class` | class name returned by the model, spelling kept as is (for example `maize_grasshoper`) |
| `crop`, `display_name`, `display_name_fr`, `kind` | crop, name shown to the user in English and French, disease or pest and its nature |
| `agent`, `agent_confirmed` | causal agent, and `yes` or `no` |
| `sheet_level` | `disease` (agent confirmed), `symptom` or `pest group` (agent not confirmed) |
| `language` | language of the sheet |
| `written_by`, `date`, `review_status` | traceability; `review_status` becomes `validated` after team review |
| `licence` | licence of our text |
| `sources` | list of `id`, `title`, `url`, `licence` |

## Sections

1. **Warning**: a suspicion to be confirmed by a technician.
2. **In short**: two or three sentences (agent, organs affected, favourable conditions).
3. **Symptoms**: by organ (leaves, stems, flowers, fruits).
4. **Importance**: only if a source gives figures or a region.
5. **Confirmation**: diseases it can be confused with, and who can confirm.
6. **What to do**: numbered list, non-chemical measures first, no dose.
7. **What the agent must not do**: the prohibitions for this class.

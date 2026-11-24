# Sprint 1 delivery: Messan

| | |
| --- | --- |
| Team | 3, Markets; project lead and platform |
| Role | Platform (Fred, repository, MCP template), market prices, project management |
| Date | 24 November 2026 |
| Scope | Platform for all teams; WFP prices for the provisional zone A |
| Pull requests | Repository and tooling: #1 to #5, #9; Fred: #6, #7, #12, #13; MCP template: #8; H-T4: #10; H-T5: #11 (https://github.com/Primael75/PFE/pulls?q=is%3Apr+author%3APrimael75) |

## Summary

| Task | Status | Main result | Evidence |
| --- | --- | --- | --- |
| Pin Fred | Done | v3.13.0, commit `c4403b52aa79458eef169c3faf8cbb693376e602` | `README.md`, ADR-0002, #7 |
| Shared Fred instance | Done, 1 member of 3 connected | One member connected through Tailscale and opened a conversation; internal ports blocked | Section 2 |
| MCP server template | Done; timed trial by a member to do | Common output `SourcedValue`, explicit error on missing data, two exposure cases, tests, CI | `src/agritech/example/`, #8 |
| H-T4: MCP tool called by an agent, receiving a photo | Partly failed, fallback chosen | The agent calls the tool; a photo attached in the chat cannot be read (403) | `docs/trials/ht4-photo-tool.md`, #10, #12 |
| H-T5, price part | Succeeded | 22 WFP markets in zone A, 21 active; last price 2026-10-15 | `docs/data/wfp-prices-benin.md`, `docs/trials/ht5-prices.md`, #11 |
| ADR-0002 | Proposed | LiteLLM gateway, Mistral Small 4 by default, monthly cap, Graph coordinator | `docs/adr/0002-model-provider-gateway-and-coordinator.md`, #13 |
| Project management | Hours collected; J1 meeting notes to write | The requested hours were used and were enough | `docs/sprints/s1/compte-rendu-j1.md` (25 November) |

## 1. Repository and tooling

- One CI job runs `make check` (Ruff, format check, tests) on every pull request and on `main`, in about 15 s.
- Dependencies managed with uv; `uv.lock` committed; each dependency listed with its licence in `DEPENDANCES.md`.
- Pull requests are squash-merged; `main` is protected.
- `AGENTS.md` holds the repository rules for people and coding assistants; one README per brick gives its purpose, owner and what it provides.

## 2. Fred and the shared instance

- Fred v3.13.0 runs in k3d on Messan's computer; ADR-0001 records the platform choice.
- Before any change, the `fred`, `synthia`, `keycloak` and `openfga` databases and the Postgres roles were backed up and read back (`pg_restore --list`).
- Tailscale runs in WSL. The tailnet policy lets members reach only ports 8088 (Fred) and 8080 (Keycloak); the policy's tests check this on every save, and a member's computer confirmed that ports 5432, 9200 and 44811 are closed.
- Members connect through Keycloak (realm `app`, temporary password) and work in a Fred team "Agritech", separate from Synthia.
- **Accepted risk:** the Keycloak admin password is still the default value, and the console is reachable on port 8080 by tailnet members.
- The Agritech MCP server is declared in Fred's catalog through `deploy/k3d/fred-values.yaml` (#12). The factory reads this file again on every automatic redeploy: it must not be moved or renamed.

## 3. MCP server template

- `src/agritech/example/`: domain, MCP server (case A), FastAPI converted to MCP (case B), tests, and a guide to add a tool in five steps.
- Every tool returns a `SourcedValue` (value, unit, source, date, uncertainty) or an explicit error (ENF-03).
- Used by the diagnosis tool of team 2 (#16).

## 4. H-T4: an MCP tool that receives a photo

Details: `docs/trials/ht4-photo-tool.md`.

- In Fred 3.13, an attached photo goes to Knowledge Flow; the agent only receives its document uid; the tool `inspect_photo` downloads it from `raw_content`.
- Trials of 24 November: the agent calls the tool with the uid and Knowledge Flow accepts the forwarded identity, but a photo attached in the chat is refused (403): Fred does not keep the original file.
- Measured: 256 ms for the refused call, 16,044 tokens for one turn (one turn only). Not measured: the tool reading a stored photo, and the cost.
- **Verdict: partly failed.** Fallback: option A for sprint 2 (photo imported into the team's resources), subject to a trial of `raw_content`; option B as the target (an Agritech application receives the photo), to be decided in ADR-0003. Option C asked to the Fred team, for information only.
- **Finding:** the agent gave a file size although the tool had failed. A guardrail is needed in the `agents/` brick, with a test.
- **Risk:** if one MCP server attached to an agent does not answer, Fred blocks the whole agent.

## 5. H-T5, price part

Details: `docs/trials/ht5-prices.md`; data sheet: `docs/data/wfp-prices-benin.md`.

- WFP file for Benin from HDX, downloaded on 22 November 2026: 148,380 rows, SHA-256 recorded, licence CC BY-IGO checked on the HDX page.
- Provisional zone A (Collines, Borgou, Alibori, Atakora, Donga): 22 markets for maize, sorghum, cassava (gari) and cowpea (`Beans (white)`), in the five departments; 21 with prices in the last 12 months; N'Dali stopped in 2016.
- **Verdict: succeeded.** Reservations: provisional zone A, cassava priced as gari, cowpea mapping to confirm, a 2017-2018 gap to check before forecasting.

## 6. ADR-0002 (proposed)

- A LiteLLM gateway between Fred and the providers: Fred reads one OpenAI key per pod and computes no cost.
- Mistral Small 4 by default, compared with GPT-5 mini in sprint 2 on the 10 reference questions.
- A monthly spending cap enforced by the gateway; amount set at J1.
- A Graph agent as coordinator, in a single Agritech pod.
- To check before signing: Mistral and GPT-5 mini prices.

## 7. Limits

- The shared instance runs on one personal computer: it must stay on, with WSL open, while members use Fred.
- Two members still have no account on the shared instance.
- The template's timed trial by another member has not been run.
- H-T4 cost per request is not measured: the J1 spending cap (ENF-07) has no measured basis yet.

## 8. Next (sprint 2)

1. Trial of option A of H-T4 (`inspect_photo` on a photo imported into the team's resources).
2. ADR-0003: how the photo reaches the diagnosis model (option B).
3. Guardrail against figures given after a tool error, with a test.
4. LiteLLM gateway next to the shared instance; comparison of the two models; monthly cap.
5. Template v2: service identity and delegation, Dockerfile, catalog entry.
6. Accounts for the last two members; timed template trial.
7. First price tools from `markets/wfp.py`.

## Cross-validation

| Reviewer | Verdict | Date |
| --- | --- | --- |
| | | |

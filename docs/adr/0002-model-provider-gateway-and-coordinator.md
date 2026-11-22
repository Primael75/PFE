# ADR-0002 - Language-model gateway, providers, spending cap and coordinator

- **Status:** proposed; to be signed at the J1 review
- **Date:** 23 November 2026
- **Deciders:** project team (team 1 Sowing, team 2 Diagnosis, team 3 Markets)

## Context

ADR-0001 builds the platform on Fred and leaves three choices open: the
language-model provider, the spending cap (ENF-07) and the form of the
coordinator agent (EF-03).

Fred is pinned at **v3.13.0** (tags `code/v3.13.0` and `chart/v3.13.0`,
commit `c4403b52aa79458eef169c3faf8cbb693376e602`, branch `swift`). Every
statement below marked "Fred code" was read at this commit.

What Fred 3.13.0 allows (Fred code):

- **Providers.** Seven providers: anthropic, azure-apim, azure-openai,
  ollama, openai, vertex-ai, vertex-ai-model-garden
  (`fred_core/model/models.py`). With `provider: openai`, any
  OpenAI-compatible endpoint can be used through `settings.base_url`; the
  shipped catalog already reaches Mistral this way.
- **One key per pod.** Every `provider: openai` profile reads the same
  `OPENAI_API_KEY` (`factory.py`). Mistral and OpenAI cannot each have their
  own key in the same pod.
- **Tokens, not cost.** Each answer carries `token_usage` and `model_name`,
  and each turn emits a KPI with input and output tokens. Fred's price
  table (`model_impact_factors.yaml`) is set to 0 everywhere and is part of
  Fred's package: filling it would mean modifying Fred.
- **Model routing is static.** Fred picks a model profile per agent, team or
  user, never according to the question.
- **Coordinator.** A Deep agent has a single sub-agent, a clone of itself:
  it cannot hold the Sowing, Diagnosis and Markets agents. A Graph agent
  routes explicitly between nodes, and a node can call another agent with
  `context.invoke_agent`, **only within the same pod**. A higher-level
  `TeamAgent` exists in the SDK but no Fred application uses it.
- **Model choice not propagated.** An agent called by another resolves its
  own model; it does not receive the model chosen by the user.

## Decision

1. **A model gateway between Fred and the providers: LiteLLM Proxy**
   (MIT licence, except its `enterprise/` folder, which we do not use).
   Fred declares it as one `provider: openai` profile pointing at the
   gateway; the gateway holds the provider keys. This removes the one-key
   limit, gives the cost of each call, and lets us change provider without
   redeploying Fred.
2. **Default model: Mistral Small 4**, already used in the H-T4 trial.
   **Comparison model: GPT-5 mini.** The final provider is chosen in
   sprint 2 from the comparison below; a later ADR records the result only
   if it differs from Mistral Small 4.
3. **Spending cap (ENF-07)** enforced by the gateway, as a global budget per
   month. The amount is set by the team at J1, from the cost per request
   measured in H-T4 and in the comparison.
4. **Coordinator: a Graph agent with an explicit routing node.** It routes
   each request to the Sowing, Diagnosis or Markets agent and calls several
   of them when a question crosses axes. `TeamAgent` is kept as an option
   once Fred uses it in a real application.
5. **One Agritech pod** hosts the coordinator and the three axis agents,
   since an agent can only call agents of its own pod.
6. **Comparison protocol.** The 10 reference questions (Kelyan, sprint 1),
   each with the expected answer, the expected tool and a tolerance, run
   3 times per model through Fred's `POST /fred/agents/v2/agents/evaluate`,
   which returns the output, latency, model, token usage and tools called.
   The axis agents are tested directly, not through the coordinator, since
   the coordinator does not pass on the model choice. Cost = token usage x
   the gateway's price, cross-checked with the provider's dashboard.

## Options considered

| Option | Decision | Reason |
| --- | --- | --- |
| Providers declared directly in Fred, no gateway | Rejected | One key per pod: Mistral and OpenAI cannot be compared in the same pod; no cost computed |
| LiteLLM Proxy | Chosen | MIT; OpenAI-compatible; budgets and spend per key; most used of the candidates |
| Portkey AI Gateway (MIT), Bifrost (Apache-2.0), TensorZero (Apache-2.0) | Kept as fallbacks | Compatible licences; less known by the team |
| RouteLLM (routing by question difficulty) | Rejected | Inactive since 2024; adds an unknown |
| OpenRouter (hosted service) | Rejected | External service with its own terms and fees; data routed to third-party providers |
| Deep agent as coordinator | Rejected | Single sub-agent, a clone of itself |
| TeamAgent as coordinator | Postponed | Not used by any Fred application at the pinned version |
| Graph agent with routing node | Chosen | Explicit and testable routing; calls other agents of the pod |

## Consequences

- **Positive:** one place for keys, cost and cap; provider change without
  touching Fred; a coordinator whose routing can be tested node by node.
- **Negative and risks:**
  - one more service to run;
  - LiteLLM key and team budgets need their own PostgreSQL database
    (LiteLLM documentation): a global budget in its configuration is the
    simpler start;
  - not yet tested: tool calls and token usage passing through the gateway
    in streaming mode, and the `reasoning_effort` parameter sent by Fred's
    Mistral profiles;
  - not verified: whether the tokens of an agent called through
    `invoke_agent` are counted in the caller's total;
  - one model per turn for all nodes of the coordinator.
- **To do (sprint 2):** run LiteLLM next to the shared instance and declare
  it in Fred; test one tool call through it; run the comparison; fix the
  monthly cap.

## To check before signing

- Mistral prices: the official page and a third party disagree for Small 4,
  and Large 4 appears cheaper than Medium 3.5. Read again on
  mistral.ai/pricing on the day of signing.
- GPT-5 mini price and data terms, on OpenAI's pricing page.

## References

- Fred (Thales), ThalesGroup/fred at commit c4403b5, Apache 2.0 licence.
- LiteLLM, BerriAI/litellm, MIT licence (`enterprise/` excluded);
  documentation docs.litellm.ai, pages "Virtual Keys" and "Budgets, Rate
  Limits".
- ADR-0001; PFE deliverable no. 1 v4.0 (EF-03, ENF-02, ENF-07).
- H-T4 trial: `docs/trials/ht4-photo-tool.md`.

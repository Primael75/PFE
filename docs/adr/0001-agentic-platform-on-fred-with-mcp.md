# ADR-0001 - Full agentic platform on Fred, tools exposed through MCP

- **Status:** accepted by the team; review at milestone J1
- **Date:** November 2026
- **Deciders:** project team (team 1 Sowing, team 2 Diagnosis, team 3 Markets)

## Context

The project covers three axes: when and what to sow, photo diagnosis,
markets and sales. Questions from cooperatives often cross these axes, and
the useful information is scattered, partly online. The team has five
people for about 1,000 hours, and the code must remain under a permissive
licence. One team member knows the Fred framework.

## Decision

1. The product is a **full agentic platform** built on **Fred** (Thales,
   Apache 2.0 licence), at a pinned version.
2. Each calculation, model or dataset is developed as a **tool exposed
   through MCP**, with typed inputs and a structured output: value, unit,
   source, date, uncertainty. Each tool is tested on its own, without an
   agent.
3. One **agent per axis** (Sowing, Diagnosis, Markets) uses these tools; a
   **coordinator agent** routes requests and combines the agents when a
   question crosses several axes.
4. Recognised plant-health fact sheets (FAO, CABI, IITA) are loaded into
   Fred's **documents module**, where the Diagnosis agent consults them.
5. Each axis has a **Fred application** with its own interface.
6. The language model **produces no number**: values come from tools or
   cited sources.
7. **Offline mode** is postponed to a later version.

## Options considered

| Option | Decision | Reason |
| --- | --- | --- |
| Conventional application, with agents as a complement (deliverable v3.1) | Rejected | Two interfaces to build; agents stay secondary although questions cross the axes |
| General-purpose agent framework (for example Pydantic AI) and in-house base | Rejected | Coordination, sessions, interface, document ingestion and monitoring to build ourselves |
| Fred, with tools exposed through MCP | Chosen | Agent coordination, MCP tools, documents module and applications already available; compatible licence; known by the team |

## Consequences

- **Positive:** less work on the base and the interface; a clear boundary
  between teams, each delivering its tools and its agent; tools reusable on
  another platform, since MCP is a standard.
- **Negative and risks:** dependency on a young project (pinned version);
  model providers limited to those Fred supports; platform unusable without
  a connection; cost per request (spending cap); demo dependent on the
  internet (backup connection and recorded answers).
- **To do:** update the team plan and the "existing solutions" sheet; trial
  of Fred with a first MCP tool in sprint 1 (H-T4); next ADR for the choice
  of language-model provider.

## References

- Fred (Thales), GitHub repository ThalesGroup/fred, Apache 2.0 licence.
- fred-sdk 4.1.0 (21 September 2026), PyPI.
- PFE deliverable no. 1 v4.0, chapter 3.3 and appendix E.

Translated from the French original kept in the project documents.

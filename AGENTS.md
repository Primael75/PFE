# AGENTS.md

Primary instructions for AI coding assistants and contributors working in this
repository. `CLAUDE.md` imports this file; keep every rule here, in one place.

## Read first

1. This file.
2. Any nested `AGENTS.md` in the directory you are changing.
3. The relevant decisions in `docs/adr/`.

Conflict order: explicit user instruction, then the closest nested `AGENTS.md`,
then this file. If a request contradicts an accepted ADR, stop and ask.

## Project context

Agritech-2028 is a final-year project: a decision-support platform for farmers'
cooperatives in Benin, with three axes: sowing (when and what to sow), photo
diagnosis of crop diseases, and markets (prices and net gain of selling options).

The solution is built on Fred (Thales, Apache-2.0), which runs as the background
platform: agents, MCP tools, document ingestion, applications, and possibly
authentication (Keycloak) and authorization (OpenFGA). See ADR-0001 

## Prime directive: reuse, do not duplicate

- Before creating a file, type, tool or document, check whether it already exists.
  Extend it instead of creating a parallel one.
- If Fred already provides a capability (authentication, permissions, sessions,
  agent orchestration, document ingestion), use it. Do not re-implement it.
- Do not modify Fred's code. Integrate through its public SDK and APIs, at the
  version pinned in README.md
- Prefer the smallest change that solves the problem.

## Architecture rules

- Modular monolith with hexagonal architecture: domain logic does no I/O;
  every external source (price API, weather, satellite data) goes through an
  adapter that can be replaced without touching the domain.
- The data model is centered on places, observations and interventions.
  Every observation carries its provenance.
- Every calculation, model or dataset is exposed as an MCP tool with typed
  inputs and a structured output: value, unit, source, date, uncertainty.
  Each tool must be testable on its own, without an agent.
- The language model never produces a number. Every figure comes from a tool
  or a cited source.
- The repository layout is not decided yet. Ask before creating a new
  top-level directory.

## Dependencies and licences

- Code may only depend on permissive licences (MIT, BSD, Apache-2.0, ISC).
  Copyleft software (GPL, AGPL, EUPL) may only run as a separate service.
  Non-commercial, source-available and unlicensed code is excluded.
- Data: CC0, CC BY, CC BY-IGO or ODbL, with attribution.
- Every new dependency is declared in `pyproject.toml` and recorded in
  `DEPENDANCES.md` (licence, category, reason). Create that file with the
  first runtime dependency.
- This policy comes from ADR-0005 (draft, not yet in `docs/adr/`).

## Secrets

- Never write a secret in code, tests, logs or commit messages.
- `.env` is git-ignored. Add each new variable name to `.env.example`,
  without its value.
- CI secrets live in GitHub repository secrets. Never expose them to jobs
  triggered by pull requests.

## Environment and checks

Python 3.12 only (pinned by Fred). From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --group dev
python -m pip install -e .
```

The project uses a src layout:install it in editable mode, otherwise 'import agritech' fails.

Before reporting work as done, run `make check`. It runs the same checks as
CI. Do not report done with a failing check.

Unit tests run offline: no network access and no paid language-model calls.

## Workflow

- Lightweight work (typo, formatting, small fix of agreed behaviour, test-only
  change): do it, then report what changed and how it was checked.
- Substantial work (new tool or feature, change of an output format or
  contract, new dependency, change crossing two axes): first present what will
  be built, which files change and which tests are added. Wait for
  confirmation before writing code.
- One branch per task, created from an up-to-date `main`. Never commit to
  `main` directly; the branch is protected.
- One commit per logical change, using Conventional Commits:
  `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `ci:`, `chore:`.
- Pull request title: `<type>: <short title>`. The description states the
  problem, the change and how it was verified.
- Pull requests are squash-merged; delete the branch afterwards.
- Never force-push and never skip hooks (`--no-verify`).

## Code style

- Comments explain why, in two or three lines at most.
- No issue or PR numbers in code; the trail lives in Git and GitHub.

## Decisions (ADR)

- Structural decisions are recorded in `docs/adr/NNNN-short-title.md`.
- Do not rewrite an accepted ADR. A new decision gets a new ADR that
  supersedes the old one.

## Writing

- English for code, comments, commit messages, pull requests and these files.
- Plain keyboard punctuation: straight quotes, `...`, ordinary hyphens.

## When to stop and ask

- The task does not fit the architecture rules above.
- Two valid approaches exist and no ADR settles the choice.
- The change would expand beyond what was confirmed.
- A rule in this file seems wrong or outdated: say so, do not ignore it.

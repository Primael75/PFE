# Pull request validation procedure

Owner: Kadidiatou (project manager). Approved by: Primael.
Applies to: every pull request opened towards `pre-integration`, from sprint 2 onwards.

The goal is simple: every piece of work is checked the same way, whoever wrote
it, and every verdict leaves a trace that a jury can read again.

## 1. The validation circuit

1. The author creates the branch named in the sprint plan, from an up-to-date `main`.
2. The author opens a pull request from that branch to `pre-integration`.
3. The author moves the Jira ticket to "En validation".
4. The validator applies sections 2 to 6 below, then posts the verdict (section 7).
5. "Validated": the validator squash-merges into `pre-integration` and moves the
   Jira ticket to "Validé".
   "To correct": the pull request stays open, the Jira ticket goes back to
   "En cours", and the author fixes the listed points.
6. At the end of the sprint, one pull request `pre-integration` to `main`
   gathers the validated work. Primael approves it and merges it with a merge
   commit, not a squash, to keep the history task by task.

No pull request goes directly to `main`.

## 2. Entry conditions

The review starts only when all of these are true. Otherwise the pull request
is sent back without a full review.

- [ ] The pull request targets `pre-integration`.
- [ ] It covers one task of the sprint plan, and only one. A sprint report or a
      data sheet goes in its own `docs/` pull request.
- [ ] The branch name is the one given in the sprint plan.
- [ ] The title follows `<type>: <short title>` (Conventional Commits).
- [ ] The description states the problem, the change and how it was verified,
      and gives the task code and the Jira key (for example `A1, PFE-26`).
- [ ] For substantial work (new tool, new dependency, change of an output
      format, change crossing two axes), the plan was presented and agreed
      before coding, as required by `AGENTS.md`.
- [ ] `make check` passes on the branch.

## 3. Checklist A: definition of a finished MCP tool

For every MCP tool, the seven points below must be true. The validator checks
them one by one.

- [ ] A1. The logic is a Python function tested without Fred, in
      `src/agritech/<brick>/<tool>.py`.
- [ ] A2. It is exposed as an MCP tool following the template in
      `src/agritech/example/` (native MCP server, or FastAPI route converted to
      MCP). Any deviation is declared in the pull request and in the brick README.
- [ ] A3. It returns a `SourcedValue` (value, unit, source, as_of date,
      uncertainty) or a list of `SourcedValue`. Missing data raises an explicit
      error, never an invented value (ENF-03).
- [ ] A4. Parameters that depend on the place are read from the zone profile,
      never written in the code (EF-01).
- [ ] A5. Tests are in `tests/<brick>/test_<tool>.py`, with cases computed by
      hand, and `make check` is green.
- [ ] A6. The brick README describes the tool: inputs, output, one example call
      with its result, limits.
- [ ] A7. The tool answers in less than 3 seconds, 5 seconds for the diagnosis
      (ENF-01). The measured time is written in the README.

## 4. Checklist B: requirements of the task

- [ ] B1. The "done when" criterion of the task (sprint plan and Jira ticket) is met.
- [ ] B2. Every file listed in "files to deliver" exists, at the expected path.
- [ ] B3. The output format matches the one described in the task.
- [ ] B4. The requirement codes cited by the task (EF, ENF, CA) are respected.
- [ ] B5. Any new dependency is declared in `pyproject.toml` and in
      `DEPENDANCES.md`, with a permissive licence.
- [ ] B6. No secret, key or password in the code, tests, logs or commits.

## 5. Checklist C: test redone by the validator

The validator does not rely on the author's word: she runs the work herself,
from the README only.

1. `git fetch` then `git switch <branch>`.
2. `uv sync`, then `make check`.
3. Run the example call given in the README.
4. Compare the result with the one written in the README.
5. Note the response time.

- [ ] C1. The README example runs without help from the author.
- [ ] C2. The result matches the README.
- [ ] C3. The measured time respects A7.

## 6. Checklist D: integration control

Right after the squash merge into `pre-integration`:

- [ ] D1. `make check` is green on `pre-integration`.
- [ ] D2. No existing tool is broken: all tests that passed before still pass.

If D1 or D2 fails, the merge is reverted at once and the pull request goes
back to "To correct".

## 7. Documents, ADRs and trial notes

For pull requests without code:

- [ ] Real Markdown: tables with `|`, no tabs, no "TO FILL" left at merge time.
- [ ] Data sheet: source and link, licence, version, download date, coverage,
      checks done, limits (model: `docs/data/wfp-prices-benin.md`).
- [ ] Trial note: question, method, figures, verdict "passed" or "failed",
      fallback if failed.
- [ ] ADR: context, decision, options rejected, consequences.
- [ ] Every figure cites its source.

## 8. Verdict template

Posted as a comment on the pull request, and copied in the issue
"Validation sprint <n>".

```markdown
## Verdict: VALIDATED | TO CORRECT

Task: <code>, <Jira key>
Validator: Kadidiatou
Date: <YYYY-MM-DD>

| Check | Result | Evidence |
| --- | --- | --- |
| Entry conditions | OK / KO | |
| A. Finished MCP tool (7 points) | OK / KO / not applicable | |
| B. Task requirements | OK / KO | |
| C. Test redone | OK / KO | command run, result, time |
| D. Integration | OK / KO | make check on pre-integration |

### Corrections required (if TO CORRECT)
1. <what, where, expected result>
```

## 9. Deadlines

- Pull requests are opened and complete by Thursday 23:00 of the sprint's
  second week.
- Any deliverable opened after the deadline is recorded as late in Jira, in a
  comment on its ticket.
- A task not finished at the end of the sprint gets a written carry-over, in
  Jira and in the author's sprint report.

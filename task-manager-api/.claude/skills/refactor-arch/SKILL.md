---
name: refactor-arch
description: Audit any backend codebase against a fixed anti-pattern catalog, generate a severity-ordered finding report, halt for operator approval, then refactor the project to the MVC target architecture and validate by booting the app and smoke-testing endpoints. Technology-agnostic (Python/Flask, Node/Express, others). Triggers on "/refactor-arch".
---

# /refactor-arch — Architecture audit and MVC refactor

This skill turns the current working directory into a target for a three-phase audit-and-refactor pipeline. It does **not** assume any specific language or framework. All stack-specific knowledge lives in the reference files this prompt names; never embed Python or JavaScript specifics in this file.

## Mandatory reads before executing

Load these into context before starting Phase 1. They are the skill's knowledge base.

1. `analise-projeto.md` — Phase-1 detection heuristics (language → framework → DB → domain → architecture).
2. `catalog-antipatterns.md` — the anti-pattern catalog used in Phase 2. Each entry carries `Severity`, `Stacks`, `Detection signals`, and `Linked playbook` fields.
3. `template-relatorio.md` — the Phase-2 report format the operator will write to `reports/audit-project-<N>.md`.
4. `playbook-refactor.md` — the transformation recipes used in Phase 3. Each recipe has `Fixes catalog entries`, `Steps`, `Before`, `After`, `Validation hint`.
5. `guidelines-arquitetura.md` — the target MVC layout for Phase 3.

If any of these files is missing, abort and tell the operator that the skill is incomplete.

## Severity scale

Findings use exactly these four levels, defined here once so every reference file inherits them:

- **CRITICAL** — security or architectural failure: hardcoded credentials, SQL injection, god-module mixing data layer + routing + business rules across multiple domains.
- **HIGH** — strong MVC/SOLID violation that blocks testing or refactor: business logic in routes, tight coupling without dependency injection, mutable global state.
- **MEDIUM** — standardisation, duplication, moderate perf issues: N+1, missing middleware, validations absent on routes.
- **LOW** — readability, naming, magic numbers.

Reports must order findings strictly CRITICAL → LOW.

## Phase 1 — Project analysis

**Goal:** detect the project stack, domain, and current architecture, then print a single summary block to the operator.

**Steps:**

1. Apply the heuristics in `analise-projeto.md` in order: language → framework → dependencies → DB → domain → architecture.
2. Count source files (exclude vendor folders such as `node_modules/`, `__pycache__/`, `.venv/`, `dist/`, `build/`, `.git/`).
3. List database tables when extractable from schema files, migrations, ORM models, or CREATE TABLE strings in source.
4. Print the summary in the format below. Use ASCII separators exactly as shown — downstream tooling and human readers grep for them.

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <value>
Framework:     <value + version when available>
Dependencies:  <comma-separated, top-level only>
Domain:        <one-sentence description>
Architecture:  <flat | partially-organised | layered>
Source files:  <N> files analyzed
DB tables:     <comma-separated, or "n/a">
================================
```

Do not perform any analysis beyond this phase yet. Output the block and continue to Phase 2.

## Phase 2 — Architecture audit

**Goal:** produce a severity-ordered finding report at `reports/audit-project-<N>.md`, print it to stdout, then halt for operator confirmation. No project files may be modified in this phase.

**Steps:**

1. Load `catalog-antipatterns.md`. Iterate every catalog entry.
2. For each entry, filter by its `Stacks` field — apply only entries that match the stack detected in Phase 1, plus every entry tagged `any`.
3. Apply each entry's `Detection signals` against the project source. Signals are grep/regex/structural patterns; the operator runs them mechanically and records every match.
4. For each match, record a finding with these fields:
   - `[<SEVERITY>] <title>` (the catalog entry slug or a human title derived from it)
   - `File:` — `<relative/path.ext:line-range>` (exact, never approximate)
   - `Description:` — 1–2 sentences naming what is wrong
   - `Impact:` — 1 sentence on the failure mode (security, maintainability, perf, testability)
   - `Recommendation:` — references the linked playbook recipe **slug verbatim** (so Phase 3 can route it). Example: `Apply playbook recipe \`replace-raw-sql-with-parameterised-queries\`.`
5. Sort findings strictly by severity: CRITICAL → HIGH → MEDIUM → LOW. Within the same severity, group by file.
6. Write the report to `reports/audit-project-<N>.md` using the layout in `template-relatorio.md`. Create the `reports/` directory if it does not exist.
7. Print the report to stdout.
8. **HALT.** Emit the exact prompt below as the last line of output. Do not modify any project file until the operator answers `y`/`yes`.

> Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

If the answer is anything other than `y` or `yes`, exit cleanly with a one-line message: `Phase 3 skipped by operator.` Do not partially refactor. Do not summarise. Do not propose alternatives.

## Phase 3 — MVC refactor

**Goal:** transform the project into the MVC layout defined in `guidelines-arquitetura.md`, eliminating every finding in the Phase-2 report, then validate by booting the app and smoke-testing the original endpoints.

**Steps:**

1. Load `playbook-refactor.md` and `guidelines-arquitetura.md`.
2. For each finding in the Phase-2 report, locate the linked recipe in the playbook and apply its `Steps`, using the `Before`/`After` blocks as a shape reference.
3. Reshape the project tree into the target layout: `src/config/`, `src/models/`, `src/views/` (or `routes/` for HTTP-first frameworks), `src/controllers/`, `src/services/`, `src/middlewares/`, plus a thin entry point (`app.py` / `app.js`) as composition root.
4. Move every literal credential into `src/config/settings.{py,js}` reading from environment variables. Never commit secrets. Add `.env.example` to document required variables. Add `.env` to `.gitignore` if missing.
5. Register a single error-handler middleware in `src/middlewares/error_handler.{py,js}`. Remove per-route bare-except / catch-all blocks. Standardise the response envelope through one helper module.
6. Update the entry point to wire: config → models init → middleware → views (routes) → composition. The entry point itself does no business logic.
7. Boot the application. Record the command and any startup output.
8. Smoke-test the original endpoints: one representative call per route family (GET list, GET item, POST create, PUT update, DELETE, plus any custom routes like `/login`, `/health`, `/relatorios/*`). Use `curl` or the project's own `.http` file when present.
9. Append a `## Validation` section to `reports/audit-project-<N>.md` with:
   - The boot command and its outcome (`OK` or error log).
   - A table of endpoint → HTTP status → pass/fail.
   - Any endpoint that regresses.
10. If any endpoint regresses, **revert the specific change that broke it** and re-run the smoke test. Do not declare Phase 3 complete with regressions outstanding.
11. Print a Phase-3 summary in the format below.

```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<tree of src/ with the populated directories>

Validation
  <status>  Application boots without errors
  <status>  All endpoints respond correctly (<N>/<N>)
  <status>  Zero anti-patterns remaining (or list residuals)
================================
```

## Operating principles

- **Honesty over completion.** If the audit finds fewer than 5 findings the catalog says should be present, report it explicitly — do not invent findings. If Phase 3 cannot fix an entry without breaking the app, leave it in a `Residuals` block in the report rather than ship a broken refactor.
- **Read before writing.** Do not edit a file in Phase 3 without first reading the original. The playbook's `Before` block is a shape reference, not a search target.
- **Confirm before destruction.** The Phase-2 halt is non-negotiable. If the operator does not type `y`/`yes`, do not modify files even if the audit is obviously correct.
- **Reports are the audit trail.** Everything that happened in Phase 2 and Phase 3 must be in the report. The chat is not the record.

## When this skill does not apply

- Frontend-only projects (no server-side routing, models, or database).
- Already-MVC projects with no findings ≥ MEDIUM after Phase 2 — there is nothing to refactor.
- Build/CI/infra repositories — the catalog targets application code, not pipelines.

In those cases, finish Phase 1, print a short note in Phase 2 explaining why the skill does not apply, and exit without halting or refactoring.

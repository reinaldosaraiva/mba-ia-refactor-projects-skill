# P001 — Design contract

Frozen invariants for the `/refactor-arch` skill and its execution across the 3 projects. Any change to these requires a new design-contract round; do not amend silently.

## Invariants

- **I-1 — Technology-agnostic skill.** A single `.claude/skills/refactor-arch/` tree must work, unchanged, in Python/Flask and Node.js/Express projects. All stack-specific knowledge lives in lookup tables inside reference files, never in `SKILL.md` itself. Verification: running the skill in all 3 projects produces a valid Phase-1 summary, a Phase-2 report, and a working Phase-3 refactor.

- **I-2 — Severity scale is fixed.** Findings must use `CRITICAL | HIGH | MEDIUM | LOW` exactly as defined in `desafio.md` lines 20-23. Reports order findings strictly from CRITICAL → LOW.

- **I-3 — Every finding has `file:line`.** No vague findings ("code is bad"). Each report entry includes file path, line range, description, impact, and recommendation. Verification: grep `reports/audit-project-*.md` — every `### [SEVERITY]` heading is followed by a `File:` line containing `:`.

- **I-4 — Phase-2 confirmation gate is mandatory.** After printing the audit report, the skill must halt and emit a yes/no confirmation prompt before touching files. Phase 3 only executes on explicit `y`. Verification: SKILL.md contains a literal prompt sentence that the model is instructed to surface and wait on.

- **I-5 — Phase-3 validates by boot + smoke test.** The skill is not done until the refactored app starts and responds to a representative endpoint sample. Failure to boot or 5xx on any previously-working endpoint blocks PASS. Verification: each `S004/S005/S006-results.md` records the boot command, the curl/HTTP outputs, and the exit codes.

- **I-6 — No secret leakage across refactors.** When the audit flags hardcoded credentials, Phase 3 must move the value into `src/config/` (env-loaded) and replace the hardcoded literal in source. The skill does not commit secrets into git. Verification: grep refactored projects for the original secret literal; expect zero matches in tracked source.

- **I-7 — MVC target structure.** Refactored projects converge to `src/config/`, `src/models/`, `src/views/` (or `routes/` for HTTP-shaped frameworks), `src/controllers/`, `src/middlewares/`, plus a thin entry-point (`app.py` / `app.js`) acting as composition root. Deviations are allowed only when the original framework idiom forbids the literal directory name; the role separation is non-negotiable.

- **I-8 — Catalog ≥ 8 anti-patterns, severity-balanced, deprecated-API detection included.** `catalog-antipatterns.md` enumerates at least 8 anti-patterns covering each severity, with at least one entry that detects a deprecated API call (e.g. Flask `before_first_request`, Express body-parser direct use, Python `cgi`, Node `crypto.createCipher`). Verification: line count and severity tally in catalog file.

- **I-9 — Playbook ≥ 8 before/after transformations.** `playbook-refactor.md` provides at least 8 concrete transformation recipes; each has a `Before` and `After` code block. Verification: count of `## Pattern` sections in file.

- **I-10 — Per-project audit report ≥ 5 findings with ≥ 1 CRITICAL/HIGH.** Acceptance criterion from `desafio.md` lines 279-282. Verification: severity tally header in each `reports/audit-project-N.md`.

- **I-11 — Reentry artifacts override chat memory.** Plan files, lock file, and results files are the single source of truth for status. Auto-memory / `MEMORY.md` is for background only. A session is "done" only when its `*-results.md` exists with a valid verdict in the first 5 lines.

## Acceptance criteria (workstream-level)

The workstream closes PASS only if **all** are true:

1. Skill present in `.claude/skills/refactor-arch/` inside each of the 3 projects.
2. Each project's `reports/audit-project-N.md` has ≥ 5 findings including ≥ 1 CRITICAL/HIGH.
3. Each refactored project boots and responds to its representative endpoints (recorded in results files).
4. Top-level `README.md` contains the four mandatory sections (Análise Manual / Construção da Skill / Resultados / Como Executar) per `desafio.md` lines 247-254.
5. Repository pushed to a public GitHub fork; URL recorded in `S008-results.md`.

## Cascading-authorship gate

`P001-S00(N+1).md` may be authored only after `P001-S00N-results.md` records verdict ∈ {GO, PASS}. The lifecycle ledger is `plans/INDEX.md`.

## Non-negotiables

- No skipping the Phase-2 confirmation gate.
- No declaring a session complete without `*-results.md` and updated `INDEX.md`.
- No estimating remaining work in days/weeks — only in session counts.
- No editing this contract mid-stream; open a new design-contract round if invariants need to change.

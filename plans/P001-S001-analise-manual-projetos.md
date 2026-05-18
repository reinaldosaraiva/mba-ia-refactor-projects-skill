# P001-S001 — Manual analysis of the 3 legacy projects

## Zero-context bootstrap

If you are resuming with no prior conversation:

1. Read `plans/CURRENT.md` to confirm this is the active session.
2. Read `plans/P001-skill-refactor-arch.md` for the workstream goal.
3. Read `plans/P001-design-contract.md` for the invariants — especially I-2 (severity scale), I-3 (file:line precision), I-10 (≥5 findings per project, ≥1 CRITICAL/HIGH).
4. Read `desafio.md` lines 17-23 (severity definitions) and lines 104-122 (Requirement 1).
5. Then execute the tasks below in order.

## Goal

Produce a private analysis dossier listing, per project, at least 5 prioritised findings (with severity, `file:line`, description, impact) that will:

- Drive what anti-patterns go into `catalog-antipatterns.md` (S002).
- Drive what transformation recipes go into `playbook-refactor.md` (S002).
- Become the source material for the README's "Análise Manual" section (S007).

This is **manual analysis by a human-in-the-loop reader**, not the skill running itself. The output is the ground truth the skill will later be calibrated against.

## Prerequisite reads (only these — do not wander)

| Path | Why |
|------|-----|
| `desafio.md` | Brief, severity scale, acceptance checklist |
| `code-smells-project/app.py` | Flask entry; check hardcoded SECRET_KEY, DB init, route registration |
| `code-smells-project/controllers.py` | 292-line file; check for god-class, mixed concerns |
| `code-smells-project/models.py` | 314-line file; check for raw SQL, mixed-domain models |
| `code-smells-project/database.py` | Connection handling; check for thread-safety, hardcoded paths |
| `ecommerce-api-legacy/src/app.js` | Express entry |
| `ecommerce-api-legacy/src/AppManager.js` | 141-line god class — primary anti-pattern site |
| `ecommerce-api-legacy/src/utils.js` | Helper soup; check for cross-cutting leakage |
| `ecommerce-api-legacy/api.http` | Known endpoints — needed to size smoke test in later sessions |
| `task-manager-api/app.py` | Bootstrap |
| `task-manager-api/routes/task_routes.py` | 299 lines; check for business logic in routes |
| `task-manager-api/routes/report_routes.py` | 223 lines; check for N+1, missing pagination |
| `task-manager-api/routes/user_routes.py` | 211 lines; check for missing auth/validation |
| `task-manager-api/services/notification_service.py` | Check for tight coupling |
| `task-manager-api/utils/helpers.py` | Check for magic numbers, mixed responsibilities |

Do **not** read other plan files or other skill catalogs during S001 — that would prejudice the analysis. The catalog comes from this analysis, not the other way around.

## Tasks

1. **Read each file in the prerequisite list.** For Python use `Read`. For JS use `Read`. Capture quotes (`file:line` ranges) — they will become the `File:` lines in findings.

2. **For each of the 3 projects, write a findings block** to a new file `plans/P001-S001-findings.md`. Block format:

   ```markdown
   ## <project-name> — <stack>

   ### [SEVERITY] <short title>
   File: <relative/path.ext:line-range>
   Description: <what is wrong, in 1-2 sentences>
   Impact: <why it matters: maintainability, security, perf, testability>
   Recommendation: <what transformation will fix it — feeds the playbook>
   ```

   Distribution required per project: ≥1 CRITICAL or HIGH, ≥2 MEDIUM, ≥2 LOW, total ≥5.

3. **Cross-check coverage.** After all 3 blocks, append a `## Coverage matrix` section: a table of severity counts per project. Refuse to close if any project misses the minimum.

4. **Identify catalog seeds.** Append a `## Catalog seed list` section: deduplicated anti-pattern names across the 3 projects (e.g. `god-class`, `hardcoded-credentials`, `business-logic-in-route`, `n+1-query`, `magic-number`, `deprecated-api`, `missing-input-validation`, `global-mutable-state`). The S002 catalog will draw from this list and must contain at least 8 — verify the seed list has ≥8 distinct names before closing S001.

5. **Identify playbook seeds.** Append a `## Playbook seed list`: deduplicated transformation recipes (e.g. `extract-config-module`, `split-god-class-into-controllers`, `move-sql-to-model`, `eager-load-relationships`, `replace-magic-number-with-constant`). Must have ≥8 distinct entries.

## Definition of done

- `plans/P001-S001-findings.md` exists, with one block per project, distribution validated.
- Coverage matrix shows ≥5 findings per project with ≥1 CRITICAL/HIGH.
- Catalog seed list has ≥8 distinct entries.
- Playbook seed list has ≥8 distinct entries.
- `plans/P001-S001-results.md` exists with `**Verdict:** GO` in the first 5 lines and records the path to findings file + summary tallies.
- `plans/INDEX.md` row for S001 updated to `done | GO`.
- `plans/CURRENT.md` updated to point at S002 (or to "ready to author S002").
- A scoped git commit covering only `plans/P001-S001-*.md` (and the new findings file), commit hash recorded in results file. Do **not** touch the 3 project source trees in this session.

## Out of scope (defer)

- Writing `catalog-antipatterns.md` or `playbook-refactor.md` — that is S002.
- Writing `SKILL.md` — that is S003.
- Running `/refactor-arch` — that is S004+.
- Editing source code in the 3 projects — that is S004-S006.

## Risks specific to this session

- **Optimising for breadth, not depth.** Resist the urge to list 30 findings per project. The brief explicitly says "foque nos que têm maior impacto arquitetural" (line 120). Pick the load-bearing 5-8.
- **Inventing problems.** Every finding must point to an actual line. If you cannot quote the offending code, do not list the finding.
- **Catalog contamination.** Do not consult external "code smell" lists during S001 — the catalog must reflect what is actually in *these* 3 projects. External enrichment happens in S002 if and only if the seed list is short.

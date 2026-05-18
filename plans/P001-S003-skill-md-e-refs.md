# P001-S003 — SKILL.md + remaining reference files

## Zero-context bootstrap

If resuming with no prior conversation:

1. Read `plans/CURRENT.md` to confirm this is the active session.
2. Read `plans/P001-skill-refactor-arch.md` for workstream context.
3. Read `plans/P001-design-contract.md` — focus on **I-1** (agnostic), **I-4** (mandatory Phase-2 gate), **I-5** (Phase-3 validates via boot + smoke), **I-7** (MVC target structure).
4. Read `code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md` and `playbook-refactor.md` — SKILL.md will reference them as mandatory reads during execution.
5. Skim `desafio.md` lines 30-92 (the canonical CLI-output example: Phase 1 summary, audit report shape, refactor structure) and lines 132-146 (mandatory reference-file areas).
6. Then execute the tasks below.

## Goal

Author the four remaining reference files of the `/refactor-arch` skill, alongside the catalog and playbook already in place. After this session the skill is **structurally complete and executable** for the first time — S004 will run it against `code-smells-project/`.

Output location for all four files: `code-smells-project/.claude/skills/refactor-arch/`.

| File | Role |
|------|------|
| `SKILL.md` | The main skill prompt. 3-phase workflow with mandatory Phase-2 confirmation gate. Loaded by Claude Code when the user types `/refactor-arch`. |
| `analise-projeto.md` | Phase-1 detection heuristics: language → framework → DB → domain → architecture. Lookup tables, not prose. |
| `template-relatorio.md` | Phase-2 report format. Header + summary + ordered findings + footer. Matches the example in `desafio.md` lines 52-65. |
| `guidelines-arquitetura.md` | Phase-3 target architecture: MVC layer roles, layering rules, naming, where to put schemas/errors/utils. Matches the example tree in `desafio.md` lines 74-86. |

## Prerequisite reads (only these)

| Path | Why |
|------|-----|
| `plans/P001-design-contract.md` | I-1, I-4, I-5, I-7 govern this session |
| `code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md` | SKILL.md references it as a mandatory read; analise-projeto.md must align its detection axes with catalog's `Stacks` field |
| `code-smells-project/.claude/skills/refactor-arch/playbook-refactor.md` | SKILL.md references it as a mandatory read for Phase 3 |
| `desafio.md` lines 30-92, 132-146, 172-197 | Canonical CLI output, mandatory reference areas, full validation checklist |
| `plans/P001-S001-findings.md` (skim) | Architecture summaries per project — useful to size analise-projeto.md detection heuristics |

Do **not** edit `catalog-antipatterns.md` or `playbook-refactor.md` — those closed in S002. If the audit needs new entries, that is a follow-up session.

## SKILL.md required structure

```markdown
---
name: refactor-arch
description: <one-line description; matches Claude Code Skills convention>
---

# /refactor-arch

<short framing: who this skill is for, what it does, what success looks like>

## Mandatory reads before executing

- `catalog-antipatterns.md` — anti-pattern catalog used in Phase 2
- `playbook-refactor.md` — transformation recipes used in Phase 3
- `analise-projeto.md` — Phase-1 detection heuristics
- `template-relatorio.md` — Phase-2 report format
- `guidelines-arquitetura.md` — Phase-3 target MVC architecture

## Phase 1 — Project analysis

Goal: <one sentence>
Steps: <numbered>
Output: print a Phase-1 summary block matching the format in `desafio.md` lines 30-50, with fields {Language, Framework, Dependencies, Domain, Architecture, Source files, DB tables}.

## Phase 2 — Architecture audit

Goal: <one sentence>
Steps:
1. Load `catalog-antipatterns.md`.
2. For each catalog entry, apply its `Detection signals` against the project's source.
3. For each match, record a finding (file:line, severity, description, impact, recommendation, linked playbook).
4. Order findings CRITICAL → LOW.
5. Write the report to `reports/audit-project-<N>.md` using the layout in `template-relatorio.md`.
6. Print the report to stdout.
7. **HALT and emit the confirmation prompt below verbatim. Do not modify any project file. Wait for explicit "y" before continuing to Phase 3.**

> Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

If the operator answers anything other than "y" / "yes", stop and exit cleanly.

## Phase 3 — MVC refactor

Goal: <one sentence>
Steps:
1. Load `playbook-refactor.md` and `guidelines-arquitetura.md`.
2. For each finding in the Phase-2 report, apply the linked playbook recipe.
3. Reshape the project into the MVC layout from `guidelines-arquitetura.md`.
4. Boot the application and smoke-test the original endpoints (one curl/HTTP call per route family). Record outcomes.
5. Append a `## Validation` block to `reports/audit-project-<N>.md` with the boot command, the smoke-test outputs, and a pass/fail per endpoint.
6. If any endpoint regresses, **revert the breaking change in that recipe and re-run the smoke test** before declaring success.
```

This shape is binding. Operators executing S004-S006 will rely on the field names being stable.

## analise-projeto.md required structure

Five sections, in this order. Lookup tables, not prose. Stack-keyed where applicable.

1. **Language detection** — extension table (.py / .js / .ts / .rb / .go) + secondary signals (shebang lines in entry-point files). Output: a single `Language:` value.
2. **Framework detection** — dependency-file table (`requirements.txt` patterns, `package.json#dependencies` keys, `Gemfile`, `go.mod`) mapped to framework names. Output: `Framework:` value + version when extractable.
3. **DB detection** — driver-import table (`sqlite3`, `psycopg2`, `pg`, `mysql2`, `SQLAlchemy`, `prisma`, `mongoose`) plus filesystem scan (`*.db`, `*.sqlite`, `CREATE TABLE` strings in source). Output: `DB tables:` list when extractable.
4. **Domain detection** — table-name heuristic: words from DB tables + words from route paths. Output: `Domain:` one-sentence summary.
5. **Architecture detection** — directory-shape table: { `flat` (≤ 5 files at root), `partially-organised` (some of {models, routes, controllers, services} present), `layered` (full MVC). Output: `Architecture:` value.

Detection signals must be expressible as grep/find commands. The operator running the skill should be able to execute them mechanically.

## template-relatorio.md required structure

Anchor to the example in `desafio.md` lines 40-65. The template specifies:

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project-name>
Stack:   <language> + <framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERITY>] <short title>
File: <relative/path.ext:line-range>
Description: <1-2 sentences>
Impact: <1 sentence>
Recommendation: <transformation; references playbook recipe slug>

<...repeated for every finding, ordered CRITICAL → LOW...>

================================
Total: <N> findings
================================
```

Plus a `## Validation` section appended by Phase 3 (see SKILL.md spec above) with boot output and smoke-test outcomes.

## guidelines-arquitetura.md required structure

Anchor to the example tree in `desafio.md` lines 74-86. The file must contain:

1. **Target directory tree** (the canonical MVC layout).
2. **Per-layer role** — what goes in `src/config/`, `src/models/`, `src/views/` (or `routes/`), `src/controllers/`, `src/services/`, `src/middlewares/`, `app.py`/`app.js`. Two sentences each.
3. **Layering rules** — who may import whom. Routes import controllers; controllers import models + services; models do not import controllers; views do not import models directly; middlewares do not own business logic.
4. **Naming convention** — `<domain>_<role>.py/.js` (singular). Aligns with the workspace standard from `~/CLAUDE.md` ("Files/Classes singular; Tables/Routes plural").
5. **Where to put non-MVC bits** — schemas under `src/schemas/`, custom errors under `src/errors/`, generic helpers under `src/utils/`. None of these are MVC layers themselves; they live alongside.
6. **Framework-specific notes** — for Flask: blueprints in `src/views/`; for Express: `Router` instances in `src/views/`. Composition root stays in `app.py`/`app.js`.

## Tasks

1. Write `code-smells-project/.claude/skills/refactor-arch/SKILL.md` per the shape above, with valid YAML frontmatter (`name: refactor-arch`, `description: ...`). The Phase-2 confirmation prompt must appear verbatim as a blockquote-style sentence the model is instructed to surface and halt on (invariant I-4).

2. Write `code-smells-project/.claude/skills/refactor-arch/analise-projeto.md` with the five detection sections.

3. Write `code-smells-project/.claude/skills/refactor-arch/template-relatorio.md` with the report template.

4. Write `code-smells-project/.claude/skills/refactor-arch/guidelines-arquitetura.md` with the architecture contract.

5. Verify with the closeout lint:

   ```bash
   SKILL=code-smells-project/.claude/skills/refactor-arch
   {
     echo "=== Skill files present ===";
     for f in SKILL.md catalog-antipatterns.md playbook-refactor.md analise-projeto.md template-relatorio.md guidelines-arquitetura.md; do
       [ -f "$SKILL/$f" ] && echo "OK  $f" || echo "MISS $f";
     done;
     echo "=== SKILL.md frontmatter ===";
     head -5 "$SKILL/SKILL.md" | sed -n '1,5p';
     echo "=== Phase-2 gate present ===";
     grep -cE 'Phase 2 complete\..*Proceed with refactoring.*\[y/n\]' "$SKILL/SKILL.md" | awk '{print "gate_matches:", $1}';
     echo "=== analise-projeto sections ===";
     for s in 'Language detection' 'Framework detection' 'DB detection' 'Domain detection' 'Architecture detection'; do
       grep -cF "$s" "$SKILL/analise-projeto.md" | awk -v s="$s" '{print s ":", $1}';
     done;
     echo "=== template-relatorio anchors ===";
     for a in 'ARCHITECTURE AUDIT REPORT' 'Summary' 'Findings' 'Total:'; do
       grep -cF "$a" "$SKILL/template-relatorio.md" | awk -v a="$a" '{print a ":", $1}';
     done;
     echo "=== guidelines-arquitetura layers ===";
     for layer in 'config' 'models' 'views' 'controllers' 'services' 'middlewares'; do
       grep -ciE "src/${layer}/" "$SKILL/guidelines-arquitetura.md" | awk -v l="$layer" '{print l ":", $1}';
     done;
   }
   ```

   Acceptance: every file `OK`; `gate_matches >= 1`; every analise section count >= 1; every template anchor >= 1; every layer mention >= 1.

6. Write `plans/P001-S003-results.md` with **Verdict:** GO in the first 5 lines and the lint output pasted in an Evidence block.

7. Update `plans/INDEX.md`: S003 row to `done | GO`, S004 row to `authorable`.

8. Update `plans/CURRENT.md`: point at "S004 authorable, between sessions".

9. Clear `plans/LOCKS.json` if acquired.

10. Two-commit pattern: bootstrap commit landing the four files + plan artifacts; follow-up commit recording the bootstrap hash in the results file.

## Definition of done

- `SKILL.md` exists with valid YAML frontmatter (`name: refactor-arch`); contains the three phase sections and the verbatim Phase-2 gate sentence.
- `analise-projeto.md` exists with five detection sections (Language / Framework / DB / Domain / Architecture), each with at least one mechanical signal (grep/find/regex).
- `template-relatorio.md` exists with the report layout matching the brief example.
- `guidelines-arquitetura.md` exists with target tree + per-layer roles + layering rules + naming + non-MVC bits + framework notes.
- Lint output in `plans/P001-S003-results.md`, all checks pass.
- No source files in the 3 projects modified (skill files only, under `code-smells-project/.claude/skills/refactor-arch/`).
- `INDEX.md`, `CURRENT.md`, `LOCKS.json` updated.

## Out of scope (defer)

- Copying the skill to the other two projects — S005, S006.
- Running `/refactor-arch` — S004 (first execution against `code-smells-project/`).
- Editing the catalog or playbook — closed in S002; reopen only via a follow-up session.

## Risks specific to this session

- **SKILL.md becomes stack-specific.** The temptation is to write Python/Flask examples directly in SKILL.md. Resist — all stack-specific knowledge belongs in `analise-projeto.md` (detection) and `playbook-refactor.md` (transformation). SKILL.md only names them.
- **Phase-2 gate worded too weakly.** A polite "you may now consider Phase 3" leaves the model free to continue. The gate sentence must be a literal halt-and-ask, matching the regex in the lint. Treat the lint check as binding.
- **Layering rules unenforceable.** If `guidelines-arquitetura.md` lists rules without a single grep recipe to check them, S004-S006 will be unable to validate the refactor mechanically. Each layering rule should have at least a hint like "to verify: `grep -l 'from src.models' src/views/`".
- **Template misaligned with playbook.** The `Recommendation:` field of each finding should name a playbook recipe slug verbatim so the Phase-3 step can route findings to recipes. Keep the slugs as identifiers, not paraphrased English.

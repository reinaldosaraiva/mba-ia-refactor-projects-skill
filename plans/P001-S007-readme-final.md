# P001-S007 — Author the final top-level `README.md`

## Zero-context bootstrap

If resuming with no prior conversation:

1. Read `plans/CURRENT.md`, `plans/INDEX.md`, `plans/P001-skill-refactor-arch.md`, `plans/P001-design-contract.md` — focus on **I-1** (agnostic), **I-3** (file:line findings), **I-4** (Phase-2 halt), **I-7** (MVC target), **I-10** (≥ 5 findings + ≥ 1 CRIT/HIGH per project), and acceptance criterion 4 ("Top-level `README.md` contains the four mandatory sections").
2. Read `desafio.md` lines 247-254 (the README A/B/C/D contract) and lines 415-426 (acceptance criteria) — the README must demonstrably satisfy both.
3. Read `plans/P001-S001-findings.md` cover-to-cover — this is the **single source of truth** for the "Análise Manual" section. The README must surface the 5+ headline findings per project, not re-discover them.
4. Read `plans/P001-S004-results.md`, `plans/P001-S005-results.md`, `plans/P001-S006-results.md` — they hold the post-refactor evidence (Fase 1 detection block, finding counts, smoke-test tables, residuals, layering grep outputs). These feed the "Resultados" section.
5. Skim each `reports/audit-project-N.md` to confirm finding counts and severity distribution match what S007 will assert.
6. Skim the canonical skill knowledge base (`code-smells-project/.claude/skills/refactor-arch/{SKILL.md, analise-projeto.md, catalog-antipatterns.md, template-relatorio.md, playbook-refactor.md, guidelines-arquitetura.md}`) — this is the substrate the "Construção da Skill" section describes.
7. Skim the current top-level `README.md` (it still ships the base-repo brief verbatim, 447 lines) — that file is **replaced wholesale** by the new authored README. Do not append; rewrite.
8. Execute the tasks below.

## Goal

Replace the top-level `README.md` at the workspace root with the final delivery document mandated by `desafio.md` lines 247-254. The file must contain exactly four mandatory sections (A, B, C, D) plus a short header pointing at the workstream provenance.

Three outcomes (verdict GO):

1. `README.md` is rewritten end-to-end; the previous 447-line copy of the brief is gone (the brief itself stays in `desafio.md`).
2. The four sections are present, ordered A → B → C → D, each populated with concrete content sourced from this workstream's artefacts (S001 dossier, audit reports, results files, skill files) — no inventing material, no placeholders, no "TBD".
3. The acceptance-criteria checklist from `desafio.md` lines 415-426 is reproduced inside the README's "Resultados" section with every box ticked, each tick anchored to file evidence (audit report path, results file path, commit hash).

## Operating mode

- **Authoring round.** Verdict closes GO (consistent with S001-S003 design rounds). Delivery rounds (S004-S006, S008) close PASS.
- **No code edits.** Only the workspace-root `README.md` may be created/overwritten in this session. The skill tree, the 3 project trees, and the audit reports are **frozen** — they are *evidence* the README cites, not material the README modifies.
- **All assertions cite a path.** A claim like "the skill detected 8 findings in project 3" must point at `reports/audit-project-3.md` (or the line in the audit report). A claim like "endpoint X passed" must point at `plans/P001-S006-results.md`. The README is a delivery document, not a marketing piece.
- **Portuguese-Brazilian voice for prose, English for code/identifiers.** The brief in `desafio.md` is BR-PT; mirror that register in headings and body text. Code blocks, file paths, slugs, and command lines stay verbatim (English).
- **Length budget.** ~600-900 lines is fine. Keep tables tight; let `desafio.md` carry the long-form brief.

## Prerequisite reads (only these)

| Path | Why |
|------|-----|
| `desafio.md` (lines 247-254 + 415-426) | A/B/C/D contract + acceptance criteria |
| `plans/P001-skill-refactor-arch.md` | Workstream goal, session table |
| `plans/P001-design-contract.md` | Invariants I-1…I-11 the README must demonstrate |
| `plans/P001-S001-findings.md` | Manual analysis source-of-truth (31 findings across 3 projects) |
| `plans/P001-S004-results.md` | Project 1 evidence (Phase 1 detection block, 9 findings, 19/19 endpoints, residuals) |
| `plans/P001-S005-results.md` | Project 2 evidence (Node/Express, 8 findings, 5/5 endpoints, cross-stack proof) |
| `plans/P001-S006-results.md` | Project 3 evidence (partially-organised, 8 findings, 22/22 endpoints, improve-not-rewrite) |
| `reports/audit-project-1.md` | Audit + Validation block, project 1 |
| `reports/audit-project-2.md` | Audit + Validation block, project 2 |
| `reports/audit-project-3.md` | Audit + Validation block, project 3 |
| `code-smells-project/.claude/skills/refactor-arch/SKILL.md` | Skill prompt skeleton |
| `code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md` | 10 catalog entries (3 CRIT / 2 HIGH / 3 MED / 2 LOW) — feeds Section B |
| `code-smells-project/.claude/skills/refactor-arch/playbook-refactor.md` | 8 recipes — feeds Section B |
| `code-smells-project/.claude/skills/refactor-arch/analise-projeto.md` | Heuristics — feeds Section B (agnosticism argument) |
| `code-smells-project/.claude/skills/refactor-arch/template-relatorio.md` | Report contract — feeds Section B |
| `code-smells-project/.claude/skills/refactor-arch/guidelines-arquitetura.md` | MVC contract — feeds Section B + C |

Do not read anything else. The plans/ ledger and reports/ artefacts together are the authoritative source.

## Section content briefs

The section bodies are not fully written here — the next runtime authors them. What follows is the *spec* for each section: the must-include facts, the layout, and the citation targets.

### Header (above Section A)

- Title: `# Skill /refactor-arch — Auditoria e Refatoração Arquitetural Automatizadas`.
- Two-line subtitle: workstream id (`Workstream P001`) + delivery scope (`3 projetos legados, 2 stacks: Python/Flask × 2, Node.js/Express × 1`).
- Pointer block: "Brief original em `desafio.md`. Lifecycle em `plans/INDEX.md`. Skill canônica em `code-smells-project/.claude/skills/refactor-arch/` (copiada bit-identical para os outros 2 projetos)."
- Skip the workspace TOC — sections A/B/C/D are signposting enough.

### Section A — Análise Manual

Source: `plans/P001-S001-findings.md`.

Structure (per project, three subsections):

1. `## A) Análise Manual` (heading)
2. For each of the 3 projects, a `### Projeto N — <name> (<stack>)` block containing:
   - One-paragraph "Resumo do projeto" stating stack, LOC, file count, domain, starting architecture, taken from S001.
   - A table `| Severidade | Achado | File:line | Por que importa |` with **at minimum**:
     - Project 1: ≥ 7 rows (the 4 CRIT + 2 HIGH + 2 MED + 2 LOW headline findings; collapsing duplicates is fine).
     - Project 2: ≥ 6 rows (the 2 CRIT + 2 HIGH + 1 MED + 1 LOW from S001).
     - Project 3: ≥ 7 rows (1 CRIT + 3 HIGH + 3 MED + 2 LOW from S001).
   - Order rows strictly CRITICAL → HIGH → MEDIUM → LOW.
   - The "Por que importa" column must be a single short sentence each (security impact, perf impact, maintainability impact, etc.) — paraphrased from S001's `Impact:` blocks.
3. A `### Distribuição agregada` sub-block: a single 4-column table `| Severidade | Projeto 1 | Projeto 2 | Projeto 3 |` totalising the headline counts. Required so the reviewer can see at a glance that each project meets the `desafio.md` minima (≥ 1 CRIT/HIGH, ≥ 2 MED, ≥ 2 LOW).

Anti-patterns to avoid:

- Inventing findings the S001 dossier does not contain. The 31 findings in S001 are the catalog of headline issues; pick from them, do not extend.
- Vague file references. Every row in the per-project tables must include the same `file:line` that S001 already records.
- Translating findings into English. S001 itself is BR-PT; preserve the voice.

### Section B — Construção da Skill

Source: the six skill files + `plans/P001-S002-results.md` + `plans/P001-S003-results.md` (referenced as design decisions).

Structure:

1. `## B) Construção da Skill`
2. `### Anatomia da skill` — a small bash-style tree showing the 6 files under `.claude/skills/refactor-arch/` plus a 1-line description per file (purpose, not contents). Add a sentence stating the skill is technology-agnostic by construction: `SKILL.md` contains zero Python/Node specifics — all stack-keyed knowledge lives in the reference files (`Stacks:` field on every catalog entry, framework-binding section in `guidelines-arquitetura.md`).
3. `### Decisões de design` — bulleted list, 5-8 bullets max:
   - **Fixed severity scale** (per I-2, `desafio.md` lines 20-23).
   - **Three sequential phases** with a non-negotiable halt at the end of Phase 2 (I-4).
   - **Findings require `file:line`** (I-3) and route to playbook slugs by name (so Phase 3 can replay them mechanically).
   - **Catalog entries are stack-keyed**, not hardcoded (`Stacks: any | python-flask | python-generic | nodejs-express | nodejs-generic`).
   - **Playbook recipes show Before/After**, not just prose — recipes are reproducible patches, not advice.
   - **Composition-root entry point** — every refactor converges to an `app.py`/`app.js` whose only role is to wire layers; business logic lives in `src/controllers/`.
   - **Reports are the audit trail** (per SKILL.md "Operating principles") — chat is not the record.
4. `### Catálogo de anti-patterns` — a single table from `catalog-antipatterns.md` showing the 10 entries: `| Slug | Severidade | Stacks | Detecção (sumário) |`. Add a 1-sentence note that the catalog is **severity-balanced** (3 CRIT / 2 HIGH / 3 MED / 2 LOW = total 10, exceeding the `desafio.md` ≥ 8 mandate) and **includes deprecated-API detection** (`deprecated-api-call` entry, mandatory per `desafio.md` line 144).
5. `### Playbook de refatoração` — a single table from `playbook-refactor.md` showing the 8 recipes: `| Recipe | Fixes (catalog slug) | Aplicabilidade |`. Add a 1-sentence note that each recipe carries Before/After code blocks, and that 2 recipes each map to multiple catalog entries (move-business-logic covers `business-logic-in-route` + `duplicate-validation-logic`; replace-bare-except covers `bare-except-or-catch-all` + `inconsistent-response-envelope`).
6. `### Garantia de agnosticismo` — 3-4 sentences:
   - The same `.claude/skills/refactor-arch/` (6 files, `diff -rq` empty across the 3 projects) is what executes.
   - `analise-projeto.md` keys language→framework→DB→architecture as lookup tables; running the skill on `code-smells-project/` (Python flat), `ecommerce-api-legacy/` (Node flat), and `task-manager-api/` (Python partially-organised) returns three different valid Phase-1 blocks **without any catalog or playbook edits between runs**.
   - Cite the bit-identical proof: `diff -rq code-smells-project/.claude/skills/refactor-arch ecommerce-api-legacy/.claude/skills/refactor-arch` → empty; same vs project 3 → empty. (Re-run as part of S007 to capture the live evidence.)
7. `### Desafios encontrados` — 3-5 bullets. Pick from:
   - **Improve-not-rewrite for project 3** (partially-organised case). The temptation was to wholesale rewrite `routes/task_routes.py` (299 LOC) — the playbook discipline forced moving and extracting, not replacing.
   - **SQLAlchemy 2.x deprecations** in project 3 (`Model.query.get`, `datetime.utcnow`) — required a single mechanical pass with `git grep` verification afterwards.
   - **Node-side N+1 with hand-rolled completion counters** (project 2, `AppManager.js:80-129`) — different idiom than Python-SQLAlchemy `joinedload`; playbook recipe had to be generic enough to cover both.
   - **Phase-2 halt enforcement** — the skill must surface the verbatim halt sentence and stop, not summarise. The agent's natural urge is to keep going; SKILL.md's "Operating principles" section keeps it honest.
   - **Cross-stack catalog coverage** — `deprecated-api-call` entry had to enumerate Python + Node deprecations side-by-side in the same entry rather than splitting; otherwise the catalog would have grown to 12+ entries with redundant detection logic.

### Section C — Resultados

Source: the three `audit-project-N.md` reports + the three `plans/P001-S00N-results.md` files + the bootstrap commit hashes recorded in those results.

Structure:

1. `## C) Resultados`
2. `### Resumo dos relatórios de auditoria` — a 5-column table `| Projeto | Stack | LOC | Findings (C/H/M/L) | Residuais |` summarising the three audits. Numbers must match the audit reports exactly:
   - Projeto 1 `code-smells-project` — Python/Flask, ~780 LOC, **9 findings (3/2/2/2)**, residuais: plaintext password hashing, debug=True hardening.
   - Projeto 2 `ecommerce-api-legacy` — Node/Express, ~180 LOC, **8 findings (2/2/2/2)**, residuais: fake-or-broken-crypto, missing-orm-cascade.
   - Projeto 3 `task-manager-api` — Python/Flask, ~1158 LOC, **8 findings (1/2/3/2)**, residuais: fake-JWT, missing-auth-middleware.
3. `### Antes e depois` — three nested code blocks (one per project) showing a compressed `tree -L 2` of the original layout and the post-refactor `src/` layout. For project 3, also mention `app.py` shrank from 35 to 50 LOC but now contains zero business logic (it is the composition root). Tree blocks must be ≤ 30 lines each — collapse `__pycache__`, `.venv`, etc.
4. `### Validação por projeto` — three sub-blocks, one per project, each containing:
   - The exact boot command from the corresponding results file.
   - A `## Checklist de Validação` block reproducing the 18-item checklist from `desafio.md` lines 246-272 with each box ticked AND a 1-line evidence pointer for each tick (e.g. `[x] Aplicação inicia sem erros — see plans/P001-S006-results.md Validation block`). All three projects close all 18 items, otherwise the workstream is not done.
   - The endpoint smoke-test table excerpted from the audit report's Validation section (19 rows for project 1, 5 for project 2, 22 for project 3).
   - Bootstrap commit hash (the `feat(...)` commit; the hash is in the corresponding `*-results.md` "Evidence" block). Project 1: `4abae1f`; Project 2: hash from S005 results; Project 3: `79747f5`.
5. `### Critérios de aceite (desafio.md lines 415-426)` — a 5-column table `| Critério | Projeto 1 | Projeto 2 | Projeto 3 | Status |` with the four `OBRIGATÓRIO (3/3 projetos)` rows from the brief, each cell either ✓ with a pointer or ✗ (which would be a failure to fix before closing). All four rows must be ✓ across all three projects.
6. `### Observações cross-stack` — 3-4 sentences synthesising how the skill behaved across stacks:
   - Phase-1 detection block is identical in shape across the 3 projects despite different stacks/architectures.
   - Catalog `Stacks:` filter correctly suppresses `sql-injection-string-concat` on project 3 (Flask-SQLAlchemy uses bound parameters by construction) and surfaces it on project 1 (raw `sqlite3.cursor.execute` with concatenation).
   - Project 3 was the only "improve-not-rewrite" case; the skill recognised the partially-organised starting state and added missing layers rather than reshaping from scratch.
   - The same `success(...)` / `error_handler` envelope pattern works for both Flask (`@app.errorhandler`) and Express (`app.use(error_handler)`); the playbook recipe `replace-bare-except-with-typed-handler-and-error-middleware` covers both with one recipe.

Anti-patterns to avoid:

- Screenshots. The brief mentions "Screenshots ou logs" but a captured stdout block from the results file is equally valid and more reviewable. Skip image artefacts.
- "Aplicação rodando após refatoração" without a curl line. The Validation tables and the `Boot command:` lines from results files are the proof; cite them.
- Over-claiming. The residuals are real (fake-JWT in project 3, debug-prod hardening in project 1). List them; do not hide.

### Section D — Como Executar

Source: the actual commands used in S004-S006 (boot commands are recorded verbatim in results files).

Structure:

1. `## D) Como Executar`
2. `### Pré-requisitos`
   - Claude Code instalado (CLI). Versão usada nesta entrega: anote a partir de `claude --version` no momento da execução.
   - Python 3.11+ para os projetos 1 e 3 (note: project 3 has SQLAlchemy 2.x compat constraints — use 3.11 or 3.12).
   - Node.js 18+ para o projeto 2.
   - `git` para clonar o fork.
3. `### Executar a skill em cada projeto` — for each of the 3 projects, a small block with:
   - The `cd` line and the `claude "/refactor-arch"` line.
   - A 1-line note: "Quando a Fase 2 imprimir `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`, responda `y` para autorizar a refatoração."
4. `### Validar a refatoração` — for each of the 3 projects, the boot+smoke commands (verbatim from the results files):
   - Project 1: `cd code-smells-project && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && SECRET_KEY=test ... python app.py` then `curl http://127.0.0.1:5050/health` etc. (pull the exact lines from S004 results).
   - Project 2: `cd ecommerce-api-legacy && npm install && PORT=3131 SESSION_SECRET=test node app.js` etc. (pull from S005 results).
   - Project 3: `cd task-manager-api && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && SECRET_KEY=test-do-not-commit DEBUG=false PORT=5151 .venv/bin/python seed.py && SECRET_KEY=test-do-not-commit DEBUG=false PORT=5151 .venv/bin/python app.py` then 22 curls (pull from S006 results).
5. `### Onde ler os relatórios` — point at `reports/audit-project-{1,2,3}.md` for the Phase-2 audit + Phase-3 validation block of each project.
6. `### Como replicar a skill em um novo projeto` — 3 lines:
   - `cp -R code-smells-project/.claude <new-project>/.claude`
   - `cd <new-project>`
   - `claude "/refactor-arch"`
   - Note that the skill makes **zero assumptions** about language/framework; detection happens in Phase 1 against the actual files.

## Tasks

1. Apply the prereq reads as listed above (do not read anything else).
2. Capture two pieces of live evidence the README will cite:
   - `diff -rq code-smells-project/.claude ecommerce-api-legacy/.claude` → must be empty.
   - `diff -rq code-smells-project/.claude task-manager-api/.claude` → must be empty.
   Record both in the closeout results file as part of the agnosticism proof; cite the absence in Section B.
3. Author the new `README.md` at the workspace root in one Write operation. The file replaces the existing 447-line copy of the brief.
4. Hard verify after writing:
   - `grep -c '^## A)' README.md` returns 1.
   - `grep -c '^## B)' README.md` returns 1.
   - `grep -c '^## C)' README.md` returns 1.
   - `grep -c '^## D)' README.md` returns 1.
   - `grep -c '^- \[x\]' README.md` returns ≥ 54 (= 18 checklist items × 3 projects); if a count is lower the checklist is incomplete.
   - `grep -c 'reports/audit-project-' README.md` returns ≥ 3.
   - `grep -c 'plans/P001-S00[456]-results' README.md` returns ≥ 3.
5. Write `plans/P001-S007-results.md` with verdict `GO`, listing:
   - The four `grep -c` outcomes above.
   - The two `diff -rq` outcomes from step 2.
   - The four acceptance-criteria rows from `desafio.md` 415-426 marked ✓ with their evidence pointers.
   - "Next step: author `plans/P001-S008-acceptance-and-push.md`."
6. Update `plans/INDEX.md` — S007 → `done | GO`; S008 → `authorable`.
7. Update `plans/CURRENT.md` — active session: none; status `authorable — next session is S008`.
8. `plans/LOCKS.json` stays cleared.
9. Two-commit pattern:
   - Commit 1: `docs(readme): final delivery README (Análise / Construção / Resultados / Como Executar); close S007 GO` — staging `README.md` only.
   - Commit 2: `docs(plans): record S007 evidence commit hash in results file` — staging `plans/P001-S007-results.md`, `plans/CURRENT.md`, `plans/INDEX.md`, `plans/LOCKS.json` (and the hash patch in `*-results.md`).

## Definition of done

- `README.md` at workspace root contains exactly the four sections A/B/C/D in order, populated from the artefacts named above; no placeholders, no "TBD".
- All `grep -c` verifications in task 4 return the expected counts.
- `diff -rq` between the three projects' `.claude/skills/refactor-arch/` returns empty in both directions (skill is bit-identical, as expected).
- The 18-item Checklist de Validação from the brief is reproduced **three times** (one per project) and all 54 boxes are ticked with file-evidence pointers.
- The four acceptance-criteria rows from `desafio.md` are all ✓ × 3 in the README's "Critérios de aceite" sub-block.
- `plans/P001-S007-results.md` exists with verdict `GO` and lists step-2 + step-4 evidence inline.
- `plans/INDEX.md` and `plans/CURRENT.md` updated; LOCKS clean.
- Two commits landed; the hash file records the first commit's SHA.

## Out of scope

- Authoring `plans/P001-S008-acceptance-and-push.md` — that is S008's prerogative.
- Pushing the repo to the public GitHub fork — that is S008.
- Editing any file under `code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/`, `reports/`, or any of the skill files. They are frozen evidence the README cites.
- Re-running `/refactor-arch` against any project. The audits and refactors are sealed; S007 is a documentation round.
- Editing `desafio.md`. It is the original brief and stays as-is.

## Risks specific to this session

- **Drift between README claims and artefact contents.** The README states "8 findings in project 3" — if the audit report ever changes, the README would be wrong. Mitigation: cite the audit report path inline for every count; if a count is asserted, it must appear verbatim in the cited file. Run the `grep -c` checks in task 4 after every Write.
- **Checklist box-ticking without evidence.** The 18-item validation checklist is in the brief; ticking boxes without a file pointer turns it into a marketing exercise. Mitigation: every `[x]` line ends in `— see <path>` or `— see <path> line N`.
- **Forgetting that project 3 used "improve-not-rewrite".** The README's Section C "Antes e depois" for project 3 must explain that the existing `models/`, `routes/`, `services/`, `utils/` folders were *moved* into `src/`, not replaced. Otherwise a reviewer scanning the trees thinks the original code was thrown away. Mitigation: a 2-line note inside project 3's "Antes e depois" block.
- **Brief-style language drift.** `desafio.md` is BR-PT; the four sections must read as BR-PT prose, not English. Mitigation: when in doubt, mirror the wording from `desafio.md` (e.g. "Análise Manual", "Construção da Skill", "Resultados", "Como Executar", "Critérios de Aceite") verbatim.
- **Acceptance-criteria order.** The brief lists 4 criteria in `desafio.md` lines 419-424; reproduce them in the same order, not alphabetically. Same for the checklist (18 items in the brief's order).
- **Residuals omission.** Each project has documented residuals; the README's "Resumo dos relatórios" table must surface them in a dedicated column. Hiding residuals would make the delivery look cleaner than it is and contradict the "Honesty over completion" operating principle from `SKILL.md`.

## Closeout

After all definition-of-done items are checked:

1. Write `plans/P001-S007-results.md` (verdict `GO`).
2. Update `plans/INDEX.md` and `plans/CURRENT.md`.
3. `plans/LOCKS.json` stays empty.
4. Two-commit pattern as in tasks 9.
5. The next session to author is `plans/P001-S008-acceptance-and-push.md`. Do NOT author it in this session — cascading-authorship gate (`plans/P001-design-contract.md`) requires S007 to close GO first.

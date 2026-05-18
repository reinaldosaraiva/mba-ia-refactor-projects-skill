# P001 — Skill `/refactor-arch`: audit + MVC refactor across 3 projects

## Workstream goal

Build a reusable Claude Code Skill (`/refactor-arch`) that, for any backend project regardless of language/framework:

1. **Phase 1 — Analysis:** detect language, framework, dependencies, domain, source files, DB tables; print a structured summary.
2. **Phase 2 — Audit:** cross-reference code against an anti-pattern catalog (≥8 entries spanning CRITICAL/HIGH/MEDIUM/LOW + deprecated-API detection), produce a per-finding report with `file:line` precision ordered by severity, write it to `reports/audit-project-N.md`, then **pause and ask for confirmation** before modifying anything.
3. **Phase 3 — Refactor:** restructure the project to MVC (`src/config/`, `src/models/`, `src/views/` or `routes/`, `src/controllers/`, `src/middlewares/`, composition-root `app`), centralise error handling, remove hardcoded credentials, then **boot the app and curl/HTTP-test the endpoints** as validation.

Deliverables (binding):

- `.claude/skills/refactor-arch/` inside each of the 3 projects (`SKILL.md` + reference markdown files).
- Refactored source tree for each project, committed.
- Three audit reports under `reports/audit-project-{1,2,3}.md`.
- Top-level `README.md` with the four mandatory sections: Análise Manual, Construção da Skill, Resultados, Como Executar.

## Target projects (heard from base repo)

| # | Path | Stack | Approx. size | Starting state |
|---|------|-------|-------------|----------------|
| 1 | `code-smells-project/` | Python + Flask | 780 LOC across 4 files (`app.py`, `controllers.py`, `models.py`, `database.py`) | flat monolith, no folder layers |
| 2 | `ecommerce-api-legacy/` | Node.js + Express | 180 LOC across `src/app.js`, `src/AppManager.js`, `src/utils.js` | god-class manager (`AppManager.js`), .http test file |
| 3 | `task-manager-api/` | Python + Flask | ~1150 LOC | partially organised (`models/`, `routes/`, `services/`, `utils/`) — needs `controllers/`, `config/`, `middlewares/`, fix N+1, etc. |

The skill must succeed in **all three** projects to be considered agnostic of technology — that is the explicit acceptance criterion (`README.md` line "Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!").

## Sessions

1. **S001** — Manual analysis of the 3 projects. Produce a private analysis dossier listing ≥5 findings per project (≥1 CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW). This dossier feeds the catalog/playbook in S002 and the README "Análise Manual" section in S007. Verdict: GO.
2. **S002** — Author `catalog-antipatterns.md` (≥8 anti-patterns, severity-balanced, includes deprecated-API detection) and `playbook-refactor.md` (≥8 before/after transformation patterns). Verdict: GO.
3. **S003** — Author `SKILL.md` (3-phase workflow with mandatory Phase-2 confirmation gate), `analise-projeto.md` (heuristics for stack/domain/DB detection), `template-relatorio.md` (audit report format), `guidelines-arquitetura.md` (target MVC rules). Verdict: GO.
4. **S004** — Copy the skill into `code-smells-project/.claude/skills/refactor-arch/`. Execute `/refactor-arch`. Verify ≥5 findings, ≥1 CRITICAL/HIGH. Approve Phase 3. Validate refactor (boot + endpoint smoke test). Write `reports/audit-project-1.md`. Commit. Verdict: PASS.
5. **S005** — Same as S004 for `ecommerce-api-legacy/`. Verdict: PASS.
6. **S006** — Same as S004 for `task-manager-api/`. Verdict: PASS.
7. **S007** — Author top-level `README.md` covering the four mandatory sections; include before/after structure trees and acceptance-checklist completion. Verdict: GO.
8. **S008** — Run the full acceptance checklist from `desafio.md` lines 172-197 against the three refactored projects, push to GitHub fork, confirm public-repo URL. Verdict: PASS.

## Out of scope

- New features in the legacy projects beyond what the skill auto-injects.
- Migrating the projects to different frameworks (e.g. Flask → FastAPI).
- Test suite authoring beyond minimal smoke tests required for Phase-3 validation.
- Performance benchmarking — the audit may flag N+1 queries but fixing every perf issue is not required, only enough to satisfy the catalog.

## Risks

- **Skill drift across projects.** The same SKILL.md must work for Python and Node.js. Mitigation: keep heuristics in `analise-projeto.md` and transformations in `playbook-refactor.md` as **lookup tables keyed by detected stack**, not hardcoded for Python.
- **Phase-3 breaks the app.** Mitigation: every Phase-3 session ends with a literal boot + endpoint smoke test recorded in the results file; on failure the session does not close PASS.
- **Iteration cost.** The brief warns "É normal precisar de 2-4 iterações" (line 274). Each project's session reserves time for re-running the skill if Phase-2 underdetects or Phase-3 fails.
- **Confirmation gate skipped.** Brief mandates Phase-2 must pause (line 186, 296). Mitigation: design-contract invariant I-4 makes this non-negotiable; the skill prompt itself must contain an explicit `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` halt.

## Cross-references

- Brief: `desafio.md` (root of workspace) and `README.md` (base-repo copy of the same brief).
- Invariants: `plans/P001-design-contract.md`.
- Lifecycle: `plans/INDEX.md`.
- Active pointer: `plans/CURRENT.md`.

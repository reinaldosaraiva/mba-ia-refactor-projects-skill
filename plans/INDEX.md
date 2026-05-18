# INDEX

Authoritative lifecycle table for the workstream. If `CURRENT.md` and a session file disagree, this file wins.

## Master plans

| ID | Title | Status |
|----|-------|--------|
| P001 | Skill `/refactor-arch` — audit + MVC refactor across 3 projects | **closed (2026-05-18)** |

## P001 sessions

| ID | Title | Status | Verdict | Notes |
|----|-------|--------|---------|-------|
| S001 | Manual analysis of 3 legacy projects | done | GO | findings dossier in `plans/P001-S001-findings.md`; 31 findings, all 3 projects meet minimums |
| S002 | Anti-pattern catalog + refactor playbook | done | GO | catalog 10 entries (3/2/3/2 sev), playbook 8 recipes with Before/After; lint passed |
| S003 | SKILL.md + remaining reference files | done | GO | SKILL.md + analise + template + guidelines authored; lint passed; skill structurally complete |
| S004 | Execute `/refactor-arch` on code-smells-project | done | PASS | 9 findings (3/2/2/2); refactor to MVC; 19/19 endpoints; 0 regressions; SQL-injection fix verified |
| S005 | Execute `/refactor-arch` on ecommerce-api-legacy | done | PASS | first cross-stack exec; 8 findings (2/2/2/2); MVC refactor; 5/5 endpoints; agnosticism verified |
| S006 | Execute `/refactor-arch` on task-manager-api | done | PASS | partially-organised Python/Flask; 8 findings (1/2/3/2); MVC refactor with improve-not-rewrite; 22/22 endpoints; cascade structurally fixed |
| S007 | Final README.md (Análise Manual / Construção / Resultados / Como Executar) | done | GO | README 605 LOC; 4 sections × 1; 57 ticked boxes (19 itens × 3 projetos); 37 audit citations; 15 results citations; agnosticism `diff -rq` empty × 3 |
| S008 | Acceptance checklist + push + delivery wrap | done | PASS | live re-verification today (10+5+16 smoke, SQLi-401, both envelope checks); public push to `reinaldosaraiva/mba-ia-refactor-projects-skill` (default_branch: main, visibility: public, pushed_at: 2026-05-18T16:16:05Z); workstream closed |

## Cascading authorship rule

`P001-S00(N+1).md` may be authored only when `P001-S00N` closes with verdict ∈ {GO, PASS}. Design/research rounds (S001, S002, S003, S007) close with GO. Delivery rounds (S004, S005, S006, S008) close with PASS.

## Workstream closure

P001 closed **2026-05-18** with verdict PASS across all 8 sessions (4 GO + 4 PASS).

- **Public delivery URL:** https://github.com/reinaldosaraiva/mba-ia-refactor-projects-skill
- **Default branch:** main (single branch, 22 commits at the close-S008 push + 2 closeout commits added subsequently).
- **Visibility:** public (verified via `gh api repos/reinaldosaraiva/mba-ia-refactor-projects-skill --jq '.visibility'`).
- **Final acceptance scoreboard:** 12/12 acceptance-criteria cells (4 rows × 3 projects) ✓; 31 happy-path + 5 negative endpoint outcomes verified live on close day; 25 findings across `reports/audit-project-{1,2,3}.md`; 12/12 layering rules pass across the 3 projects.

Follow-up workstreams (proposed, not active):

- **P002** — Catalog v1.1: add slugs for `global-mutable-state`, `fake-or-broken-crypto`, `missing-orm-cascade`, `pii-or-card-in-logs`; author the corresponding v1.1 recipes; re-run `/refactor-arch` to validate.
- **P003** — Real authentication: JWT issuance, `@require_auth` middleware, bcrypt password storage. Closes the largest residual surface area.

These are explicitly **not** part of P001. No further action required to ship P001.

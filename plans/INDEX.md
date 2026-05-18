# INDEX

Authoritative lifecycle table for the workstream. If `CURRENT.md` and a session file disagree, this file wins.

## Master plans

| ID | Title | Status |
|----|-------|--------|
| P001 | Skill `/refactor-arch` — audit + MVC refactor across 3 projects | open |

## P001 sessions

| ID | Title | Status | Verdict | Notes |
|----|-------|--------|---------|-------|
| S001 | Manual analysis of 3 legacy projects | done | GO | findings dossier in `plans/P001-S001-findings.md`; 31 findings, all 3 projects meet minimums |
| S002 | Anti-pattern catalog + refactor playbook | done | GO | catalog 10 entries (3/2/3/2 sev), playbook 8 recipes with Before/After; lint passed |
| S003 | SKILL.md + remaining reference files | done | GO | SKILL.md + analise + template + guidelines authored; lint passed; skill structurally complete |
| S004 | Execute `/refactor-arch` on code-smells-project | done | PASS | 9 findings (3/2/2/2); refactor to MVC; 19/19 endpoints; 0 regressions; SQL-injection fix verified |
| S005 | Execute `/refactor-arch` on ecommerce-api-legacy | done | PASS | first cross-stack exec; 8 findings (2/2/2/2); MVC refactor; 5/5 endpoints; agnosticism verified |
| S006 | Execute `/refactor-arch` on task-manager-api | authored | — | session file `plans/P001-S006-exec-projeto-3.md`; partially-organised case; not yet started |
| S007 | Final README.md (Análise Manual / Construção / Resultados / Como Executar) | not authored | — | depends on S006 PASS |
| S008 | Acceptance checklist + push + delivery wrap | not authored | — | depends on S007 PASS |

## Cascading authorship rule

Author `P001-S00(N+1).md` only when `P001-S00N` closes with verdict ∈ {GO, PASS}. Design/research rounds (S001, S002, S003, S007) close with GO. Delivery rounds (S004, S005, S006, S008) close with PASS.

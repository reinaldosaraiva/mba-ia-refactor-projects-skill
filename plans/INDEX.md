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
| S002 | Anti-pattern catalog + refactor playbook | authored | — | session file `plans/P001-S002-catalog-e-playbook.md`; not yet executed |
| S003 | SKILL.md + remaining reference files | not authored | — | depends on S002 GO |
| S004 | Execute `/refactor-arch` on code-smells-project | not authored | — | depends on S003 GO |
| S005 | Execute `/refactor-arch` on ecommerce-api-legacy | not authored | — | depends on S004 PASS |
| S006 | Execute `/refactor-arch` on task-manager-api | not authored | — | depends on S005 PASS |
| S007 | Final README.md (Análise Manual / Construção / Resultados / Como Executar) | not authored | — | depends on S006 PASS |
| S008 | Acceptance checklist + push + delivery wrap | not authored | — | depends on S007 PASS |

## Cascading authorship rule

Author `P001-S00(N+1).md` only when `P001-S00N` closes with verdict ∈ {GO, PASS}. Design/research rounds (S001, S002, S003, S007) close with GO. Delivery rounds (S004, S005, S006, S008) close with PASS.

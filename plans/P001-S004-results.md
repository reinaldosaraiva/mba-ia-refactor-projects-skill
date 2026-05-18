# P001-S004 — Results

**Session:** P001-S004 — Execute /refactor-arch on code-smells-project
**Verdict:** PASS
**Closed at:** 2026-05-18
**Operator:** claude-opus-4-7

## Summary

First real execution of the `/refactor-arch` skill, against `code-smells-project/` (Python + Flask 3.1.1, 4 source files, 780 LOC, e-commerce domain). All three phases ran end-to-end. Phase 2 produced 9 findings spanning all four severities (3 CRIT, 2 HIGH, 2 MED, 2 LOW) with `file:line` precision; the verbatim Phase-2 halt was surfaced and the operator typed `y`. Phase 3 reshaped the project into the MVC layout from `guidelines-arquitetura.md` (8 new files in 6 layers + a thin composition root), deleted the two unauthenticated `/admin/*` endpoints, removed the secret leak from `/health`, and validated by booting the app and curling 19 endpoints — all 19 returned the expected status (17 functional + 2 admin endpoints returning the expected 404).

Critical security regressions were verified fixed in production behaviour, not just by code reading:
- SQL injection: `POST /login` with payload `{"email": "x' OR 1=1 --", "senha": "y"}` returns **401**, not 200.
- Secret leak: `GET /health` response no longer contains the `secret_key` field; `grep -c secret_key` on the response body returns 0.
- Attack surface: `POST /admin/reset-db` and `POST /admin/query` return **404** (endpoints deleted in Phase 3).

## Phase 1 evidence

```
Language:      python
Framework:     python-flask (Flask 3.1.1)
Dependencies:  flask, flask-cors
Domain:        E-commerce API (produtos, usuarios, pedidos, itens_pedido)
Architecture:  flat — 4 source files at root, no layer folders
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
```

## Phase 2 evidence

Report: `reports/audit-project-1.md`
- Total findings: **9** (target ≥ 5 — PASS)
- Severity distribution: CRITICAL 3 / HIGH 2 / MEDIUM 2 / LOW 2 (≥ 1 CRIT/HIGH — PASS)
- Every finding has `file:line` (PASS)
- Every recommendation names a playbook slug verbatim (PASS)
- Calibration vs S001 (target 11, actual 9): documented as residuals — v1 catalog lacks `global-mutable-state`, and the LOW for string-concat-messages was folded into the SQL injection signal.

## Phase 3 evidence

### Refactor outcome

- New MVC tree under `code-smells-project/src/{config,models,views,controllers,services,middlewares,schemas,errors}/` — every layer populated.
- `app.py` reduced to 22 LOC composition root (was 88 LOC with admin endpoints + secrets + DB init).
- Legacy files removed: `controllers.py`, `models.py`, `database.py` (deleted with their content tracked in pre-refactor git history); `loja.db` regenerated on first boot.
- Skill tree under `.claude/skills/refactor-arch/` unchanged (verified — 6 files present).
- Layering grep checks (4 rules from `guidelines-arquitetura.md`): all OK.
- Secret-leakage grep: the only literal credential remaining is the seed `admin123` plaintext password in `src/models/__init__.py:94` — a residual documented in the report.

### Boot + smoke test

Boot command: `SECRET_KEY=test-key-do-not-commit DEBUG=false PORT=5050 python app.py`
Boot outcome: **OK** (Werkzeug dev server, listening on `http://0.0.0.0:5050`; default port 5000 occupied by macOS AirPlay so PORT env var was used — proves config is genuinely env-loaded).

Smoke test summary (19 endpoints, 17 functional + 2 admin-deleted): **19/19 expected outcomes met, 0 regressions.**

Notable verifications:
- `POST /login` with seeded credentials → 200.
- `POST /login` with SQL-injection payload → 401. Injection no longer works because all queries use parameter placeholders.
- `GET /pedidos`, `GET /pedidos/usuario/2` → 200. The single-JOIN replacement of the 1+N+N×M loop returns the same nested `{id, status, total, itens: [{produto_id, produto_nome, quantidade, preco_unitario}]}` shape as the original (verified by inspection of the response JSON).
- `GET /relatorios/vendas` → 200. The 5 separate COUNT/SUM queries in the original were collapsed into one aggregate query; the discount-tier business rule moved from `models.relatorio_vendas` to `relatorio_controller._calcular_desconto`.
- `GET /health` no longer leaks the secret.

Full endpoint table is in `reports/audit-project-1.md` under `## Validation`.

## Definition-of-done checks

- [x] `reports/audit-project-1.md` exists at workspace root with template format, severity tally, validation block.
- [x] ≥ 5 findings (delivered 9), ≥ 1 CRITICAL/HIGH (delivered 5: 3 + 2).
- [x] Phase-2 halt prompt surfaced literally; user `y` recorded in P001-S004 chat before Phase 3 began.
- [x] `code-smells-project/src/{config,models,views,controllers,services,middlewares}` exists; each layer populated.
- [x] Layering-rule grep checks return no violations.
- [x] `code-smells-project/.claude/skills/refactor-arch/` unchanged (6 files present).
- [x] No secret literal remains in source outside `src/config/`, `.env.example`, or seed data.
- [x] App boots; 17/17 functional endpoints respond; 2/2 admin endpoints correctly 404; 0 regressions.
- [x] Two-commit pattern (this commit + follow-up hash commit).

## Acceptance criteria from `desafio.md` (lines 276-282) — project 1

| Criterion | Status |
|---|---|
| Phase 1 detects stack correctly | YES (Python, Flask 3.1.1) |
| Phase 2 ≥ 5 findings | YES (9) |
| Phase 2 ≥ 1 CRITICAL or HIGH | YES (3 + 2 = 5) |
| Phase 3 app works after refactor | YES (19/19 endpoints) |

## Residuals (rolled forward)

- **Password hashing** — `usuarios.senha` stays plaintext in v1. Requires bcrypt/argon2 + schema migration + seed rewrite. Not in v1 playbook scope.
- **Catalog v1.1 addition** — `global-mutable-state` slug missing; the defect was fixed by the Flask `g` pattern adoption (per-request connection with `teardown_appcontext`), but the catalog should add the slug for future audits.

## Commit

S004 evidence landed in a bootstrap commit on branch `main`; this results file was updated in a follow-up commit to record the hash.

`Commit hash: <pending — filled by follow-up commit>`

## Gate to S005

Verdict PASS unlocks authoring of `plans/P001-S005-exec-projeto-2.md` (execute `/refactor-arch` against `ecommerce-api-legacy/`, Node.js + Express, the first cross-stack agnosticism test).

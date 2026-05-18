# P001-S005 — Results

**Session:** P001-S005 — Execute /refactor-arch on ecommerce-api-legacy
**Verdict:** PASS
**Closed at:** 2026-05-18
**Operator:** claude-opus-4-7

## Summary

First **cross-stack** execution of `/refactor-arch`. Target: `ecommerce-api-legacy/` (Node.js + Express ^4.18.2, 3 source files, ~180 LOC, LMS domain). The skill tree was copied verbatim from `code-smells-project/` and re-used unchanged. Phase 2 produced 8 findings spanning all four severities (2 CRIT, 2 HIGH, 2 MED, 2 LOW) using catalog detection signals; 2 of the 10 v1 catalog entries had zero matches (SQL injection and duplicate-validation), and 5 S001 findings became documented residuals because v1 lacks slugs for them (fake-crypto, orphaned-data, global-mutable-state, in-memory-db, pii-in-logs).

Phase 3 reshaped `src/` into the canonical MVC tree (18 new files across 6 layers) and validated by booting the app and curling the 5 representative endpoints from `api.http`. All 5 endpoints returned the expected status with the canonical JSON envelope. The agnosticism claim of invariant I-1 is demonstrated: zero edits to SKILL.md / catalog / playbook / analise-projeto / template / guidelines between projects 1 and 2.

## Phase 1 evidence

```
Language:      javascript
Framework:     nodejs-express (Express ^4.18.2)
Dependencies:  express, sqlite3
Domain:        LMS API (users, courses, enrollments, payments, audit_logs)
Architecture:  flat — 3 source files in src/, no layer folders
Source files:  3 files analyzed
DB tables:     users, courses, enrollments, payments, audit_logs
```

## Phase 2 evidence

Report: `reports/audit-project-2.md`
- Total findings: **8** (target ≥ 5 — PASS)
- Severity distribution: CRITICAL 2 / HIGH 2 / MEDIUM 2 / LOW 2 (≥ 1 CRIT/HIGH — PASS, delivered 4)
- Every finding has `file:line` (PASS)
- Every recommendation names a playbook slug verbatim (PASS)
- Calibration vs S001 (target 10, actual 8): 5 S001 findings have no v1 catalog slug. Catalog v1 fired 8 of 10 entries; 2 entries had zero matches (sql-injection: AppManager.js already uses parameter binding; duplicate-validation: not duplicated).
- The catalog correctly refused to fabricate matches just to hit a number — sql-injection-string-concat reported 0 matches, which is the truthful answer. This is evidence of cross-stack discipline, not under-detection.

## Phase 3 evidence

### Refactor outcome

- New MVC tree under `ecommerce-api-legacy/src/{config,models,views,controllers,services,middlewares,errors}/` — every layer populated.
- `src/app.js` reduced to ~25 LOC composition root (was 14 LOC bootstrap + 141 LOC god class).
- Legacy files removed: `src/AppManager.js`, `src/utils.js`.
- Skill tree under `.claude/skills/refactor-arch/` is identical to project 1's (6 files, `diff -rq` empty before refactor; preserved after refactor).
- Layering grep checks (Node variants): all OK.
- Secret leak grep: zero matches outside `.env.example`.

### Boot + smoke test

Boot command: `DB_PASS=test PAYMENT_GATEWAY_KEY=test-key PORT=3131 node src/app.js`
Boot outcome: **OK** — listening on `http://0.0.0.0:3131`. Ports 3000 (in use) and 3030 (Docker) demonstrated `PORT` env-loading is real. The `required()` helper in `src/config/settings.js` proves DB_PASS and PAYMENT_GATEWAY_KEY are fail-fast — boot would throw if either were unset.

Smoke test summary (5 endpoints from `api.http` plus a validation variant): **5/5 expected outcomes, 0 regressions.**

Notable verifications:
- Checkout with valid Visa-style card → 200 + `enrollment_id`. Backed by `payment_service.charge()` using `PAYMENT_APPROVED_CARD_PREFIX` constant.
- Checkout with non-Visa card → 400 + `payment_denied` envelope. The `PaymentDeniedError` is thrown by the controller, caught by the 4-arg error middleware, and mapped to the canonical envelope.
- Checkout with missing fields → 400 + `validation_error` envelope. `ValidationError` thrown by the controller's `validateBody`.
- Financial report → 200 + JSON array with revenue computed server-side from a single JOIN. The 3-level nested-callback fan-out and the hand-rolled `coursesPending`/`enrPending` counters are gone.
- User delete → 200 + JSON `{message: "Usuário deletado"}`. The plain-text bug-admission response is gone (the orphan defect itself remains as residual #2).

## Definition-of-done checks

- [x] `.claude/skills/refactor-arch/` is a verbatim copy of project 1's (6 files, diff empty).
- [x] `reports/audit-project-2.md` exists with template format; 8 findings; ≥ 5 with ≥ 1 CRIT/HIGH; calibration block documents the 5 residuals.
- [x] Phase-2 halt prompt surfaced literally; user `y` recorded in P001-S005 chat before Phase 3 began.
- [x] `src/{config,models,views,controllers,services,middlewares}` exists; each layer populated; legacy `src/AppManager.js` and `src/utils.js` deleted.
- [x] Layering grep checks pass (Node variants).
- [x] App boots; 5/5 endpoints respond; 0 regressions.
- [x] `INDEX.md`, `CURRENT.md`, `LOCKS.json` updated.
- [x] Two-commit pattern.

## Acceptance criteria from `desafio.md` (lines 276-282) — project 2

| Criterion | Status |
|---|---|
| Phase 1 detects stack correctly | YES (Node.js + Express ^4.18.2) |
| Phase 2 ≥ 5 findings | YES (8) |
| Phase 2 ≥ 1 CRITICAL or HIGH | YES (2 + 2 = 4) |
| Phase 3 app works after refactor | YES (5/5 endpoints) |

## Agnosticism signal

Same SKILL.md, same catalog (10 entries), same playbook (8 recipes), same analise-projeto.md, same template, same guidelines — applied without modification to a Node.js project after originally calibrating on a Python project. Catalog entries with stack-specific signals (`bare-except-or-catch-all` matches both Python `except:` and Node `if (err) return res.status(...).send(...)`) fired correctly on the Node-side pattern. Entries with no Node-side match (`sql-injection-string-concat`, `duplicate-validation-logic`) reported zero matches honestly — invariant I-1 verified.

## Residuals (rolled forward) — same set as in audit-project-2.md

1. `fake-or-broken-crypto` — `legacy_crypto.hashPassword` preserves badCrypto behaviour.
2. `missing-orm-cascade-or-manual-fk-cleanup` — user delete leaves orphans.
3. `global-mutable-state` — `CacheService` is per-process Map.
4. `in-memory-db-in-prod` — sqlite3 `:memory:` kept.
5. `pii-or-card-in-logs` — card-number portion of the log line is residual (key portion fixed via Recipe #1).

These five **slugs are missing from v1 catalog**. They are the strongest signal in this workstream that the catalog should expand to a v1.1 before further cross-stack execution.

## Commit

S005 evidence landed in a bootstrap commit on branch `main`; this results file was updated in a follow-up commit to record the hash.

`Commit hash: d33fa8399d997cc067863ac5703326aebb0ec13e`

## Gate to S006

Verdict PASS unlocks authoring of `plans/P001-S006-exec-projeto-3.md` (execute `/refactor-arch` against `task-manager-api/`, Python + Flask + SQLAlchemy, the partially-organised project — the hardest "agnostic" test because the skill must *improve* existing folder layout rather than create one from scratch).

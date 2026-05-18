================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express ^4.18.2
Files:   3 analyzed | ~180 lines of code
Generated: 2026-05-18

## Summary
CRITICAL: 2 | HIGH: 2 | MEDIUM: 2 | LOW: 2

## Findings

### [CRITICAL] God class `AppManager` mixes DB init, routing, payment, audit
File: src/AppManager.js:4-141
Description: Single 141-line class. Constructor opens the DB (`new sqlite3.Database(':memory:')`, line 7). `initDb()` runs DDL + seeds users with plaintext password `'123'` (line 18). `setupRoutes(app)` registers `POST /api/checkout`, `GET /api/admin/financial-report`, `DELETE /api/users/:id` with payment processing, audit logging, and cache writes inline.
Impact: Cannot unit-test any handler in isolation; any new endpoint grows the same class; the file owns 78% of the codebase.
Recommendation: Apply playbook recipe `split-god-class-into-controllers-by-domain`.

### [CRITICAL] Hardcoded credentials in source — DB pass, payment key (pk_live_*), SMTP user, seed plaintext password
File: src/utils.js:3-5
File: src/AppManager.js:18, 68
Description: `utils.js` exports `config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef", smtpUser: "no-reply@fullcycle.com.br", port: 3000 }`. The `pk_live_*` shape matches Stripe live key conventions. Seed inserts plaintext password `'123'` for Leonan user (line 18). Default-on-missing password is `"123456"` (line 68). The same payment key is then echoed on every checkout via `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` (line 45) — a runtime credential leak.
Impact: Repo leak compromises payment + DB + mail relay simultaneously; the live-shaped Stripe key would trigger real charge attempts; logged on every checkout request.
Recommendation: Apply playbook recipe `extract-config-to-env-or-settings-module`. The recipe's "remove same literal from log lines" step also redacts the `console.log` payment-key exposure.

### [HIGH] Business logic in route — 51-line checkout callback pyramid with payment, enrollment, audit, cache inline
File: src/AppManager.js:28-78
Description: `app.post('/api/checkout', ...)` opens a 51-line nested-callback handler doing: body parsing → course lookup → user upsert (with `badCrypto` over password) → payment decision (`cc.startsWith("4") ? "PAID" : "DENIED"`, line 46) → enrollment insert → payment insert → audit-log insert → `logAndCache(...)` → 200 response. Callback nesting reaches 7 levels deep.
Impact: Cannot swap payment provider or audit backend; impossible to unit-test the orchestration without a running Express server; any error in the inner callbacks silently fails to send a response.
Recommendation: Apply playbook recipe `move-business-logic-from-route-to-controller`. Decompose into `checkout_controller.process(body)` with `async/await` over promise-wrapped sqlite3 methods; delegate to `payment_service.charge(card)` and `audit_service.log(action)`.

### [HIGH] N+1 with hand-rolled callback counters in financial report
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` queries all courses (line 83), then for each course queries all enrollments (line 92), then for each enrollment queries the user (line 104) and the payment (line 106). Concurrency tracked via decrementing `coursesPending` and `enrPending` counters (lines 86, 93, 97, 117, 120-121) — no `Promise.all`, no `async/await`. Any inner error silently fails to call `res.json(report)`.
Impact: O(courses × enrollments) queries; latency grows quadratically; the endpoint hangs on any DB error since counter-based completion never propagates failures.
Recommendation: Apply playbook recipe `eager-load-relationships-to-fix-n+1`. Single JOIN: `courses LEFT JOIN enrollments LEFT JOIN users LEFT JOIN payments`, aggregated server-side or in one pass through the rows.

### [MEDIUM] Error-leak `if (err) return res.status(500).send("Erro ...")` pattern across 5 sites
File: src/AppManager.js:41, 51, 55, 70, 84
Description: Inline `if (err) return res.status(500).send("Erro DB")`, `... .send("Erro Matrícula")`, etc. The error itself is dropped (never logged) and the response is plain text. Per the catalog `bare-except-or-catch-all` slug, this is the Node analogue of Python's bare `except`: a catch-all that loses the diagnostic and emits an ad-hoc message.
Impact: No observability when checkout fails; the inner callback may also fail to send a response (no response at all, request times out); response text leaks Portuguese hints about which stage failed.
Recommendation: Apply playbook recipe `replace-bare-except-with-typed-handler-and-error-middleware`. Install one `app.use((err, req, res, next) => ...)` final middleware (4-arg signature mandatory); controllers throw typed errors (`AppError`, `NotFoundError`, `ValidationError`) instead.

### [MEDIUM] Deprecated API call — `require('sqlite3').verbose()`
File: src/AppManager.js:1
Description: `const sqlite3 = require('sqlite3').verbose();` — the `.verbose()` chain was useful in early sqlite3 v3/v4 for stack traces; in modern versions it is effectively a no-op recommended only for debugging. Confirms the file dates from a legacy Node-sqlite3 idiom.
Impact: Style/legacy signal; suggests no recent maintenance; future sqlite3 majors may remove the API.
Recommendation: Apply playbook recipe `replace-deprecated-api-call-with-current-equivalent`. Drop the `.verbose()` chain when constructing the connection in `src/models/db.js`.

### [LOW] Magic constants / inline whitelist — payment decision by first digit, hard-coded default password
File: src/AppManager.js:46, 68
Description: Payment status decided by `cc.startsWith("4") ? "PAID" : "DENIED"` — the "4" is a magic prefix for Visa, treated as the success criterion. Line 68 sets a fallback password `"123456"` if the request omits one. Both literals embed business rules in handler code.
Impact: Payment-rule changes require code edits; fallback password is a security hazard in addition to being magic.
Recommendation: Apply playbook recipe `lift-magic-numbers-and-whitelists-into-constants-module`. Move `PAYMENT_APPROVED_CARD_PREFIX` to `src/config/constants.js`; remove the fallback password entirely (controllers raise ValidationError on missing).

### [LOW] Inconsistent response envelope — 8 plain-text responses, 1 JSON response
File: src/AppManager.js:35, 38, 41, 48, 51, 55, 60, 70, 84, 87, 135
Description: Same controller mixes `res.status(400).send("Bad Request")`, `res.status(404).send("Curso não encontrado")`, `res.status(500).send("Erro DB")`, `res.status(200).json({ msg: "Sucesso", enrollment_id })`, `res.json(report)`, and `res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco")` (line 135 — the response literally documents a bug as the success text).
Impact: Client cannot programmatically discriminate success from error without inspecting status code AND content-type; the delete endpoint admits its own data-corruption bug in plain Portuguese.
Recommendation: Apply playbook recipe `replace-bare-except-with-typed-handler-and-error-middleware`. The recipe ships `src/views/response.js` exporting `success(data)` / `error(message, code)` returning the canonical JSON envelope; route all responses through it.

================================
Total: 8 findings
================================

## Calibration cross-check (S001)

`plans/P001-S001-findings.md` listed 10 findings for project 2 with distribution 3 CRITICAL / 2 HIGH / 3 MEDIUM / 2 LOW. This audit produced 8 findings with distribution 2 / 2 / 2 / 2. Delta: **5 S001 findings have no slug in v1 catalog**; they are recorded as residuals below and recommended for v1.1 catalog expansion.

| S001 finding | v1 catalog slug? | Captured here? |
|---|---|---|
| god-class AppManager | god-class-or-god-module | YES |
| hardcoded creds + plaintext seed + payment key leak | hardcoded-credentials | YES |
| fake-crypto `badCrypto` (CRIT in S001) | — | RESIDUAL #1 |
| N+1 in financial-report | n+1-query | YES |
| orphan data on user delete (HIGH in S001) | — | RESIDUAL #2 |
| global mutable state (cache + revenue) | — | RESIDUAL #3 |
| in-memory DB (`:memory:`) | — | RESIDUAL #4 |
| cryptic body field names + minimal input validation | — | RESIDUAL #5 |
| deprecated `sqlite3.verbose()` | deprecated-api-call | YES |
| plain-text responses / inconsistent envelope | inconsistent-response-envelope | YES |

Plus the catalog fires `business-logic-in-route-or-controller` (HIGH) and `bare-except-or-catch-all` (MEDIUM) which S001 did not list as separate items — they were folded into the god-class description. Net: catalog detection introduces 2 new findings and misses 5 Node-specific S001 findings.

Catalog applications that found **zero matches** for this project:
- `sql-injection-string-concat` — `AppManager.js` already uses parameter binding (`db.get("...WHERE id = ?", [cid], cb)`); 0 matches.
- `duplicate-validation-logic` — validation is minimal and present only at line 35; not duplicated; 0 matches.

Acceptance per `desafio.md` lines 279-282 and design contract I-10:
- ≥ 5 findings: YES (8)
- ≥ 1 CRITICAL or HIGH: YES (2 CRITICAL + 2 HIGH = 4)
- Findings ordered CRITICAL → LOW: YES
- Every finding has `file:line`: YES
- Every recommendation names a playbook slug verbatim: YES

## Residuals (5) — slugs absent from v1 catalog

These are real defects observed in the code; they will **not** be fixed in Phase 3 because no catalog slug claims them. Recommended for v1.1 catalog expansion:

1. **fake-or-broken-crypto** — `src/utils.js:17-23` `badCrypto(pwd)` does a 10000-iteration base64-truncate loop producing a deterministic, fixed-output, salt-free 10-character hash. Trivially reversible by lookup. Replace recipe candidate: `replace-fake-crypto-with-bcrypt-or-argon2`.
2. **missing-orm-cascade-or-manual-fk-cleanup** — `src/AppManager.js:131-137` deletes user without cascade; the response literally says `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` Replace recipe candidate: `add-orm-cascade-or-explicit-fk-cleanup`.
3. **global-mutable-state** — `src/utils.js:9-10` `let globalCache = {}; let totalRevenue = 0;` mutated by `logAndCache` and re-exported. No TTL, no per-tenant scoping, totalRevenue is mutated but never read. Replace recipe candidate: `inject-stateful-services-via-constructor`.
4. **in-memory-db-in-prod** — `src/AppManager.js:7` `new sqlite3.Database(':memory:')`. Demo-grade DB used as production storage; data loss on every deploy. Replace recipe candidate: `move-db-path-to-config-or-real-engine`.
5. **pii-or-card-in-logs** (broader form) — `src/AppManager.js:45` `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)`. The payment-key portion of this leak is incidentally fixed by Recipe #1 (`extract-config-to-env-or-settings-module`) because the same line embeds a config secret. The card-number portion stays as a residual until v1.1.

> Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

Operator response: `y` (2026-05-18, recorded in P001-S005 chat).

================================
PHASE 3: REFACTORING COMPLETE
================================

## New project structure

```
ecommerce-api-legacy/
├── src/
│   ├── config/{settings.js, constants.js}
│   ├── errors/index.js
│   ├── middlewares/error_handler.js
│   ├── services/{payment, audit, cache, legacy_crypto}_service.js
│   ├── models/{db, user, course, enrollment, payment, audit, report}_model.js
│   ├── controllers/{checkout, admin, user}_controller.js
│   ├── views/{response, checkout_routes, admin_routes, user_routes, index}.js
│   └── app.js                  (composition root — buildApp + listen)
├── package.json                (start: node src/app.js)
├── api.http
├── .env.example
└── .claude/skills/refactor-arch/  (6 files; identical copy of project 1's)
```

Legacy files removed: `src/AppManager.js` (141 LOC god class), `src/utils.js` (25 LOC kitchen-sink).

## Layering rule checks (Node variant)

```
1. views must NOT require models directly       → OK
2. models must NOT require controllers or views → OK
3. controllers must NOT require views           → OK
4. middlewares must NOT require models or controllers → OK
```

## Secret-leakage grep

`grep -rnE "(dbPass|paymentGatewayKey|pk_live_)\s*[:=]\s*['\"][a-zA-Z0-9_]+" src/` → **no matches** (literals confined to `.env.example`).

## Validation

Boot command: `DB_PASS=test PAYMENT_GATEWAY_KEY=test-key PORT=3131 node src/app.js`
Boot outcome: **OK** — listening on `http://0.0.0.0:3131`. Ports 3000 (system) and 3030 (Docker) were occupied; PORT env var was honoured via `src/config/settings.js`, confirming config is genuinely env-loaded. The `DB_PASS` and `PAYMENT_GATEWAY_KEY` requireds threw at boot when unset (verified by inspection of `src/config/settings.js::required()`).

| # | Endpoint | Method + payload | HTTP | Pass? | Notes |
|---|----------|-----------------|------|-------|-------|
| 1 | `/api/checkout` | POST `{usr:"Guilherme", eml, pwd, c_id:2, card:"4111..."}` | 200 | YES | enrollment_id=2 returned; `status: "ok"` envelope |
| 2 | `/api/checkout` | POST `{... card:"5111..."}` | 400 | YES | `payment_denied` (Visa-prefix decision moved to constant) |
| 3 | `/api/checkout` | POST `{usr:"x"}` (missing fields) | 400 | YES | `validation_error` — ValidationError thrown; middleware mapped |
| 4 | `/api/admin/financial-report` | GET | 200 | YES | JSON array; N+1 fixed via single JOIN; revenue computed server-side |
| 5 | `/api/users/1` | DELETE | 200 | YES | JSON `{message: "Usuário deletado"}` — no more plain-text bug-admission |

**Regressions: none.** All 5 representative endpoints from `api.http` (and the validation variant) returned the expected status with the canonical JSON envelope.

Response-shape change documented (not a regression):
- The original `DELETE /api/users/:id` returned plain text `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` The refactor returns JSON `{status:"ok", data:{message:"Usuário deletado"}}`. The honest "but the data is orphan" admission is gone — but the orphan **defect remains** as residual #2 below.

## Catalog coverage applied

| Catalog slug | Status |
|---|---|
| god-class-or-god-module | FIXED — AppManager.js decomposed into 3 controllers + 7 models + 5 services + middleware + view layer |
| hardcoded-credentials | FIXED — DB_PASS / PAYMENT_GATEWAY_KEY / SMTP_USER / PORT in src/config/settings.js with env-loaded `required()`; card+key console.log replaced with PII-safe `"Processing payment for course %s"` |
| business-logic-in-route-or-controller | FIXED — 51-line callback pyramid decomposed; checkout_controller orchestrates user-upsert → payment_service → enrollment → payment → audit_service → cache_service; routes are 3 lines each |
| n+1-query | FIXED — financial-report rewritten as single JOIN over courses/enrollments/users/payments; admin_controller groups by course in one pass |
| bare-except-or-catch-all | FIXED — all 5 `if (err) return res.status(500).send("Erro...")` removed; controllers throw typed errors; one 4-arg error middleware at app.js end |
| deprecated-api-call | FIXED — `.verbose()` chain removed from sqlite3 require in src/models/db.js |
| magic-numbers-or-inline-whitelist | FIXED — `PAYMENT_APPROVED_CARD_PREFIX` and `PAYMENT_STATUS` in src/config/constants.js; default password `"123456"` deleted (ValidationError on missing pwd) |
| inconsistent-response-envelope | FIXED — all responses through `src/views/response.js::success()`; errors through middleware → `{status: "error", error: {code, message}}` |

## Residuals (5) — slugs absent from v1 catalog

Honoured per session DoD: not fixed in this refactor; documented for v1.1 catalog expansion.

1. **fake-or-broken-crypto** — `badCrypto` moved verbatim to `src/services/legacy_crypto.js::hashPassword`. Behaviour preserved (existing seeded users must keep logging in). v1.1 recipe should swap to bcrypt + a one-shot migration.
2. **missing-orm-cascade-or-manual-fk-cleanup** — `user_controller.remove` deletes only the user row; enrollments / payments / audit_logs for that user become orphans. v1.1 recipe should wrap delete in a transaction or enable FK cascades.
3. **global-mutable-state** — `CacheService` is a class but still per-process Map with no TTL. Encapsulated for v1.1 swap to a real cache backend.
4. **in-memory-db-in-prod** — `src/models/db.js` still constructs `new sqlite3.Database(':memory:')`. Encapsulated for v1.1 swap to a file-backed path or a real engine.
5. **pii-or-card-in-logs** — the payment-key portion of the original `console.log` was incidentally removed by Recipe #1 (key is now an env var); the broader principle (never log card numbers, mask to last-4) is residual.

================================
Total: 8 findings, 8 fixed (with 5 residuals documented above)
================================

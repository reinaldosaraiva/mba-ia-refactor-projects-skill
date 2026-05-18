# P001-S005 — Execute /refactor-arch on ecommerce-api-legacy

## Zero-context bootstrap

If resuming with no prior conversation:

1. Read `plans/CURRENT.md`, `plans/P001-skill-refactor-arch.md`, `plans/P001-design-contract.md` — focus on **I-1** (cross-stack agnosticism is on test here), **I-4** (Phase-2 gate), **I-5** (boot + smoke), **I-10** (≥ 5 findings + ≥ 1 CRIT/HIGH).
2. Read the six skill files under `code-smells-project/.claude/skills/refactor-arch/` (source of truth — copy lives at this path; S005 step 1 replicates it into the project under audit).
3. Read `plans/P001-S004-results.md` for the operating pattern. S005 follows the same two-part split.
4. Read `plans/P001-S001-findings.md` (ecommerce-api-legacy block, 10 findings) — used only for Phase-2 calibration cross-check after the audit produces its own report.
5. Skim `desafio.md` lines 156-162 (project-2 checklist).
6. Execute the tasks below. **Stop after Phase 2** and wait for explicit user `y` before Phase 3.

## Goal

Execute `/refactor-arch` against `ecommerce-api-legacy/` (Node.js + Express, 3 source files in `src/`, ~180 LOC). Three outcomes:

1. Skill tree is replicated from `code-smells-project/.claude/skills/refactor-arch/` into `ecommerce-api-legacy/.claude/skills/refactor-arch/` (per `desafio.md` line 159).
2. Phase 1 prints the canonical summary; Phase 2 writes `reports/audit-project-2.md` and halts on the verbatim prompt.
3. After explicit `y`, Phase 3 reshapes `ecommerce-api-legacy/src/` into the MVC layout from `guidelines-arquitetura.md`, boots the app, smoke-tests every original endpoint from `api.http`, and records the validation block.

Verdict: PASS (delivery round).

## Operating mode

Same as S004:

- The agent **is** the skill's runtime.
- Treat SKILL.md as the prompt; do not improvise heuristics or recipes that contradict the reference files.
- Phase-2 halt is enforced literally: surface the prompt `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` and end the turn. No self-approval.

## Prerequisite reads (only these)

| Path | Why |
|------|-----|
| `code-smells-project/.claude/skills/refactor-arch/SKILL.md` (and the 5 siblings) | The runtime prompt + knowledge base |
| `ecommerce-api-legacy/src/app.js` | Composition site (14 LOC) — where Express is built |
| `ecommerce-api-legacy/src/AppManager.js` | God class (141 LOC) — primary target for split |
| `ecommerce-api-legacy/src/utils.js` | Kitchen-sink config + cache + fake crypto (25 LOC) |
| `ecommerce-api-legacy/api.http` | Endpoint catalogue — sets smoke-test surface |
| `ecommerce-api-legacy/package.json` | Dependency list and start script |

Do not read more than this during Phase 2; over-reading inflates context for the heaviest turn (Phase 3).

## Tasks — preamble (step 0)

0. **Copy the skill tree** into the target project:
   ```bash
   cp -R code-smells-project/.claude ecommerce-api-legacy/.claude
   ls ecommerce-api-legacy/.claude/skills/refactor-arch/
   ```
   Expected: 6 files (SKILL.md, catalog-antipatterns.md, playbook-refactor.md, analise-projeto.md, template-relatorio.md, guidelines-arquitetura.md). The two projects must share the **exact same** skill tree — diff them after the copy.

## Tasks — Phase 1 (analysis)

1. Apply `analise-projeto.md` heuristics. Expected output (subject to verification):
   - `Language: javascript`
   - `Framework: nodejs-express (Express ~4.x)`
   - `Dependencies: express, sqlite3`
   - `Domain: LMS API (users, courses, enrollments, payments, audit_logs) with checkout + financial-report + user-delete flows`
   - `Architecture: flat — 3 source files in src/, no layer folders`
   - `Source files: 3`
   - `DB tables: users, courses, enrollments, payments, audit_logs`
2. Print the summary block. Continue without halting.

## Tasks — Phase 2 (audit)

3. Iterate `catalog-antipatterns.md`. Apply entries tagged `any`, `nodejs-express`, or `nodejs-generic`.
4. **Stack filter caveat:** the v1 catalog has 10 entries; only **8** apply to project 2's code:
   - god-class-or-god-module (CRITICAL) → `AppManager.js`
   - hardcoded-credentials (CRITICAL) → `utils.js` config + `AppManager.js:18, 68`
   - business-logic-in-route-or-controller (HIGH) → 50-line checkout callback pyramid
   - n+1-query (HIGH) → financial-report nested callbacks with manual counters
   - bare-except-or-catch-all (MEDIUM) → `if (err) return res.status(500).send("Erro DB")` pattern
   - deprecated-api-call (MEDIUM) → `require('sqlite3').verbose()`
   - magic-numbers-or-inline-whitelist (LOW) → `cc.startsWith("4")` payment decision; default password `"123456"`
   - inconsistent-response-envelope (LOW) → `res.send("text")` vs `res.json({...})` mix
   
   `sql-injection-string-concat` finds **no matches** in project 2: `AppManager.js` uses parameter-bound queries (`db.get("...WHERE id = ?", [cid], ...)`) consistently. Catalog correctly fires zero times — record this in the report's Calibration block.
   
   `duplicate-validation-logic` also finds no matches: the validation is minimal and not duplicated. Acceptable.
5. Build findings using the schema in `template-relatorio.md` (heading + `File:` + `Description:` + `Impact:` + `Recommendation: Apply playbook recipe \`<slug>\`.`). Sort CRIT → LOW.
6. Write `reports/audit-project-2.md`. Header: `Project: ecommerce-api-legacy`, `Stack: Node.js + Express`, `Files: 3 analyzed | ~180 lines of code`.
7. **Calibration cross-check** against `plans/P001-S001-findings.md` (target: 10 findings, distribution 3/2/3/2). Delta: this audit will produce 8 findings (3/2/2/1) because the v1 catalog lacks slugs for:
   - `fake-or-broken-crypto` — `utils.js::badCrypto` and the `Buffer.from(...).toString('base64')` loop
   - `pii-or-card-in-logs` — `console.log(\`Processando cartão ${cc} ...\`)`
   - `missing-orm-cascade-or-manual-fk-cleanup` — `DELETE FROM users` leaving orphan enrollments/payments
   - `global-mutable-state` — `utils.js` `globalCache`, `totalRevenue`
   - `in-memory-db-in-prod` — `sqlite3.Database(':memory:')`
   These five S001 findings become **residuals**, documented at the bottom of the report. The catalog v1.1 should add them. Note that the project still passes acceptance (≥ 5 findings with ≥ 1 CRIT/HIGH) — 8 ≥ 5 and 3 CRIT + 2 HIGH = 5 ≥ 1.
8. Print the report to stdout.
9. Surface the verbatim halt prompt as the **last line** of the turn. End the turn.

## Tasks — Phase 3 (refactor + validate)

Execute only on explicit user `y`.

10. Apply playbook recipes in this order (risk-graded):
    1. `extract-config-to-env-or-settings-module` — move `dbPass`, `paymentGatewayKey`, `smtpUser`, `port` into `src/config/settings.js` reading from `process.env`. Add `.env.example`. **As part of this recipe**, also redact the credit-card `console.log` in the checkout handler — it was logging the live payment key alongside the card, so the same line is a config-secret leak in addition to PII. Replace with `console.log("Processing payment for course %s", cid)`.
    2. `replace-deprecated-api-call-with-current-equivalent` — drop `.verbose()` from `require('sqlite3')`. Move the require into `src/models/db.js`.
    3. `split-god-class-into-controllers-by-domain` — decompose `AppManager.js` into:
       - `src/models/{user,course,enrollment,payment,audit}_model.js` (one per table; promise-wrapped sqlite3)
       - `src/controllers/{checkout,admin,user}_controller.js`
       - `src/views/{checkout,admin,user}_routes.js` (Express Routers)
       - `src/services/{payment,audit,cache}_service.js`
       - `src/middlewares/error_handler.js`
       - `src/errors/index.js`
       - `src/views/response.js`
    4. `eager-load-relationships-to-fix-n+1` — rewrite `/api/admin/financial-report` as **one JOIN** (`courses LEFT JOIN enrollments LEFT JOIN users LEFT JOIN payments`), grouped server-side by course. Drop the hand-rolled `coursesPending`/`enrPending` counters.
    5. `move-business-logic-from-route-to-controller` — the 50-line checkout handler becomes:
       - route: parse body → call `checkout_controller.process(req.body)` → wrap in `success()`
       - controller: orchestrates user-upsert → payment via `payment_service.charge(card)` → enrollment insert → payment insert → audit via `audit_service.log()` → returns enrollment id
       - Use `async/await` with `util.promisify` over the sqlite3 callbacks (or write a minimal `dbAll`/`dbGet`/`dbRun` wrapper in `src/models/db.js`).
    6. `replace-bare-except-with-typed-handler-and-error-middleware` — install `src/middlewares/error_handler.js` as the **last** `app.use(...)` in `app.js` (Express requires the 4-arg error-middleware signature). Remove per-route `if (err) return res.status(...).send("...")` blocks; controllers throw typed errors instead. Every success response goes through `src/views/response.js::success()`.
    7. `lift-magic-numbers-and-whitelists-into-constants-module` — `src/config/constants.js`:
       - `PAYMENT_APPROVED_CARD_PREFIX = "4"` (replace `cc.startsWith("4")`)
       - `DEFAULT_PASSWORD` removed entirely (force callers to supply one; raise ValidationError if missing)
       - `PAYMENT_STATUS = { PAID: "PAID", DENIED: "DENIED" }`
11. **Do NOT fix the 5 residuals** (fake-crypto, card-in-logs as a separate concern, orphaned data, global cache, in-memory DB) — they are out of v1 catalog scope. The card-in-logs **is** partially addressed by recipe #1 above (removing the literal payment key from the log line); the broader PII-redaction recipe is residual.
12. Reshape `app.js` to a composition root: import `settings` → build `express()` → `app.use(express.json())` → mount routers from `src/views/` → `app.use(error_handler)` last → `app.listen(settings.PORT)`. No business logic.
13. Update `package.json` if a `start` script is missing: `"start": "node app.js"`.
14. Run the layering-rule grep checks from `guidelines-arquitetura.md` (Node variants: `from src/` becomes `require('./src/`). Fix any violation before continuing.
15. Boot. Command: `cd ecommerce-api-legacy && DB_PASS=test PAYMENT_GATEWAY_KEY=test-key PORT=3030 node app.js` (default port 3000 may also be free; the env var pattern proves config is genuinely env-loaded).
16. Smoke-test from `api.http` plus deletions:
    - `POST /api/checkout` with card `4111222233334444` → expect 200 (status PAID)
    - `POST /api/checkout` with card `5111222233334444` → expect 400 (status DENIED)
    - `POST /api/checkout` with missing fields → expect 400 (ValidationError)
    - `GET /api/admin/financial-report` → expect 200, response is a JSON array of `{course, revenue, students}` objects
    - `DELETE /api/users/1` → expect 200 (the response is now JSON, no longer plain text that admits leaving orphan data)
17. Append a `## Validation` section to `reports/audit-project-2.md` (boot command + outcome + endpoint table + regressions/residuals).
18. If any endpoint regresses, revert the breaking change and re-run before completion.

## Tasks — closeout

19. Write `plans/P001-S005-results.md` with **Verdict:** PASS, including Phase 1 block, Phase 2 finding counts, Phase 3 endpoint table, residual list, commit hash (pending then filled).
20. Update `plans/INDEX.md`: S005 → `done | PASS`, S006 → `authorable`.
21. Update `plans/CURRENT.md`.
22. Clear `plans/LOCKS.json`.
23. Two-commit pattern.

## Definition of done

- `ecommerce-api-legacy/.claude/skills/refactor-arch/` is a verbatim copy of `code-smells-project/.claude/skills/refactor-arch/` (6 files).
- `reports/audit-project-2.md` exists; severity tally ≥ 5 with ≥ 1 CRIT/HIGH; calibration block documents the 5 residuals.
- Phase-2 halt surfaced literally; user `y` recorded before Phase 3.
- `ecommerce-api-legacy/src/{config,models,views,controllers,services,middlewares}` all exist with at least one populated file each; legacy `src/AppManager.js` and `src/utils.js` deleted.
- Layering grep checks pass (Node variants).
- App boots with `node app.js` (after exporting `DB_PASS`, `PAYMENT_GATEWAY_KEY`); 0 regressions on the 5 smoke calls.
- Plan files updated; lock cleared; two-commit pattern landed.

## Out of scope

- Catalog/playbook edits — frozen for execution sessions; v1.1 expansion (residuals → catalog) is a follow-up workstream.
- Fixing fake-crypto, orphaned-data, in-memory-DB, global-cache — they are residuals, not v1 catalog entries.
- Tests beyond smoke calls.

## Risks specific to this session

- **Skill agnosticism on real trial.** v1 catalog is Python-leaning; 5 Node-specific S001 findings have no catalog slug. The session passes anyway (8 findings ≥ 5, 3 CRIT + 2 HIGH ≥ 1), but the report must document the residuals so the v1.1 catalog expansion is data-driven.
- **Promise-wrapping sqlite3.** sqlite3's `db.run` returns the row id via `function() { this.lastID }`, which conflicts with arrow functions. Use a named function in the wrapper. Mitigation: `src/models/db.js` exposes `dbRun(sql, params)` returning a Promise that resolves to `{ lastID, changes }`.
- **Express error-middleware signature.** Express identifies error-handling middleware by **4-argument signature** `(err, req, res, next)`. A 3-argument middleware will not catch thrown errors. Mitigation: explicitly use 4 args in `error_handler.js`.
- **`:memory:` DB persistence.** The original uses `sqlite3.Database(':memory:')`. The refactor keeps that for v1 (in-memory-db is a residual). Consequence: every restart re-seeds; smoke tests must be deterministic about which user/course IDs exist after seed.
- **`/api/users/:id` response shape change.** The original returned plain text confessing the orphan bug. The refactor returns JSON `{ message: "Usuário deletado" }`. Clients depending on the exact text break. Acceptable change — the brief allows it and the response is now safer; document in the validation block.
- **Default port collision.** Default 3000 may be taken (Node ecosystem). Use 3030. Validates config-is-env-loaded.

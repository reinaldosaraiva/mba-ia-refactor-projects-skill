---
total: 10
critical: 3
high: 2
medium: 3
low: 2
deprecated_api_entries: 1
stacks_covered: [python-flask, python-generic, nodejs-express, nodejs-generic]
schema_version: 1
---

# Anti-pattern catalog

Knowledge base consulted by the `/refactor-arch` skill during Phase 2 (audit). Every entry follows the same shape so the audit engine can grep stable field names. Stacks are tagged per entry; `any` means signals apply regardless of language.

Severity scale per `desafio.md` lines 20-23:

| Severity | Meaning |
|----------|---------|
| CRITICAL | Architecture or security failure: hardcoded secrets, SQL injection, god-modules mixing data layer with routing and logic. |
| HIGH | Strong MVC/SOLID violations that block testing or refactoring: business logic stuck in routes, tight coupling, global mutable state. |
| MEDIUM | Standardisation, duplication, moderate perf issues: N+1 queries, missing middleware, validations absent on routes. |
| LOW | Readability, naming, magic numbers. |

---

## god-class-or-god-module

- **Severity:** CRITICAL
- **Stacks:** any
- **What it is:** A single file or class that owns multiple concerns across multiple domains — typically DB access, request parsing, business rules, formatting, and routing — for more than one domain entity at once.
- **Why it matters:** Impossible to test in isolation; every change risks breaking unrelated features; the file becomes a merge-conflict magnet and a knowledge bottleneck.
- **Detection signals:**
  - any: source file > 200 LOC that combines ≥ 2 of {HTTP handlers, SQL/ORM calls, validation, formatting, notification} for ≥ 2 domain entities.
  - any: a class named `*Manager`, `*Handler`, `*Service` with > 10 public methods spanning multiple unrelated responsibilities.
  - python-flask, python-generic: a `controllers.py` (or equivalent) that imports `request`, `models`, and `database` AND defines handlers for more than one resource.
  - nodejs-express: a class whose constructor opens a DB connection AND whose `setupRoutes(app)` method registers endpoints for multiple resources.
- **Example from analysis:** `code-smells-project/controllers.py:1-292` (17 handlers across produtos/usuarios/pedidos/login/relatórios/health, includes `print()`-as-notification on lines 208-210); `ecommerce-api-legacy/src/AppManager.js:4-141` (constructor opens DB, `setupRoutes` registers checkout/report/delete-user with payment processing inline).
- **Linked playbook:** `split-god-class-into-controllers-by-domain`

## hardcoded-credentials

- **Severity:** CRITICAL
- **Stacks:** any
- **What it is:** Secrets (passwords, signing keys, API tokens, SMTP credentials, payment-provider keys) committed as literal strings in source code instead of read from environment variables or a secrets manager.
- **Why it matters:** Source-tree access becomes full credential compromise; rotating leaked secrets requires patching code and redeploying instead of swapping an env var; signing keys in source enable session forgery.
- **Detection signals:**
  - any: regex `(SECRET_KEY|API_KEY|SECRET|PASSWORD|PASSWD|TOKEN)\s*[=:]\s*['"][^'"]{4,}['"]` matched outside `*test*`, `*example*`, `.env*`, or a config module that documents itself as env-loaded.
  - any: provider-key shape strings — `pk_live_`, `sk_live_`, `AKIA[0-9A-Z]{16}`, `xoxb-`, `ghp_`.
  - python-flask, python-generic: `app.config['SECRET_KEY'] = '<literal>'`; `email_password = '<literal>'`; `password='<literal>'` in `smtplib.SMTP_SSL.login(...)`.
  - nodejs-express, nodejs-generic: `const config = { ..., (dbPass|paymentGatewayKey|smtpPass): '<literal>' }`; literal cred strings passed to `new Client(...)`, `mailer.createTransport(...)`.
- **Example from analysis:** `code-smells-project/app.py:7` (`SECRET_KEY = "minha-chave-super-secreta-123"`) and re-leaked in `controllers.py:289` via `/health`; `ecommerce-api-legacy/src/utils.js:1-7` (`dbPass`, `paymentGatewayKey: "pk_live_..."`); `task-manager-api/services/notification_service.py:10-11` (`email_password='senha123'`).
- **Linked playbook:** `extract-config-to-env-or-settings-module`

## sql-injection-string-concat

- **Severity:** CRITICAL
- **Stacks:** python-flask, python-generic, nodejs-express, nodejs-generic
- **What it is:** SQL queries built by concatenating or interpolating request-derived data into a query string instead of using parameter placeholders bound by the driver.
- **Why it matters:** Authentication bypass, full data read/write, secondary RCE in some drivers. Trivially exploitable when login or search endpoints concatenate user input. Endpoints that `execute()` arbitrary SQL from the request body are an even worse variant.
- **Detection signals:**
  - python-flask, python-generic: regex `cursor\.execute\s*\(\s*["'].*\+`, `cursor\.execute\s*\(\s*f["']`, `cursor\.execute\s*\(\s*["'].*%\s*\(.*\)\s*\)`.
  - python-flask, python-generic: any usage of `request.get_json()` or `request.args` fields concatenated into a SQL string in the same function.
  - nodejs-express, nodejs-generic: regex `db\.(run|get|all|exec)\s*\(\s*["'].*\+`, `db\.(run|get|all|exec)\s*\(\s*\`.*\$\{` (template literal interpolation).
  - any: routes named `/admin/query`, `/admin/sql`, `/debug/exec` accepting JSON `{sql: ...}` and feeding it to a DB driver.
- **Example from analysis:** `code-smells-project/models.py:28, 47-49, 109-110` (every query concatenates `id`/`nome`/`email`/`senha`); `code-smells-project/app.py:59-78` (`/admin/query` executes JSON-supplied SQL verbatim).
- **Linked playbook:** `replace-raw-sql-with-parameterised-queries`

## business-logic-in-route-or-controller

- **Severity:** HIGH
- **Stacks:** any
- **What it is:** HTTP handler functions that compute business rules, dispatch side effects (emails, notifications, audit), or aggregate domain statistics directly, instead of delegating to a controllers or services layer.
- **Why it matters:** Cannot unit-test rules without spinning up an HTTP server; the same logic gets duplicated across endpoints (create vs update vs admin variants) and drifts; swapping the transport (HTTP → CLI → queue worker) requires rewriting everything.
- **Detection signals:**
  - any: route handler function > 40 LOC.
  - any: route handler that reads from one model and *also* writes to another *and* dispatches a notification — three responsibilities.
  - any: business calculation (pricing, discount tiers, status transitions, aggregations) inside the handler body, with no controllers/services module in the project tree.
  - any: `print("ENVIANDO EMAIL:")`, `console.log("Sending")`, or any side-effect notification implemented as a log line inside a handler.
- **Example from analysis:** `code-smells-project/controllers.py:208-210` (notifications as `print()` inside `criar_pedido`); `code-smells-project/models.py:256-262` (discount tier rules inside `relatorio_vendas`); `task-manager-api/routes/report_routes.py:13-101` (89-line `summary_report` doing 6 aggregations inline).
- **Linked playbook:** `move-business-logic-from-route-to-controller`

## n+1-query

- **Severity:** HIGH
- **Stacks:** any
- **What it is:** A pattern where an initial query returns N rows and the code then issues one or more follow-up queries per row, multiplying DB round-trips with the collection size.
- **Why it matters:** Endpoint latency grows linearly (or worse) with row count; under load the DB connection pool saturates and unrelated traffic stalls. Especially severe on shared-storage engines like SQLite.
- **Detection signals:**
  - python-flask: `Model.query.all()` followed in the same function by `OtherModel.query.get(...)` or `OtherModel.query.filter_by(...)` inside a `for` loop.
  - python-flask: SQLAlchemy session usage without `joinedload`, `selectinload`, or an explicit `.options(...)` clause where relationships are accessed.
  - python-generic: raw SQL inside a `for row in rows:` body.
  - nodejs-express, nodejs-generic: nested `db.get`/`db.all` callbacks where the outer callback iterates an array; manual `pending--` counters mimicking `Promise.all`.
- **Example from analysis:** `code-smells-project/models.py:171-201` (per-pedido cursor for itens, per-item cursor for produto name = O(P × I) queries); `task-manager-api/routes/task_routes.py:14-59` (per-task User and Category fetches); `ecommerce-api-legacy/src/AppManager.js:80-129` (3-level nested callbacks with hand-rolled completion counters).
- **Linked playbook:** `eager-load-relationships-to-fix-n+1`

## bare-except-or-catch-all

- **Severity:** MEDIUM
- **Stacks:** any
- **What it is:** Exception handlers that catch everything indiscriminately, either with no exception class (`except:`), or with `Exception`/`Error` and no logging, or empty Node `catch` blocks. Tracebacks are swallowed; clients receive either nothing or the raw error message string.
- **Why it matters:** Hides real failure modes; turns programming bugs into HTTP 500s with no observability; raw `str(e)` leaked to clients exposes table names and query structure, helping attackers.
- **Detection signals:**
  - python-flask, python-generic: regex `^\s*except\s*:\s*$`; `except\s+Exception\s+as\s+\w+\s*:` followed within 3 lines by `return.*str\(e\)` or `return.*\{['"]error['"].*str\(e\)`.
  - python-flask: every HTTP handler wrapped in `try: ... except Exception as e: return jsonify({"erro": str(e)}), 500`.
  - nodejs-express, nodejs-generic: regex `catch\s*\(\s*\w*\s*\)\s*\{\s*\}` (empty catch); `.catch\s*\(\s*\(?\w*\)?\s*=>\s*\{?\s*\}?\s*\)` (no-op promise catch).
  - any: absence of a single application-level error handler (`@app.errorhandler(Exception)` for Flask, `app.use(errorHandler)` middleware for Express).
- **Example from analysis:** `code-smells-project/controllers.py:10-12, 21-22, 60-62` and 14 other route blocks; `task-manager-api/routes/task_routes.py:62-63, 137-138, 204-205, 236-238`; `task-manager-api/routes/report_routes.py:186-188, 207-209, 221-223`.
- **Linked playbook:** `replace-bare-except-with-typed-handler-and-error-middleware`

## duplicate-validation-logic

- **Severity:** MEDIUM
- **Stacks:** any
- **What it is:** The same validation rules (length checks, whitelist membership, regex, presence) repeated across multiple route handlers — typically POST (create) and PUT (update) for the same resource — without being shared. Sometimes coexists with a dead validator module that nobody imports.
- **Why it matters:** Rules drift between copies (update path forgets a check that create has, or vice versa), creating silent business-rule bugs; fixing a validation requires editing N places and missing one is invisible until a customer hits it.
- **Detection signals:**
  - any: two route handlers for the same resource (POST and PUT) whose first half is a near-identical block of `if not data['field']` / `if len(field) < N` / `if field not in [...]`.
  - any: presence of a `validate*.py`, `*_validator.py`, `*_schema.py`, `*_helpers.py::process_*_data` module that defines validation but is not imported by any route file.
  - any: no schema library (`marshmallow`, `pydantic`, `zod`, `joi`, `express-validator`) in `requirements.txt` / `package.json` despite the project having user input.
- **Example from analysis:** `code-smells-project/controllers.py:30-54` vs `72-91` (produto create vs update — update silently drops the category-whitelist check); `task-manager-api/routes/task_routes.py:92-144` vs `166-213` (drift on `len(title) < 3` between create and update); `task-manager-api/utils/helpers.py:57-108` (dead `process_task_data` validator never imported).
- **Linked playbook:** `move-business-logic-from-route-to-controller`

## deprecated-api-call

- **Severity:** MEDIUM
- **Stacks:** any
- **What it is:** Use of a language/library API that has been deprecated, scheduled for removal, or replaced by a safer/faster equivalent. Includes both library-level deprecations and language-level patterns that have been superseded.
- **Why it matters:** Future runtime upgrades break the app; security advisories on the deprecated API go unpatched; some deprecated APIs ship with worse defaults (no TLS verification, weak crypto modes); CI lint warnings accumulate and get ignored. Detection of this anti-pattern is **explicitly required** by `desafio.md` line 144.
- **Detection signals:**
  - python-flask: `@app.before_first_request` (removed in Flask 2.3+, replaced by startup hooks under `with app.app_context()`); `flask.escape` (use `markupsafe.escape`); `flask._app_ctx_stack` (use `flask.globals`).
  - python-generic: `datetime.utcnow()` (deprecated in 3.12 in favour of `datetime.now(datetime.UTC)`); `crypt`, `imp`, `cgi`, `pipes`, `nis`, `audioop` modules (PEP 594 removal queue); `urllib.request.urlopen` without explicit context.
  - python-sqlalchemy: `Query.get(id)` (replaced by `db.session.get(Model, id)` in SQLAlchemy 2.x); implicit query construction without explicit `select(...)`.
  - nodejs-express, nodejs-generic: `require('sqlite3').verbose()` (no-op in modern sqlite3, signals legacy code); `new Buffer(x)` (use `Buffer.from(x)`); `crypto.createCipher`/`createDecipher` (use `createCipheriv`/`createDecipheriv`); `body-parser` direct require (built into Express ≥ 4.16 via `express.json()`/`express.urlencoded()`); `url.parse` (use `new URL(...)`); `fs.exists` (use `fs.access` or `fs.stat`).
- **Example from analysis:** `ecommerce-api-legacy/src/AppManager.js:1` (`require('sqlite3').verbose()` — confirms legacy code path).
- **Linked playbook:** `replace-deprecated-api-call-with-current-equivalent`

## magic-numbers-or-inline-whitelist

- **Severity:** LOW
- **Stacks:** any
- **What it is:** Numeric literals in conditionals (`if x > 200`, `if priority < 1 or priority > 5`) or inline list/array literals (`if status in ['pending', 'done', 'cancelled']`) embedded in routes/controllers, instead of named constants centralised in a config module. A worse variant: constants exist in a utility module but are not imported by the code that needs them.
- **Why it matters:** Business rules invisible to readers; cannot change a threshold per environment; constant drift between routes (POST allows status `X`, PUT silently rejects it); dead constants modules accumulate.
- **Detection signals:**
  - any: numeric literals other than `0`, `1`, `-1`, `2` in comparison expressions inside route or controller files.
  - any: inline list/array literals of strings in `if x in [...]` / `if (![...].includes(x))` validation.
  - any: a `constants.py` / `constants.js` / `enums.py` / `utils/helpers.py::*_CONSTANTS` exists in the tree but is not imported by routes/controllers.
- **Example from analysis:** `code-smells-project/controllers.py:47-50` (`< 2`, `> 200`), `:52` (`categorias_validas = [...]`), `:242` (status whitelist); `code-smells-project/models.py:257-262` (discount thresholds 10000/5000/1000); `task-manager-api/routes/task_routes.py:110-113` (status list, `< 1 or > 5`) while `task-manager-api/utils/helpers.py:110-116` already defines `VALID_STATUSES`, `MAX_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY` but routes don't import them.
- **Linked playbook:** `lift-magic-numbers-and-whitelists-into-constants-module`

## inconsistent-response-envelope

- **Severity:** LOW
- **Stacks:** any
- **What it is:** HTTP responses from the same API use multiple unrelated shapes: sometimes `{"dados": ..., "sucesso": true}`, sometimes a bare array, sometimes `{"error": "..."}`, sometimes plain text. No envelope contract.
- **Why it matters:** Client code cannot programmatically discriminate success from error without inspecting HTTP status; type-safe consumers (TypeScript, mobile SDKs) drift; tests duplicate response-shape assertions in every test case.
- **Detection signals:**
  - any: same route file mixes `jsonify(dict)` / `jsonify(list)` / `jsonify({"erro": ...})` / `res.send("text")` / `res.json({...})` without a single response helper module.
  - any: absence of a `response.py` / `responses.js` / `envelope.ts` module exporting `success(data, message=None)` and `error(message, code)`.
  - any: clients in the same repo writing `data.dados` for one route and `data` for another and `data.error` for failures — sign of envelope drift.
- **Example from analysis:** `code-smells-project/controllers.py` — line 9 `{"dados": produtos, "sucesso": True}`, line 124 adds `"total"`, line 132 `{"dados": usuarios, "sucesso": True}`, line 252 `{"sucesso": True, "mensagem": "Status atualizado"}` (no `dados`), errors are `{"erro": ...}` (no `sucesso`); `ecommerce-api-legacy/src/AppManager.js:35-38` (text via `res.send`) vs `:60` (`res.status(200).json(...)`).
- **Linked playbook:** `replace-bare-except-with-typed-handler-and-error-middleware`

---

### Catalog↔playbook coverage matrix

| Catalog slug | Linked playbook |
|---|---|
| god-class-or-god-module | split-god-class-into-controllers-by-domain |
| hardcoded-credentials | extract-config-to-env-or-settings-module |
| sql-injection-string-concat | replace-raw-sql-with-parameterised-queries |
| business-logic-in-route-or-controller | move-business-logic-from-route-to-controller |
| n+1-query | eager-load-relationships-to-fix-n+1 |
| bare-except-or-catch-all | replace-bare-except-with-typed-handler-and-error-middleware |
| duplicate-validation-logic | move-business-logic-from-route-to-controller |
| deprecated-api-call | replace-deprecated-api-call-with-current-equivalent |
| magic-numbers-or-inline-whitelist | lift-magic-numbers-and-whitelists-into-constants-module |
| inconsistent-response-envelope | replace-bare-except-with-typed-handler-and-error-middleware |

Every catalog entry has at least one linked playbook recipe; every playbook recipe is the target of at least one catalog entry. The inverse direction is verified in `playbook-refactor.md` via the `Fixes catalog entries:` field on each recipe.

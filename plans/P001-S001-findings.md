# P001-S001 — Findings dossier

Ground-truth manual analysis of the 3 legacy projects. Used by S002 (catalog/playbook) and S007 (README "Análise Manual"). Severity scale per `desafio.md` lines 20-23.

---

## code-smells-project — Python + Flask 3.x

Stack: Flask 3.x + flask-cors + raw `sqlite3` (no ORM). 4 source files, 780 LOC.
Domain: E-commerce API (produtos, usuarios, pedidos, itens_pedido, relatórios de vendas).
Architecture: monolítica flat — `app.py` (entry+admin endpoints), `controllers.py` (17 funcs), `models.py` (data access via raw SQL), `database.py` (singleton connection + schema DDL + seed).

### [CRITICAL] SQL Injection via string concatenation across the entire data layer
File: `models.py:28, 47-49, 57-60, 68, 92, 109-110, 126-128, 140, 148-150, 155, 157-159, 163-165, 174, 188, 192, 220, 224, 279-280, 289-297`
Description: 100% of queries are built by Python string concatenation/interpolation with request data. Examples: login query `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (line 109-110); produto search uses LIKE with raw `termo` (line 291). Plus `app.py:59-78` exposes `/admin/query` which `cursor.execute(query)` on arbitrary JSON-supplied SQL.
Impact: Authentication bypass, full DB read/write, RCE-adjacent via admin endpoint. The most dangerous finding in the workstream.
Recommendation: Replace every `cursor.execute(<concat>)` with parameterised `cursor.execute(<sql>, (params,))`; delete `/admin/query`; move queries into a repository layer in `src/models/`.

### [CRITICAL] Hardcoded credentials, debug-enabled prod, secret leaked via /health
File: `app.py:7-8, 88; controllers.py:289; database.py:31, 76-79`
Description: `SECRET_KEY = "minha-chave-super-secreta-123"` committed to source. `DEBUG=True` set in both `app.config["DEBUG"]` and `app.run(debug=True)`. `/health` endpoint *returns the secret in the JSON response*. Seed creates admin user with plaintext `"admin123"` and stores raw passwords in `usuarios.senha` column.
Impact: Source-tree theft = full session forgery + DB takeover; debug mode enables Werkzeug RCE via the interactive debugger PIN; plaintext passwords trivially leakable.
Recommendation: Extract `SECRET_KEY`, `DEBUG`, `DB_PATH` into a `src/config/settings.py` loading from env; drop secret from `/health`; hash passwords with bcrypt or argon2 at the model layer.

### [CRITICAL] God class `controllers.py` mixing 4 domains plus side effects
File: `controllers.py:1-292`
Description: One 292-line file holds 17 handler functions for produtos, usuarios, pedidos, login, relatórios, and health. Each handler does parsing + validation + business logic + side-effect notification (lines 208-210 print "ENVIANDO EMAIL/SMS/PUSH" as the implementation), logging (line 8, 11, 57, 106, etc.), and response formatting. Plus `app.py:47-78` adds two unauth admin endpoints (`/admin/reset-db`, `/admin/query`).
Impact: Impossible to test in isolation, any change in one domain risks breaking others, admin endpoints are attack surface.
Recommendation: Split into `src/controllers/produto_controller.py`, `usuario_controller.py`, `pedido_controller.py`, `relatorio_controller.py`; remove admin endpoints; extract notifications to `src/services/notification_service.py`.

### [CRITICAL] Module-level mutable global DB connection shared across threads
File: `database.py:4, 9-10`
Description: Module global `db_connection = None`, lazily opened with `sqlite3.connect(db_path, check_same_thread=False)`. Same connection object served to every request handler. Flask debug server forks workers — concurrent writes corrupt WAL. Connection never closed, no pool, schema DDL re-runs on every cold start inside `get_db()`.
Impact: Race conditions under any concurrency; transactional bugs (commits crossing requests); cannot be safely deployed behind gunicorn with workers > 1.
Recommendation: Use Flask's `app.teardown_appcontext` + per-request connection (or migrate to SQLAlchemy); move DDL into a startup hook or migration script; remove `check_same_thread=False`.

### [HIGH] N+1 queries when listing pedidos
File: `models.py:171-201, 203-233`
Description: `get_pedidos_usuario(usuario_id)` runs one query for pedidos, then per pedido one query for itens, then **per item one query for the produto name**. Same pattern in `get_todos_pedidos()`. With 100 pedidos × 5 items each = 500+ queries for one HTTP request.
Impact: Endpoint latency grows linearly with order volume; SQLite global lock amplifies it.
Recommendation: Single JOIN across pedidos × itens_pedido × produtos, or eager-load with a CTE; surface as `src/repositories/pedido_repository.py` method.

### [HIGH] Business logic in controllers (notifications, discount tiers, status whitelist)
File: `controllers.py:208-210, 247-250; models.py:256-262`
Description: Pedido-created notification is `print("ENVIANDO EMAIL: ...")` in `criar_pedido` (lines 208-210). Status-changed notification is `print(...)` inside `atualizar_status_pedido` (lines 248-250). Status whitelist hardcoded as inline list (line 242). Discount tier rules live inside `models.relatorio_vendas` (`if faturamento > 10000 ...` lines 257-262) — pure business policy embedded in the data-access function.
Impact: Cannot swap notification backend; cannot unit-test the discount policy without a DB; whitelist drift between create/update routes.
Recommendation: Pull discount tiers into `src/controllers/relatorio_controller.py` (or a `pricing_service.py`); replace prints with `src/services/notification_service.py` (interface + noop impl); hoist status whitelist into `src/config/enums.py`.

### [MEDIUM] Duplicated validation logic between create and update
File: `controllers.py:30-54 vs 72-91 (produto); 153-158 vs 190-194 (usuario)`
Description: Same validation block copied between `criar_produto`/`atualizar_produto` and `criar_usuario`/`atualizar_usuario`, with minor drift (update path drops the category-whitelist check on line 52, allowing `categoria` poisoning).
Impact: Fix-it-once becomes fix-it-twice; drift already happened.
Recommendation: Extract `validate_produto_payload(dados, partial=False)` to `src/schemas/produto_schema.py`; share between routes.

### [MEDIUM] Catch-all `except Exception` swallows tracebacks and leaks internals
File: `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292`
Description: Every route wraps its body in `try: ... except Exception as e: return jsonify({"erro": str(e)}), 500`. Stack traces and SQL error messages reach the client; logging is `print()` to stdout.
Impact: Information disclosure (error messages reveal table names, query structure); makes structured monitoring impossible.
Recommendation: Register a single `@app.errorhandler(Exception)` in `src/middlewares/error_handler.py`; use `logging.exception(...)`; return a generic 500 envelope.

### [LOW] String concatenation for messages instead of f-strings
File: `controllers.py:8, 11, 54, 57, 106, 161, 208-210, 248, 250; models.py:28, 48-49, 92, 109-110, 126-128, 140-141, 148-150, 155, 157-159, 163-165, 174, 188, 192, 220, 224, 279-280, 291-297`
Description: Codebase predates f-strings (Python 3.6+) stylistically — uses `"Listando " + str(len(produtos)) + " produtos"` etc.
Impact: Readability, plus this exact pattern is what made the SQL injection viable.
Recommendation: f-strings for messages; parameterised queries for SQL (never f-string SQL). Add a lint rule.

### [LOW] Magic numbers and inline whitelists scattered through validation
File: `controllers.py:47-50, 52, 242; models.py:257-262`
Description: `if len(nome) < 2 ... > 200`, `categorias_validas = [...]`, status list `["pendente","aprovado",...]`, discount thresholds `10000/5000/1000` all inline.
Impact: Business rules invisible to readers; can't be configured per environment.
Recommendation: Move into `src/config/constants.py` (e.g. `PRODUTO_NOME_MIN_LEN`, `CATEGORIAS_VALIDAS`, `PEDIDO_STATUS`, `DISCOUNT_TIERS`).

### [LOW] Inconsistent response envelope
File: `controllers.py: throughout (e.g. 9, 18, 29, 132, 141, 161, 180, 252, 270-289)`
Description: Sometimes `{"dados": ..., "sucesso": True}`, sometimes `{"dados": ..., "sucesso": True, "mensagem": "..."}`, sometimes plain `{"erro": "..."}`, sometimes adds `"total"`. No contract.
Impact: Client code drifts; mocking/typing impossible.
Recommendation: Define a single envelope in `src/views/response.py` (e.g. `success(data, message=None)`, `error(message, code)`) and route all returns through it.

**Severity tally for project 1:** CRITICAL: 4 | HIGH: 2 | MEDIUM: 2 | LOW: 3 — **total 11**.

---

## ecommerce-api-legacy — Node.js + Express

Stack: Express 4.x + sqlite3 5.x + body-parser via `express.json()`. 3 source files in `src/`, 180 LOC.
Domain: LMS (Learning Management) — users, courses, enrollments, payments, audit logs, full checkout flow.
Architecture: god-class `AppManager` is constructor + DB init + route definitions + business logic; `utils.js` is a kitchen-sink (config + cache + fake crypto); `app.js` is a 14-line bootstrap.

### [CRITICAL] God class `AppManager` mixing DB schema, routing, payment, audit, callback hell
File: `src/AppManager.js:4-141`
Description: Constructor opens DB; `initDb()` runs DDL + seeds users with plaintext password `'123'` (line 18) and a fake "Clean Architecture" course; `setupRoutes(app)` registers POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id. The checkout handler is a 50-line nested-callback pyramid (lines 28-78) that does request parsing → course lookup → user upsert (with `badCrypto`) → payment processing (`cc.startsWith("4")`) → enrollment insert → payment insert → audit log insert → cache write → response.
Impact: Untestable end-to-end; any new endpoint goes inside this class; impossible to isolate failure domains.
Recommendation: Decompose into `src/controllers/{checkout,admin,user}_controller.js`, `src/models/{user,course,enrollment,payment}_model.js`, `src/services/{payment,audit,notification}_service.js`, `src/middlewares/error_handler.js`, and a thin `src/views/routes.js` composing them.

### [CRITICAL] Hardcoded production-grade credentials in committed source
File: `src/utils.js:1-7; src/AppManager.js:18, 68`
Description: `config = { dbUser: "admin_master", dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_1234567890abcdef", smtpUser: "no-reply@fullcycle.com.br", port: 3000 }`. Seed users plaintext password `'123'`. Default-on-missing password `"123456"` in `badCrypto(p || "123456")`.
Impact: Repo leak = prod takeover; the `pk_live_*` shape matches Stripe live keys verbatim and would trigger real charge attempts.
Recommendation: Move to `src/config/settings.js` reading `process.env.*`; add `.env.example`; rotate the leaked-looking keys regardless of whether they were ever real.

### [CRITICAL] Custom broken password hash plus cleartext card logging
File: `src/utils.js:17-23; src/AppManager.js:45-46`
Description: `badCrypto(pwd)` does `for(let i=0; i<10000; i++) hash += Buffer.from(pwd).toString('base64').substring(0,2)`, returns `hash.substring(0,10)`. Deterministic, no salt, fixed 10-char output, reversible by lookup table. Plus `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` (line 45) logs the full card number and the live payment key on every checkout. Payment decision: `cc.startsWith("4") ? "PAID" : "DENIED"` (line 46).
Impact: Passwords trivially compromised; PCI-DSS violation (card in logs); fake payment processing.
Recommendation: Replace `badCrypto` with `bcrypt.hash` (cost ≥ 10); redact card to last-4 in any log; integrate a real PSP client or mock with explicit feature flag in `src/services/payment_service.js`.

### [HIGH] N+1 with hand-rolled callback counters in financial report
File: `src/AppManager.js:80-129`
Description: `GET /api/admin/financial-report` queries all courses, then for each course queries all enrollments, then for each enrollment queries the user and the payment. Concurrency tracked via decrementing `coursesPending` and `enrPending` counters with `if (... === 0) res.json(report)` — no Promise.all, no async/await. Any inner error silently fails to send a response.
Impact: O(courses × enrollments) queries; hangs on any DB error since neither the inner nor outer counters propagate failures.
Recommendation: Single JOIN query (courses LEFT JOIN enrollments LEFT JOIN users LEFT JOIN payments), aggregated server-side, or rewrite with `async/await` + `Promise.all` in `src/controllers/admin_controller.js`.

### [HIGH] Orphaned-data bug self-documented in response message
File: `src/AppManager.js:131-137`
Description: `DELETE /api/users/:id` runs `DELETE FROM users WHERE id = ?` then responds `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` Note: the user wrote out the bug in plain Portuguese as the response payload.
Impact: Foreign-key references dangling; financial reports break; cannot recreate user with same id.
Recommendation: Transaction wrapping DELETE FROM enrollments / payments / audit_logs / users with row-level FK enforcement (sqlite `PRAGMA foreign_keys = ON`) and `ON DELETE CASCADE`; logic lives in `src/models/user_model.js`.

### [MEDIUM] Global mutable state for cache and revenue
File: `src/utils.js:9-10, 12-15, 25`
Description: Module-level `let globalCache = {}` and `let totalRevenue = 0`, mutated by `logAndCache(key, data)`, re-exported. Cache has no TTL, no eviction, no per-user scoping; `totalRevenue` is mutated but never updated by the checkout code.
Impact: Memory grows unbounded; cross-tenant data leakage; unused mutable export is a footgun.
Recommendation: Replace with a `CacheService` interface in `src/services/cache_service.js` (default: in-memory LRU with TTL); remove `totalRevenue`.

### [MEDIUM] In-memory SQLite database (`:memory:`) wired into prod constructor
File: `src/AppManager.js:7`
Description: `this.db = new sqlite3.Database(':memory:')` inside the AppManager constructor. The DB lives only as long as the process; restart drops all data; horizontal scaling impossible.
Impact: Demo-grade DB used as production storage; data loss on any deploy.
Recommendation: File path from `src/config/settings.js` (`DB_PATH=./data/lms.sqlite`), or proper PostgreSQL via `knex`/`prisma`.

### [MEDIUM] Cryptic request body field names + minimal input validation
File: `src/AppManager.js:29-35`
Description: `req.body.usr, .eml, .pwd, .c_id, .card`. Validation is only `if (!u || !e || !cid || !cc)`; no schema, no length checks, no email format, no card format (just the 1-digit "is it Visa" check).
Impact: Trivial bad-input crashes; misnamed contract makes the API self-undocumented.
Recommendation: Add `zod`/`joi`/`express-validator` schema in `src/middlewares/validate.js`; rename to `name`, `email`, `password`, `courseId`, `card`.

### [LOW] Deprecated/anachronistic API usage: `sqlite3.verbose()` chain
File: `src/AppManager.js:1`
Description: `const sqlite3 = require('sqlite3').verbose();` — the `.verbose()` chain was useful in early sqlite3 v3/v4 for stack traces; in modern versions it is effectively a no-op recommended only for debugging.
Impact: Style/legacy signal; suggests the file dates from 2015-era Node patterns and confirms no recent maintenance.
Recommendation: `const sqlite3 = require('sqlite3')` in dev/prod; migrate to `better-sqlite3` for synchronous performance, or to a real DB driver, in `src/config/database.js`.

### [LOW] Plain-text responses mixed with JSON; ad-hoc error strings
File: `src/AppManager.js:35, 38, 41, 48, 51, 55, 70, 84, 135`
Description: Errors returned as `res.status(400).send("Bad Request")`, `res.status(404).send("Curso não encontrado")`, success as `res.status(200).json(...)`. No consistent envelope, no error codes.
Impact: Frontend cannot programmatically detect error types; HTTP status alone insufficient.
Recommendation: Standardise on `{ status, data?, error? }` JSON envelope in `src/views/response.js`; route all responses through a small helper.

**Severity tally for project 2:** CRITICAL: 3 | HIGH: 2 | MEDIUM: 3 | LOW: 2 — **total 10**.

---

## task-manager-api — Python + Flask + SQLAlchemy

Stack: Flask + flask-cors + Flask-SQLAlchemy. ~1150 LOC across `app.py`, `database.py`, `seed.py`, `models/{task,user,category}.py`, `routes/{task,user,report}_routes.py`, `services/notification_service.py`, `utils/helpers.py`.
Domain: Task management (tasks, users, categories, reports, notifications).
Architecture: partially MVC — models and routes exist, but **no controllers layer**, business logic lives in routes, services are mostly stubs, utils are stale, no middleware, no config module.

### [CRITICAL] Hardcoded SMTP credentials and Flask secret key
File: `services/notification_service.py:7-11; app.py:11-13`
Description: `NotificationService.__init__` hardcodes `email_host='smtp.gmail.com'`, `email_port=587`, `email_user='taskmanager@gmail.com'`, `email_password='senha123'`. `app.py:13` `SECRET_KEY = 'super-secret-key-123'`. No environment loading.
Impact: SMTP credentials in source = mail-relay abuse; weak signed-cookie secret = session forgery.
Recommendation: Extract into `src/config/settings.py` reading `os.environ`; provide `.env.example`; never instantiate NotificationService with literal creds.

### [HIGH] Fake JWT issuance + no authentication middleware on any route
File: `routes/user_routes.py:185-211; routes/{task,report}_routes.py (entire files)`
Description: `/login` returns `{'token': 'fake-jwt-token-' + str(user.id)}` (line 210). The string is never verified anywhere. Every other endpoint (`/tasks`, `/users`, `/reports/*`, `/categories`) is open — no `Authorization` header required, no decorator like `@login_required`.
Impact: Authentication is theatre; any client can call any endpoint including DELETE.
Recommendation: Replace the fake token with `pyjwt`-issued JWT signed by `SECRET_KEY`; add `@require_auth` decorator in `src/middlewares/auth.py`; apply to all non-public routes in `src/controllers/`.

### [HIGH] N+1 in `/tasks`, `/reports/summary`, `/users/<id>/tasks`
File: `routes/task_routes.py:14-59; routes/report_routes.py:30-43, 53-68; routes/user_routes.py:153-183`
Description: `get_tasks` does `Task.query.all()` then per task `User.query.get(t.user_id)` + `Category.query.get(t.category_id)`. `summary_report` loops all tasks for overdue (lines 30-43) and then loops users running `Task.query.filter_by(user_id=u.id).all()` for each (53-68).
Impact: Both endpoints degrade quadratically; `/reports/summary` will saturate the DB under any non-trivial seed.
Recommendation: Use `db.session.query(Task).options(joinedload(Task.user), joinedload(Task.category)).all()`; aggregate stats with `func.count()` + `group_by`; encapsulate in `src/models/task_repository.py` and call from `src/controllers/task_controller.py`.

### [HIGH] Business logic embedded in routes (controllers responsibility)
File: `routes/task_routes.py:30-39, 71-80, 273-296; routes/user_routes.py:171-180; routes/report_routes.py:13-101`
Description: Overdue-computation block (lines 30-39, 71-80, etc.) is duplicated in **four places**. Stats aggregation lives directly in `task_stats` route. The 89-line `summary_report` route builds the entire report in-place — counts per status, per priority, overdue list, recent activity window, per-user productivity — all inside the HTTP handler.
Impact: No layer to unit-test; routes carry business invariants; same logic drifts across copies.
Recommendation: Extract to `src/controllers/task_controller.py::compute_overdue(task)`, `src/controllers/report_controller.py::build_summary()`, etc. Routes become 3-line dispatchers.

### [MEDIUM] Duplicate validation between create/update plus dead-code parallel validator in utils
File: `routes/task_routes.py:92-144 vs 166-213; utils/helpers.py:57-108`
Description: `create_task` and `update_task` repeat the same `title/status/priority/user_id/category_id/due_date/tags` checks with drift. Meanwhile `utils/helpers.py::process_task_data(data, existing_task=None)` is a fully-formed parallel validator (51 lines) that is **never imported** by any route.
Impact: Validation rules diverge between create and update (e.g. only create checks `len(title) < 3`); 51 lines of dead code create maintenance illusion.
Recommendation: Adopt the existing `process_task_data` (or a marshmallow/pydantic schema in `src/schemas/task_schema.py`); delete the inline blocks; either wire `process_task_data` in or remove it entirely.

### [MEDIUM] Bare `except:` blocks throughout swallow tracebacks
File: `routes/task_routes.py:62-63, 137-138, 204-205, 236-238; routes/report_routes.py:186-188, 207-209, 221-223`
Description: Pattern `except: return jsonify({'error': 'Erro interno'}), 500` (no exception variable). Hides the actual error type, prevents logging.
Impact: Debugging requires re-reading code paths; structured monitoring impossible.
Recommendation: Replace with `except SQLAlchemyError as e:` (or `except Exception as e:` minimally) plus `current_app.logger.exception(e)`; register an `@app.errorhandler` in `src/middlewares/error_handler.py`.

### [MEDIUM] User delete handles cascade manually instead of declaring on the model
File: `routes/user_routes.py:140-142`
Description: `delete_user` queries `Task.query.filter_by(user_id=user_id).all()` and deletes them in a loop before deleting the user. The relationship is declared on `User.tasks` (visible from `len(u.tasks)` at line 22) but without `cascade="all, delete-orphan"`.
Impact: Route-level cascade is fragile (skips the FK declaration), invisible to migrations, fails if another route deletes a user without replicating the loop.
Recommendation: Add `tasks = db.relationship('Task', backref='user', cascade='all, delete-orphan')` in `src/models/user.py`; simplify the route to one `db.session.delete(user)`.

### [LOW] Unused imports and standard-lib bloat in nearly every file
File: `app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:8; utils/helpers.py:3-7`
Description: `import os, sys, json, datetime` (only `datetime` used) in app.py; `import json, os, sys, time` in task_routes.py (none used); `import hashlib, json` in user_routes.py (only `re` and `datetime` used elsewhere); `import json` in report_routes.py (unused); `import os, json, sys, math, hashlib` in helpers.py (none used).
Impact: Cognitive overhead, hides what each module actually depends on.
Recommendation: Run `ruff check --select F401 --fix .`; configure pre-commit to prevent regression.

### [LOW] Magic strings and numbers in routes despite constants existing in utils
File: `routes/task_routes.py:32, 110, 113, 177, 182, 243, 286; utils/helpers.py:110-116`
Description: Routes check `if status not in ['pending', 'in_progress', 'done', 'cancelled']` (line 110), `if priority < 1 or priority > 5` (line 113), `'done' and 'cancelled'` overdue check (line 32, 286). `utils/helpers.py:110-116` already defines `VALID_STATUSES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY` — **none imported by the routes**.
Impact: Constants drift; rules invisible from the controllers/views perspective.
Recommendation: Move constants to `src/config/constants.py` (or `src/models/enums.py`), import in controllers, schemas, and routes uniformly.

### [LOW] `type(x) == list` instead of `isinstance(x, list)`
File: `routes/task_routes.py:141, 210; utils/helpers.py:103`
Description: Three call sites use `type(x) == list` style.
Impact: Style + reliability (doesn't handle list subclasses, breaks under duck-typing).
Recommendation: `isinstance(x, list)` consistently; add `ruff` rule `E721` if not already enabled.

**Severity tally for project 3:** CRITICAL: 1 | HIGH: 3 | MEDIUM: 3 | LOW: 3 — **total 10**.

---

## Coverage matrix

| Project | CRITICAL | HIGH | MEDIUM | LOW | Total | Meets ≥5 + ≥1 CRIT/HIGH + ≥2 MED + ≥2 LOW? |
|---------|----------|------|--------|-----|-------|---------------------------------------------|
| code-smells-project | 4 | 2 | 2 | 3 | 11 | YES |
| ecommerce-api-legacy | 3 | 2 | 3 | 2 | 10 | YES |
| task-manager-api | 1 | 3 | 3 | 3 | 10 | YES |

Aggregate: 8 CRITICAL, 7 HIGH, 8 MEDIUM, 8 LOW — 31 findings. Distribution is balanced enough to seed a representative anti-pattern catalog without skewing toward one severity tier.

## Catalog seed list (S002 input)

Deduplicated anti-pattern names observed across the three projects. Catalog in S002 must include at least 8 entries; this list provides 22 viable seeds:

1. `god-class-or-god-module` — P1 controllers.py, P2 AppManager.js
2. `hardcoded-credentials` — P1, P2, P3
3. `sql-injection-string-concat` — P1 (every query)
4. `arbitrary-sql-execution-endpoint` — P1 `/admin/query`
5. `business-logic-in-route-or-controller` — P1, P3
6. `n+1-query` — P1, P2, P3
7. `global-mutable-state` — P1 db_connection, P2 globalCache/totalRevenue
8. `plaintext-password-storage` — P1, P2
9. `broken-or-fake-crypto` — P2 badCrypto, P3 fake-jwt-token
10. `bare-except-or-catch-all` — P1, P3
11. `magic-numbers-or-inline-whitelist` — P1, P3
12. `missing-input-validation` — P2
13. `duplicate-validation-logic-across-create-update` — P1, P3
14. `dead-code-parallel-implementation` — P3 process_task_data
15. `unused-imports` — P3 (every file)
16. `missing-orm-cascade-or-manual-fk-cleanup` — P2, P3
17. `pii-or-card-in-logs` — P2
18. `deprecated-api-call` — P2 sqlite3.verbose() (target slot for the brief's explicit requirement)
19. `inconsistent-response-envelope` — P1, P2
20. `debug-true-in-prod-config` — P1
21. `mixed-domain-models-or-routes` — P1, P3
22. `synchronous-side-effects-in-controller` — P1 print-as-notification, P2 inline payment logic

## Playbook seed list (S002 input)

Deduplicated transformation recipes addressing the catalog above. Playbook in S002 must include at least 8 before/after recipes; this list provides 16 viable seeds:

1. `extract-config-to-env-or-settings-module` — moves SECRET_KEY, DB_PATH, SMTP creds, payment keys out of source
2. `split-god-class-into-controllers-by-domain` — `controllers.py` → `produto_controller.py` + siblings; `AppManager.js` → 3-4 controllers
3. `replace-raw-sql-with-parameterised-queries` — `cursor.execute(sql, params)` everywhere; addresses SQL injection
4. `eager-load-relationships-to-fix-n+1` — JOIN/`joinedload` in repository methods
5. `move-business-logic-from-route-to-controller-or-service` — overdue computation, discount tiers, notifications
6. `extract-validation-to-schema-module` — marshmallow/pydantic/zod schemas; one source of truth for create+update
7. `replace-bare-except-with-typed-exceptions-and-error-middleware` — `@app.errorhandler`; structured logging
8. `replace-fake-crypto-with-bcrypt-or-argon2` — `bcrypt.hash` with cost ≥ 10; salt per password
9. `centralise-error-handling-in-middleware` — single error-handler module returning consistent envelope
10. `redact-secrets-and-pii-from-logs` — card → last-4; never log payment keys
11. `add-orm-cascade-or-explicit-fk-cleanup` — `cascade="all, delete-orphan"`; PRAGMA foreign_keys = ON
12. `replace-magic-numbers-with-constants-module` — `src/config/constants.py` or `src/models/enums.py`
13. `remove-dead-code-and-unused-imports` — `ruff F401`, manual review for parallel-implementation modules
14. `standardise-response-envelope` — `src/views/response.py::success()/error()` helpers; route through
15. `replace-deprecated-api-call-with-current` — `sqlite3.verbose()` removal; covers brief's mandatory deprecated-API detection
16. `move-schema-init-out-of-runtime-getter-to-migration-or-startup-hook` — `database.py` DDL → `init_db.py` or alembic

## Notes for S002

- The deprecated-API requirement (`desafio.md` line 144) is satisfied by seed #18 in the catalog and recipe #15 in the playbook. Pick at least one additional generic deprecated-API signal for the catalog (e.g. Python `cgi` module, Node `crypto.createCipher`, Express `body-parser` direct import) to make the catalog stack-agnostic.
- The skill must be agnostic — keep all stack-specific detection signals (regex, file globs) inside lookup tables in `analise-projeto.md` and `catalog-antipatterns.md`, never in `SKILL.md` (invariant I-1).
- Project 3 is the toughest "agnostic" test because it is partially organised — the skill must improve rather than rewrite. Plan the playbook so each recipe is independently applicable.

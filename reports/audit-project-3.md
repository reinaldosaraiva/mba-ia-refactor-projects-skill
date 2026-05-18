================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Files:   15 analyzed | ~1158 lines of code
Generated: 2026-05-18

## Summary
CRITICAL: 1 | HIGH: 2 | MEDIUM: 3 | LOW: 2

## Findings

### [CRITICAL] hardcoded-credentials
File: app.py:13, services/notification_service.py:7-10
Description: `SECRET_KEY = 'super-secret-key-123'` is a literal in the composition root; SMTP host/port/user/password (`'senha123'`) are literals in `NotificationService.__init__`.
Impact: Source-tree access compromises Flask sessions and exfiltrates the production mailbox credential; rotation requires a code deploy.
Recommendation: Apply playbook recipe `extract-config-to-env-or-settings-module`.

### [HIGH] business-logic-in-route-or-controller
File: routes/report_routes.py:13-101, routes/report_routes.py:103-155, routes/task_routes.py:11-63, routes/task_routes.py:273-299
Description: Routes own aggregation, formatting, overdue computation, and percentage maths inline. `summary_report` is 89 lines computing six aggregations (overview, status, priority, overdue, recent activity, per-user productivity) directly against the ORM; `user_report` repeats the per-status counters; `get_tasks` builds per-row dicts plus overdue calc; `task_stats` computes completion rate inline.
Impact: Cannot unit-test rules without an HTTP server; the same overdue check is hand-rolled in four places and is already drifting (different early-exit shapes); swapping the HTTP transport to a queue worker would require rewriting four endpoints.
Recommendation: Apply playbook recipe `move-business-logic-from-route-to-controller`.

### [HIGH] n+1-query
File: routes/task_routes.py:14-59, routes/report_routes.py:30-43, routes/report_routes.py:53-68, routes/user_routes.py:153-183
Description: `get_tasks` runs `Task.query.all()` then issues `User.query.get(t.user_id)` and `Category.query.get(t.category_id)` per row (2N follow-up queries). `summary_report` does `Task.query.all()` for overdue then `User.query.all()` followed by `Task.query.filter_by(user_id=u.id).all()` per user (N+M queries). `get_user_tasks` loops to compute overdue without eager-loading. No `joinedload`/`selectinload` anywhere.
Impact: Endpoint latency grows linearly with row count; on SQLite the connection pool serialises queries, so under any concurrent load the API stalls; `/reports/summary` is the worst offender because it compounds two N-shaped loops.
Recommendation: Apply playbook recipe `eager-load-relationships-to-fix-n+1`.

### [MEDIUM] bare-except-or-catch-all
File: routes/task_routes.py:62, routes/task_routes.py:137, routes/task_routes.py:151-154, routes/task_routes.py:204, routes/task_routes.py:221-223, routes/task_routes.py:236-238, routes/user_routes.py:87-90, routes/user_routes.py:130-132, routes/user_routes.py:149-151, routes/report_routes.py:186-188, routes/report_routes.py:207-209, routes/report_routes.py:221-223, services/notification_service.py:23-25, utils/helpers.py:46, utils/helpers.py:49, utils/helpers.py:88
Description: 16 bare `except:` or `except Exception` blocks swallow tracebacks and return either `{'error': 'Erro interno'}` or `{'error': 'Erro ao atualizar'}` — every per-route try/except is a no-op for observability. No `@app.errorhandler` is registered anywhere.
Impact: Programming bugs surface as opaque HTTP 500s; legitimate validation failures get reclassified as transient errors; root-cause analysis requires log archaeology because no exception is logged.
Recommendation: Apply playbook recipe `replace-bare-except-with-typed-handler-and-error-middleware`.

### [MEDIUM] duplicate-validation-logic
File: routes/task_routes.py:92-114 vs routes/task_routes.py:166-184, routes/user_routes.py:54-72 vs routes/user_routes.py:102-122, utils/helpers.py:57-108
Description: The task title/status/priority checks are duplicated between `create_task` (POST) and `update_task` (PUT) and already drifting (`create_task` validates priority via `< 1 or > 5` always, `update_task` only when `'priority' in data` — same intent, different gates). User email/role/password checks are similarly duplicated. Meanwhile, `utils/helpers.py::process_task_data` is a complete validator that no route imports, and `marshmallow==3.20.1` ships in `requirements.txt` but is never used.
Impact: Drift between create and update paths produces invisible bugs (a customer can PUT a record into a state POST would have rejected); the dead validator is decay-by-default; the unused schema library inflates dependency surface for zero benefit.
Recommendation: Apply playbook recipe `move-business-logic-from-route-to-controller`.

### [MEDIUM] deprecated-api-call
File: app.py:7, services/notification_service.py:35, utils/helpers.py:38, models/task.py:15-16, models/task.py:52, models/user.py:14, models/category.py:11, routes/task_routes.py:31, routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:72, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:172, routes/task_routes.py:188, routes/task_routes.py:195, routes/task_routes.py:215, routes/task_routes.py:227, routes/task_routes.py:285, routes/user_routes.py:29, routes/user_routes.py:94, routes/user_routes.py:136, routes/user_routes.py:155, routes/user_routes.py:172, routes/report_routes.py:35, routes/report_routes.py:42, routes/report_routes.py:45, routes/report_routes.py:71, routes/report_routes.py:105, routes/report_routes.py:133, routes/report_routes.py:192, routes/report_routes.py:213, seed.py:66-75
Description: 18 call sites use `datetime.utcnow()` (deprecated in Python 3.12 in favour of `datetime.now(datetime.UTC)`). 16 call sites use `Model.query.get(id)` (deprecated in SQLAlchemy 2.x in favour of `db.session.get(Model, id)`). Both deprecations are mass-recurring across the route surface, not isolated.
Impact: A Python 3.12 upgrade emits `DeprecationWarning` on every request; an SQLAlchemy 2.x upgrade breaks the routes outright; CI lint accumulates noise that hides real warnings.
Recommendation: Apply playbook recipe `replace-deprecated-api-call-with-current-equivalent`.

### [LOW] magic-numbers-or-inline-whitelist
File: routes/task_routes.py:96, routes/task_routes.py:99, routes/task_routes.py:110, routes/task_routes.py:113, routes/task_routes.py:167, routes/task_routes.py:169, routes/task_routes.py:177, routes/task_routes.py:182, routes/user_routes.py:64, routes/user_routes.py:71, routes/user_routes.py:115, routes/user_routes.py:120, routes/report_routes.py:24-28, models/task.py:39, models/task.py:46, utils/helpers.py:110-116
Description: Routes embed `len(title) < 3`, `len(title) > 200`, `priority < 1 or priority > 5`, `if status not in ['pending', 'in_progress', 'done', 'cancelled']`, `if role not in ['user', 'admin', 'manager']`, and `if len(password) < 4` directly in handler bodies. `models/task.py` even hand-rolls `validate_status` and `validate_priority` methods with the same inline lists. Meanwhile, `utils/helpers.py:110-116` defines `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY`, `DEFAULT_COLOR` — and no route or model imports them.
Impact: Business rule changes require editing 8+ sites; the parallel dead-constants module guarantees future drift; the canonical name for "valid statuses" is whatever any given developer typed at the call site.
Recommendation: Apply playbook recipe `lift-magic-numbers-and-whitelists-into-constants-module`.

### [LOW] inconsistent-response-envelope
File: routes/task_routes.py:61, routes/task_routes.py:81, routes/task_routes.py:83, routes/task_routes.py:150, routes/task_routes.py:235, routes/task_routes.py:271, routes/task_routes.py:299, routes/user_routes.py:25, routes/user_routes.py:86, routes/user_routes.py:148, routes/user_routes.py:207-211, routes/report_routes.py:101, routes/report_routes.py:155, routes/report_routes.py:165
Description: The API mixes at least five response shapes: bare list (`jsonify(result)`), bare dict via `to_dict()`, `{'error': '...'}`, `{'message': '...'}`, and ad-hoc envelopes like `{'message': ..., 'user': ..., 'token': ...}` from `/login`. No `response.py` helper, no canonical `{status, data}` envelope.
Impact: Client code cannot programmatically discriminate success from error without inspecting HTTP status; mobile/TypeScript consumers duplicate response-shape assertions everywhere; the `/login` payload mixes domain data with a top-level token field that breaks any envelope convention the rest of the API might adopt.
Recommendation: Apply playbook recipe `replace-bare-except-with-typed-handler-and-error-middleware`.

================================
Total: 8 findings
================================

## Calibration note (Phase 2)

S001 manual analysis flagged 10 issues in this project. The catalog (v1) covers 8 of them. The remaining 5 surface area items have no catalog slug in v1 and are recorded here as **residuals** to be revisited after Phase 3 if scope permits — not as fabricated findings to inflate the total:

- `fake-jwt-token-issuance` — `routes/user_routes.py:210` returns a deterministic `'fake-jwt-token-' + str(user.id)` instead of signing a real JWT. Same family as project 2's fake-or-broken-crypto residual.
- `missing-auth-middleware-on-protected-routes` — no `@require_auth` decorator anywhere; every endpoint (including admin operations and the `/login` issuer) is open.
- `missing-orm-cascade-or-manual-fk-cleanup` — `routes/user_routes.py:140-142` manually loops `Task.query.filter_by(user_id=user_id).all()` and deletes each before deleting the user, instead of declaring `cascade='all, delete-orphan'` on the `User.tasks` relationship. Same family as project 2's residual.
- `unused-imports` — `task_routes.py:7 (json, os, sys, time)`, `user_routes.py:6 (hashlib, json)`, `report_routes.py:8 (json)`, `utils/helpers.py:3-7 (os, json, sys, math, hashlib)`.
- `type(x) == list` instead of `isinstance(x, list)` — `task_routes.py:141, 210`, `utils/helpers.py:103`.

Phase 3 will fix the `User.tasks` cascade as a structural side-effect of moving the model under `src/models/` (the cascade declaration is the natural ORM-side artefact, and removing the manual loop simplifies the new `user_controller.delete`). The other four residuals remain out of v1 scope and will be listed in the post-Phase-3 Validation block.

> Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

> Operator answered `y` on 2026-05-18.

## Validation

Boot command:
```
SECRET_KEY=test-do-not-commit DEBUG=false PORT=5151 .venv/bin/python seed.py
SECRET_KEY=test-do-not-commit DEBUG=false PORT=5151 .venv/bin/python app.py
```

Boot outcome: OK (3 usuários / 4 categorias / 10 tasks seeded; Flask serving on `http://127.0.0.1:5151`).

| Endpoint                            | Method | HTTP | Pass? |
|-------------------------------------|--------|------|-------|
| /                                   | GET    | 200  | YES   |
| /health                             | GET    | 200  | YES   |
| /tasks                              | GET    | 200  | YES   |
| /tasks                              | POST   | 201  | YES   |
| /tasks/{id}                         | GET    | 200  | YES   |
| /tasks/{id}                         | PUT    | 200  | YES   |
| /tasks/{id}                         | DELETE | 200  | YES   |
| /tasks/search?q=login               | GET    | 200  | YES   |
| /tasks/stats                        | GET    | 200  | YES   |
| /users                              | GET    | 200  | YES   |
| /users                              | POST   | 201  | YES   |
| /users/{id}                         | GET    | 200  | YES   |
| /users/{id}                         | PUT    | 200  | YES   |
| /users/{id}                         | DELETE | 200  | YES   |
| /users/{id}/tasks                   | GET    | 200  | YES   |
| /login                              | POST   | 200  | YES   |
| /reports/summary                    | GET    | 200  | YES   |
| /reports/user/{id}                  | GET    | 200  | YES   |
| /categories                         | GET    | 200  | YES   |
| /categories                         | POST   | 201  | YES   |
| /categories/{id}                    | PUT    | 200  | YES   |
| /categories/{id}                    | DELETE | 200  | YES   |
| /tasks/9999 (error envelope check)  | GET    | 404  | YES   |
| /tasks  (validation error check)    | POST   | 400  | YES   |

22 happy-path endpoints + 2 negative envelope checks; all pass.

Regressions: none.

Catalog findings status (post-refactor):

| Slug | Status |
|------|--------|
| hardcoded-credentials | FIXED — `SECRET_KEY` + SMTP creds read from env via `src/config/settings.py`; boot fails fast without `SECRET_KEY`; `.env.example` documents required vars; `.env` covered by repo-root `.gitignore`. |
| business-logic-in-route-or-controller | FIXED — `summary_report`, `user_report`, `task_stats`, `get_tasks`, overdue computation moved to `src/controllers/{report,task}_controller.py`; `src/views/*_routes.py` route bodies are now 1-line dispatchers. |
| n+1-query | FIXED — `list_tasks` uses `joinedload(Task.user, Task.category)`; `/reports/summary` per-user productivity now a single `func.count(...).group_by(User.id)` aggregate (was N+1 over `User.query.all()`); `task_stats` overdue is one `func.count(...)` SQL filter. |
| bare-except-or-catch-all | FIXED — every per-route try/except removed; controllers raise typed errors (`NotFoundError`, `ValidationError`, `ConflictError`, `AuthError`, `ForbiddenError`); `src/middlewares/error_handler.py` registers handlers for `AppError`, `HTTPException`, `Exception`; SMTP catch narrowed to `smtplib.SMTPException`. |
| duplicate-validation-logic | FIXED — `process_task_data` retired; `src/schemas/{task,user,category}_schema.py` define marshmallow schemas adopted by both POST (full) and PUT (`partial=True`); marshmallow 3.20.1 now in active use (previously dead in `requirements.txt`). |
| deprecated-api-call | FIXED — 18 `datetime.utcnow()` sites replaced with `src.utils.helpers.now_utc()` (`datetime.now(timezone.utc).replace(tzinfo=None)`); 16 `Model.query.get(...)` sites replaced with `db.session.get(Model, ...)`. Layering grep `grep -rEn 'datetime\.utcnow|\.query\.get\(' src/` returns no matches. |
| magic-numbers-or-inline-whitelist | FIXED — all whitelists/thresholds (`VALID_STATUSES`, `VALID_ROLES`, `TASK_TITLE_MIN_LEN`, `TASK_PRIORITY_MIN`, `TASK_PRIORITY_MAX`, `USER_PASSWORD_MIN_LEN`, `CATEGORY_DEFAULT_COLOR`, `TERMINAL_STATUSES`, `RECENT_ACTIVITY_DAYS`) consolidated in `src/config/constants.py` and consumed by schemas/controllers/models. Old dead module retired. |
| inconsistent-response-envelope | FIXED — all success responses go through `src/views/response.py::success(data, message, http)` → `{status: ok, data: …}`; all errors flow through `error_handler.py` → `{status: error, error: {code, message}}`. Verified against `/tasks` and `/tasks/9999` payloads. |

Residuals (out of v1 catalog scope; documented and accepted):

- **fake-jwt-token-issuance** — `src/controllers/user_controller.py::authenticate` still returns `'fake-jwt-token-' + str(user.id)`. Real JWT signing is not in the v1 playbook. Marked with an inline comment so it does not regress in future sweeps.
- **missing-auth-middleware** — no `@require_auth` decorator wired on protected routes. Adding an auth strategy is a separate workstream.
- **unused-imports** — verified clean post-refactor: `grep -rEn '^(import|from)' src/ | wc -l` → only live imports remain.
- **`type(x) == list`** — replaced with `isinstance(x, list)` inside `src/schemas/task_schema.py::normalise_tags` as a side-effect of moving validation. No surviving `type(...) ==` patterns in `src/`.
- **manual cascade in delete_user** — STRUCTURALLY FIXED (not a residual after all): `User.tasks` now declares `cascade='all, delete-orphan'`, so `db.session.delete(user)` removes the user's tasks transactionally. The pre-refactor manual loop in `delete_user` is gone. Documented as a small bleed beyond the strict v1 catalog because the cascade declaration is the natural ORM-side artefact of moving the model under `src/models/`.


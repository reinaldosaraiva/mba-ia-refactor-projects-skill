# P001-S006 — Results

**Verdict:** PASS
**Date:** 2026-05-18
**Owner:** claude-opus-4-7

## What changed

Executed `/refactor-arch` end-to-end against `task-manager-api/` (Python + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1, ~1158 LOC across 15 source files). This is the third and final delivery round of P001 — the first cross-stack project (partially-organised, vs. flat-Python in S004 and flat-Node in S005) — so the run also doubles as the architecture-agnosticism end-to-end proof inside Python.

### Part A — skill copy + Fase 1 + Fase 2

1. `cp -R code-smells-project/.claude task-manager-api/.claude`; `diff -rq` empty (6 skill files bit-identical to the canonical source in project 1).
2. Fase 1 detection block:
   ```
   Language:      python
   Framework:     python-flask (Flask 3.0.0 + Flask-SQLAlchemy 3.1.1)
   Dependencies:  flask, flask-sqlalchemy, flask-cors, marshmallow, requests, python-dotenv
   Domain:        Task Manager API (tasks, users, categories, reports, notifications)
   Architecture:  partially-organised — models/, routes/, services/, utils/ present; controllers/, config/, middlewares/, schemas/, errors/ absent
   Source files:  15 .py files analyzed (~1158 LOC)
   DB tables:     tasks, users, categories
   ```
3. Fase 2 wrote `reports/audit-project-3.md` with 8 findings (1 CRIT + 2 HIGH + 3 MED + 2 LOW), exact file/line refs, calibration block against S001 listing 5 residuals; halt prompt surfaced verbatim and operator answered `y`.

### Part B — Fase 3 (refactor + validate)

1. **Skill copy preserved** — `task-manager-api/.claude/skills/refactor-arch/` untouched after Fase 3 (6 files, identical to project 1).
2. **MVC tree under `src/`** (10 layers, 30 `.py` files):
   - `src/config/{settings.py, constants.py}` — env-loaded; secrets fail-fast; all whitelists/thresholds consolidated (`VALID_STATUSES`, `VALID_ROLES`, `TASK_TITLE_MIN_LEN`, `TASK_PRIORITY_MAX`, `USER_PASSWORD_MIN_LEN`, `TERMINAL_STATUSES`, `RECENT_ACTIVITY_DAYS`, …).
   - `src/models/{__init__.py, user.py, category.py, task.py}` — `db = SQLAlchemy()` exported; `User.tasks` declares `cascade='all, delete-orphan'`; `back_populates` replaces the implicit `backref`; `created_at`/`updated_at` use `now_utc` (no more `datetime.utcnow`).
   - `src/views/{__init__.py, response.py, task_routes.py, user_routes.py, report_routes.py, category_routes.py}` — every route handler is now 1–3 lines; uses `success()` envelope; no direct ORM access (`grep -rEn 'from src\.models' src/views/` returns nothing).
   - `src/controllers/{task,user,report,category}_controller.py` — all business logic. `compute_overdue(task, reference)` is the single source of truth; `build_summary()` is one aggregate query (was N+1 over users); `task_stats()` overdue count is one SQL filter (was Python loop). `db.session.get(Model, id)` everywhere (16 sites rewritten from `Model.query.get`).
   - `src/services/notification_service.py` — SMTP host/user/password injected from `settings`; `_enabled()` no-ops when SMTP not configured; bare `except Exception` narrowed to `smtplib.SMTPException` with `logger.exception`.
   - `src/middlewares/error_handler.py` — `register(app)` wires three handlers (`AppError`, `HTTPException`, `Exception`); canonical envelope `{status: error, error: {code, message}}`.
   - `src/errors/__init__.py` — `AppError` + `ValidationError`, `NotFoundError`, `ConflictError`, `AuthError`, `ForbiddenError`, each with `code` + `http` attrs.
   - `src/schemas/{task,user,category}_schema.py` + `src/schemas/__init__.py::validate_with()` — marshmallow 3.20.1 adopted; `_task_schema` reused with `partial=True` for PUT; converts `marshmallow.ValidationError` into our `AppError`.
   - `src/utils/helpers.py` — pure helpers only; `now_utc()` exposed; dead `process_task_data` retired; unused imports gone.
3. **`app.py`** is now a composition root: 6 `from src.*` imports, 50 LOC, no business logic, no SQL, no validation. `create_app()` wires config → DB → CORS → blueprints → error handlers → adds `/` + `/health`.
4. **`seed.py`** updated to import from `src.models.*` and `src.utils.helpers.now_utc`; reseeded 3 users / 4 categories / 10 tasks successfully.
5. **`.env.example`** authored with `SECRET_KEY`, `DEBUG`, `HOST`, `PORT`, `DATABASE_URI`, `SMTP_*`; repo-root `.gitignore` already covers `.env`.
6. **Old folders removed** — `task-manager-api/{models,routes,services,utils}/` deleted; `database.py` deleted; nothing left at repo root except `app.py`, `seed.py`, `requirements.txt`, `README.md`, `.env.example`, `src/`, `.claude/`.
7. **Layering grep checks (per `guidelines-arquitetura.md`):**
   - `from src.models` in `src/views/` → none.
   - `from src.(controllers|views)` in `src/models/` → none.
   - `from src.views` in `src/controllers/` → none.
   - `from src.(models|controllers)` in `src/middlewares/` → none.
   - `from src.` in `app.py` → 6 (composition root).
8. **Catalog-pattern grep checks (post-refactor):**
   - `datetime.utcnow` in `src/` → 1 occurrence (a docstring in `helpers.py` describing the migration; no call site).
   - `Model.query.get(` in `src/` → none.
   - `^\s*except\s*:\s*$` in `src/` → none.
   - `type(x) == list` in `src/` → none.
   - Hardcoded `SECRET_KEY`/`PASSWORD` literals outside `src/config/settings.py` → none.
9. **Boot + smoke test:**
   - venv built from `requirements.txt` (Flask 3.0.0, Flask-SQLAlchemy 3.1.1, marshmallow 3.20.1).
   - Boot command: `SECRET_KEY=test-do-not-commit DEBUG=false PORT=5151 .venv/bin/python app.py`. Flask up on `http://127.0.0.1:5151` (port 5151 chosen to avoid macOS AirPlay 5000 + previous project caches on 5050 and 3131).
   - **22 happy-path endpoints + 2 negative envelope checks = 24 hits, 0 regressions.**
   - Verified envelope shape via direct payload inspection: success → `{status, data}`; 404 → `{status: error, error: {code: not_found, message: ...}}`; 400 → `{status: error, error: {code: validation_error, message: ...}}`.

### Improve-not-rewrite discipline (I-7)

Project 3 began with `models/`, `routes/`, `services/`, `utils/` already present. The refactor **relocated** those files into `src/`, augmented them where catalog findings required (cascade, env-loaded SMTP, parse-via-schema, env-loaded SECRET_KEY), and **added** the missing layers (`config/`, `controllers/`, `middlewares/`, `errors/`, `schemas/`, `views/response.py`). Working content was preserved verbatim wherever a finding did not target it — no wholesale rewrite of any file.

## Catalog/playbook coverage (recap)

| Finding | Catalog slug | Playbook recipe | Status |
|---|---|---|---|
| 1 | hardcoded-credentials | extract-config-to-env-or-settings-module | FIXED |
| 2 | business-logic-in-route-or-controller | move-business-logic-from-route-to-controller | FIXED |
| 3 | n+1-query | eager-load-relationships-to-fix-n+1 | FIXED |
| 4 | bare-except-or-catch-all | replace-bare-except-with-typed-handler-and-error-middleware | FIXED |
| 5 | duplicate-validation-logic | move-business-logic-from-route-to-controller | FIXED |
| 6 | deprecated-api-call | replace-deprecated-api-call-with-current-equivalent | FIXED |
| 7 | magic-numbers-or-inline-whitelist | lift-magic-numbers-and-whitelists-into-constants-module | FIXED |
| 8 | inconsistent-response-envelope | replace-bare-except-with-typed-handler-and-error-middleware | FIXED |

Residuals: fake-jwt-token-issuance, missing-auth-middleware (out of v1 scope; documented). Manual-cascade was structurally fixed via `User.tasks` cascade declaration during the model move.

## Definition of done — checklist

- [x] `task-manager-api/.claude/skills/refactor-arch/` is a verbatim copy of project 1's (6 files, `diff -rq` empty).
- [x] `reports/audit-project-3.md` exists with ≥ 5 findings (8), ≥ 1 CRIT/HIGH (1 CRIT + 2 HIGH); calibration documents 5 residuals.
- [x] Fase-2 halt surfaced literally; operator `y` recorded.
- [x] `task-manager-api/src/{config,models,views,controllers,services,middlewares,errors,schemas,utils}/` populated.
- [x] Original `models/`, `routes/`, `services/`, `utils/` at repo root moved under `src/` (not duplicated).
- [x] Layering grep checks pass (4 PASS + 6 imports in composition root).
- [x] Skill tree unchanged after Fase 3.
- [x] App boots with `SECRET_KEY=… python app.py`; 22/22 endpoints respond; 0 regressions.
- [x] Plan files updated; lock cleared; two commits landed (refactor + hash).

## Decision

Verdict: **PASS**. All acceptance criteria met across the 3 project sweeps (S004 PASS, S005 PASS, S006 PASS). Skill `/refactor-arch` is cross-stack proven (Python flat, Node flat, Python partially-organised) and ready for the deliverable wrap (S007 README + S008 acceptance checklist).

## Evidence

- `task-manager-api/src/**`, `task-manager-api/app.py`, `task-manager-api/seed.py`, `task-manager-api/.env.example`.
- `reports/audit-project-3.md` (Findings + Validation block).
- Bootstrap commit hash: `79747f501fced6e29551a49def129dd17fc90009`.

## Risks consumed during execution

- `User.tasks` cascade adoption — required moving from `backref` to `back_populates` on both `User.tasks` and `Task.user` to preserve relationship semantics; smoke `DELETE /users/4` after `POST /users` confirmed clean teardown without orphan rows.
- SQLAlchemy 2.x `case()` syntax — used positional-tuple form `case((cond, val), else_=val)` (the legacy `case([(cond, val)], …)` is deprecated in SA 2.x); summary report aggregation verified live.
- Schema partial-update semantics — `_task_schema.load(payload, partial=True)` returns only present keys, allowing `'tags' in data` / `'status' in data` discrimination without re-implementing.
- Datetime tz handling — `now_utc()` returns naive UTC (`datetime.now(timezone.utc).replace(tzinfo=None)`) to keep comparison-compatible with SQLAlchemy `DateTime` columns that strip tzinfo by default; no `TypeError: can't compare offset-naive and offset-aware datetimes` observed at runtime.
- Port collision history — 5000 (macOS AirPlay), 5050 (project 1 venv possibly cached), 3030/3131 (project 2 ports) — used 5151; clean boot.

## Next step

Author `P001-S007-readme-final.md` (final README sections A/B/C/D per `desafio.md` lines 248-255). See `plans/INDEX.md` cascading authorship rule.

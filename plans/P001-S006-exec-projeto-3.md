# P001-S006 — Execute /refactor-arch on task-manager-api

## Zero-context bootstrap

If resuming with no prior conversation:

1. Read `plans/CURRENT.md`, `plans/P001-skill-refactor-arch.md`, `plans/P001-design-contract.md` — focus on **I-1** (agnostic), **I-5** (boot + smoke), **I-7** (MVC target rule about partially-organised projects: "improve, not rewrite"), **I-10** (≥ 5 findings, ≥ 1 CRIT/HIGH).
2. Read the 6 skill files under `code-smells-project/.claude/skills/refactor-arch/` (canonical source — copy lives at this path).
3. Read `plans/P001-S004-results.md` and `plans/P001-S005-results.md` for the operating pattern (two-part split).
4. Read `plans/P001-S001-findings.md` (task-manager-api block, 10 findings) — used only for calibration cross-check after Phase 2 produces its own report.
5. Skim `desafio.md` lines 163-171 (project-3 checklist).
6. Execute the tasks below in two parts.

## Goal

Execute `/refactor-arch` against `task-manager-api/` (Python + Flask + Flask-SQLAlchemy, ~1150 LOC across `app.py`, `database.py`, `seed.py`, `models/{task,user,category}.py`, `routes/{task,user,report}_routes.py`, `services/notification_service.py`, `utils/helpers.py`).

Project-3 is the **partially-organised** case — it already has `models/`, `routes/`, `services/`, `utils/`. It is missing `config/`, `controllers/`, `middlewares/`, `errors/`, `schemas/`. Constants exist in `utils/helpers.py` but routes do not import them. A complete validator (`process_task_data`) exists but is never called. The skill must **improve** this layout without rewriting working code.

Three outcomes (verdict PASS):

1. Skill tree replicated from `code-smells-project/.claude/skills/refactor-arch/` into `task-manager-api/.claude/skills/refactor-arch/`.
2. Phase 1 prints the canonical summary; Phase 2 writes `reports/audit-project-3.md` and halts on the verbatim prompt.
3. After explicit user `y`, Phase 3 reshapes the existing folders into the MVC tree (moving + augmenting, not rewriting), boots the app, smoke-tests ≥ 15 endpoints from the existing route surface, and records the validation block.

## Operating mode

Same as S004/S005:

- Agent IS the skill runtime.
- Phase-2 halt is enforced literally with the verbatim prompt sentence; end the turn waiting for `y`/`yes`.
- The `improve-not-rewrite` principle is binding. Existing files keep their content unless a catalog finding requires a change; only their *location* changes when moved under `src/`.

## Prerequisite reads (only these)

| Path | Why |
|------|-----|
| `code-smells-project/.claude/skills/refactor-arch/SKILL.md` (and the 5 siblings) | Runtime prompt + knowledge base |
| `task-manager-api/app.py` | Composition site — hard-coded port + SECRET_KEY + blueprint registration |
| `task-manager-api/database.py` | 3-line SQLAlchemy db init |
| `task-manager-api/models/{task,user,category}.py` | ORM models — relationships need cascade |
| `task-manager-api/routes/task_routes.py` (299 LOC) | Heavy: N+1, duplicate validation, bare excepts |
| `task-manager-api/routes/user_routes.py` (211 LOC) | Fake JWT, manual cascade, N+1 in /users/<id>/tasks |
| `task-manager-api/routes/report_routes.py` (223 LOC) | 89-line summary_report — primary business-logic-in-route case |
| `task-manager-api/services/notification_service.py` | Hardcoded SMTP creds |
| `task-manager-api/utils/helpers.py` | Constants present but unused; dead `process_task_data` validator |
| `task-manager-api/seed.py` | Smoke-test prep — seed data so endpoints have something to query |
| `task-manager-api/requirements.txt` | Dependency list (Flask + Flask-SQLAlchemy + flask-cors) |

## Tasks — preamble (step 0)

0. Copy the skill tree:
   ```bash
   cp -R code-smells-project/.claude task-manager-api/.claude
   diff -rq code-smells-project/.claude task-manager-api/.claude
   ```
   Expected: empty diff. 6 files under `task-manager-api/.claude/skills/refactor-arch/`.

## Tasks — Phase 1 (analysis)

1. Apply heuristics from `analise-projeto.md`. Expected (verify before printing):
   - `Language: python`
   - `Framework: python-flask (Flask + Flask-SQLAlchemy)`
   - `Dependencies: flask, flask-cors, flask-sqlalchemy`
   - `Domain: Task Manager API (tasks, users, categories, reports, notifications)`
   - `Architecture: partially-organised — models/, routes/, services/, utils/ present; controllers/, config/, middlewares/ absent`
   - `Source files: ~10 .py files outside seed/tests`
   - `DB tables: tasks, users, categories` (derived from `__tablename__` and relationships)
2. Print Phase-1 block. Continue.

## Tasks — Phase 2 (audit)

3. Iterate `catalog-antipatterns.md`. Apply entries tagged `any`, `python-flask`, `python-generic`.
4. Expected catalog matches for project 3 (verify before writing):
   - **god-class-or-god-module** — likely **zero matches**. Files are already split per domain. Closest is `report_routes.py::summary_report` (89 LOC) but it's a single function in a focused file, not a god module. Report 0 matches honestly.
   - **hardcoded-credentials** (CRITICAL) — `services/notification_service.py:10-11` (SMTP creds), `app.py:13` (SECRET_KEY).
   - **sql-injection-string-concat** — **zero matches** (Flask-SQLAlchemy ORM handles binding).
   - **business-logic-in-route-or-controller** (HIGH) — `report_routes.py:13-101` (89-line summary), `task_routes.py:30-39, 71-80` (overdue computation duplicated 4 sites), `task_routes.py:273-296` (stats aggregation in route).
   - **n+1-query** (HIGH) — `task_routes.py:14-59` (per-task User.query.get + Category.query.get), `report_routes.py:30-43, 53-68` (overdue loop + per-user filter_by), `user_routes.py:153-183` (per-task overdue).
   - **bare-except-or-catch-all** (MEDIUM) — `task_routes.py:62-63, 137-138, 204-205, 236-238`, `report_routes.py:186-188, 207-209, 221-223`.
   - **duplicate-validation-logic** (MEDIUM) — `task_routes.py:92-144 vs 166-213` (create vs update validation drift) + `utils/helpers.py:57-108` (dead `process_task_data` validator that no route imports).
   - **deprecated-api-call** (MEDIUM) — check for `Task.query.get(...)` patterns (SQLAlchemy 2.x replaces with `db.session.get(Model, id)`); `datetime.utcnow()` (deprecated 3.12+). Both expected to fire multiple times.
   - **magic-numbers-or-inline-whitelist** (LOW) — `task_routes.py:32, 110-113, 177, 182, 243` (inline status/priority literals) **plus** the "constants exist but unused" sub-pattern: `utils/helpers.py:110-116` defines `VALID_STATUSES`, `MAX_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY` but no route imports them.
   - **inconsistent-response-envelope** (LOW) — verify whether routes mix shapes. Quick grep: routes return `jsonify(dict)`, `jsonify(list)`, `jsonify({'error': ...})`, `jsonify(report)`. Multiple shapes present.
5. Build findings using `template-relatorio.md` schema. Sort CRIT → LOW.
6. Write `reports/audit-project-3.md`. Header: `Project: task-manager-api`, `Stack: Python + Flask + Flask-SQLAlchemy`, `Files: <N> analyzed | ~1150 lines of code`.
7. **Calibration cross-check** against S001 (target 10, distribution 1/3/3/3). Expected delta:
   - **Residuals** (S001 findings without v1 catalog slug):
     - `fake-JWT issuance` — `routes/user_routes.py:210` returns `{'token': 'fake-jwt-token-' + str(user.id)}`. No catalog slug — same family as project 2's `fake-or-broken-crypto`. RESIDUAL.
     - `missing-auth-middleware-on-protected-routes` — no `@require_auth` anywhere; every endpoint open. No catalog slug. RESIDUAL.
     - `missing-orm-cascade-or-manual-fk-cleanup` — `routes/user_routes.py:140-142` manually deletes user's tasks before deleting the user. Same as project 2's residual #2. RESIDUAL.
     - `unused-imports` — `task_routes.py:7 (json, os, sys, time)`, `user_routes.py:6 (hashlib, json)`, `report_routes.py:8 (json)`, `helpers.py:3-7 (os, json, sys, math, hashlib)`. No catalog slug. RESIDUAL.
     - `type(x) == list instead of isinstance` — `task_routes.py:141, 210`, `helpers.py:103`. No catalog slug. RESIDUAL.
   - Net expected: ~8 findings (1 CRIT, 2 HIGH, 3 MED, 2 LOW) with 5 residuals.
8. Print the report.
9. Surface the verbatim halt prompt as the last line. End the turn.

## Tasks — Phase 3 (refactor + validate)

Execute only on explicit user `y`.

10. **Reorganise existing folders into src/** (per the `improve-not-rewrite` principle):
    - Move `models/` → `src/models/` (no content edits beyond cascade addition + Task.query.get migration to db.session.get).
    - Move `routes/` → `src/views/` (rename file pattern from `*_routes.py` kept; routes become thin dispatchers).
    - Move `services/` → `src/services/` (with SMTP env-loading patch).
    - Move `utils/` → `src/utils/` (delete dead `process_task_data` OR adopt it as the canonical validator — pick one).
    - Move `database.py` content into `src/models/__init__.py` (or keep at root and import from `src.models`).
11. **Create new layers** missing in project 3:
    - `src/config/{settings.py, constants.py}` — move all constants from `utils/helpers.py:110-116` here (`VALID_STATUSES`, `MAX_TITLE_LENGTH`, etc.); load `SECRET_KEY`, `DB_URI`, SMTP creds from env.
    - `src/controllers/{task,user,report,category}_controller.py` — extract business logic from routes. Overdue computation (currently duplicated 4 sites) becomes `task_controller.compute_overdue(task)`. Summary report (89 LOC route) becomes `report_controller.build_summary()`.
    - `src/middlewares/error_handler.py` — single `@app.errorhandler(Exception)` mapping AppError subclasses to JSON envelope.
    - `src/errors/__init__.py` — `AppError`, `NotFoundError`, `ValidationError`, `AuthError`, `ConflictError`.
    - `src/schemas/{task,user,category}_schema.py` — adopt `process_task_data` as `task_schema.validate(data, partial=False)` and write parallels for user/category; delete inline validation in routes.
    - `src/views/response.py` — `success(data, message=None, http=200)` / errors flow through middleware.
12. Apply playbook recipes in order:
    1. `extract-config-to-env-or-settings-module` — SECRET_KEY, SMTP creds, DB URI to env; add `.env.example`.
    2. `replace-deprecated-api-call-with-current-equivalent` — replace every `Model.query.get(id)` with `db.session.get(Model, id)`; replace `datetime.utcnow()` with `datetime.now(datetime.UTC)`.
    3. `eager-load-relationships-to-fix-n+1` — use `joinedload(Task.user)` and `joinedload(Task.category)` in `task_controller.list_tasks()`; rewrite `/reports/summary` user-productivity loop as a `func.count()` group-by query; same for `/users/<id>/tasks`.
    4. `move-business-logic-from-route-to-controller` — overdue computation centralised; summary report fully in controller; stats aggregation moves out of `task_stats` route.
    5. `replace-bare-except-with-typed-handler-and-error-middleware` — install error handler; remove all 7+ bare-except blocks; routes raise typed errors.
    6. (Same recipe #4) — eliminate duplicate validation by adopting `process_task_data` (now `task_schema.validate`).
    7. `lift-magic-numbers-and-whitelists-into-constants-module` — constants in `src/config/constants.py`; routes/controllers/schemas import them.
    8. `replace-bare-except-with-typed-handler-and-error-middleware` (extending) — all responses through `src/views/response.py::success()`; errors through middleware.
13. **Add SQLAlchemy cascade** on `User.tasks` relationship: `db.relationship('Task', backref='user', cascade='all, delete-orphan')`. Simplifies the manual loop in `delete_user` (still residual since the catalog has no slug for it, but the structural fix is small enough to apply as part of the model move and the related N+1 fix).

    Note: this is a small bleed beyond strict v1 catalog scope, justified because the relationship declaration is the natural ORM-side artefact of moving the model to `src/models/`. Document the bleed in the audit Validation block.
14. Reshape `app.py` to be a composition root: load env → build Flask → register blueprints from `src/views/` → register error middleware → init DB → if `__main__`, run on `settings.PORT`.
15. Update `database.py` to either disappear (import db from `src/models/__init__.py`) or remain as a 1-line `from src.models import db` shim if other parts of the code still import it.
16. Run layering grep checks (per `guidelines-arquitetura.md`). Fix any violations.
17. Run `pip install -r requirements.txt` if not already installed.
18. Run `python seed.py` (or call its seed function from the test setup) to populate test data — `task-manager-api` ships with a `seed.py`. If seed fails after the refactor, fix it before booting.
19. Boot. Command: `SECRET_KEY=test-do-not-commit DEBUG=false PORT=5151 python app.py` (5000 occupied by AirPlay; 5050 used by project 1 still possibly cached; pick a fresh port).
20. Smoke-test the route surface. **Minimum 15 endpoints** to cover task / user / report / category families:
    1. `GET /` → 200
    2. `GET /health` → 200
    3. `GET /tasks` → 200 (N+1 fix verified — single eager-loaded query)
    4. `POST /tasks` with valid body → 201
    5. `GET /tasks/<id-just-created>` → 200
    6. `PUT /tasks/<id>` with `{status: "done"}` → 200
    7. `DELETE /tasks/<id>` → 200
    8. `GET /tasks/search?q=test` → 200
    9. `GET /tasks/stats` → 200
    10. `GET /users` → 200
    11. `POST /users` with valid body → 201
    12. `POST /login` with seeded creds → 200 (token still returned, but documented as residual)
    13. `GET /reports/summary` → 200 (N+1 fix verified — aggregate query)
    14. `GET /reports/user/<id>` → 200
    15. `GET /categories` → 200
    16. `POST /categories` with valid body → 201
    17. `PUT /categories/<id>` → 200
    18. `DELETE /categories/<id>` → 200
21. Append `## Validation` to `reports/audit-project-3.md` with boot command, outcome, endpoint table (Method × Endpoint × HTTP × Pass?), regressions, residuals.
22. If any endpoint regresses, revert breaking change and re-run.

## Tasks — closeout

23. Write `plans/P001-S006-results.md` — verdict `PASS`.
24. Update `plans/INDEX.md`: S006 → `done | PASS`, S007 → `authorable`.
25. Update `plans/CURRENT.md`.
26. Clear `plans/LOCKS.json`.
27. Two-commit pattern (bootstrap + hash).

## Definition of done

- `task-manager-api/.claude/skills/refactor-arch/` is a verbatim copy of project 1's (6 files).
- `reports/audit-project-3.md` exists; ≥ 5 findings; ≥ 1 CRIT/HIGH; calibration block documents residuals.
- Phase-2 halt surfaced literally; user `y` recorded.
- `task-manager-api/src/{config,models,views,controllers,services,middlewares,errors,schemas}/` exists; each layer populated.
- Original `models/`, `routes/`, `services/`, `utils/` at project root **moved into `src/`**, not left in place.
- Layering grep checks pass.
- Skill tree under `.claude/skills/refactor-arch/` unchanged.
- App boots with `python app.py` (after exporting `SECRET_KEY`); ≥ 15 endpoints respond with expected status; 0 regressions.
- Plan files updated; lock cleared; two commits landed.

## Out of scope

- Catalog/playbook edits — frozen.
- Fixing the 5 residuals (fake-JWT, missing-auth, missing-cascade structurally not added beyond the model relationship declaration, unused imports, `type(x) == list`).
- Real JWT implementation, password hashing for users — not in v1 playbook.
- Test suite authoring beyond smoke.

## Risks specific to this session

- **Improve-not-rewrite discipline.** Existing models, routes, services have working content. Phase 3 must preserve behaviour line-by-line where possible — only relocate files and extract business logic. A wholesale rewrite of `routes/task_routes.py` invalidates the principle.
- **SQLAlchemy `query.get` migration impact.** Replacing every `Model.query.get(id)` with `db.session.get(Model, id)` touches ~25 call sites. Mitigation: do this as a single mechanical pass (sed-equivalent), then run all smoke tests at once to catch any miss.
- **Overdue duplication is structural.** The 4 sites computing "is task overdue" all read `t.due_date`, `t.status`, `datetime.utcnow()`. Centralising in `task_controller.compute_overdue` requires updating ALL 4 call sites; missing one leaves drift. Mitigation: grep for `datetime.utcnow()` and `due_date < ` after the refactor; both should appear only inside the controller.
- **Adopting `process_task_data` vs. deleting it.** The dead validator in `utils/helpers.py:57-108` could be the new schema, OR it could be deleted. Decision: **adopt it as `src/schemas/task_schema.py::validate`**. Delete the inline blocks in `task_routes.py`. Single source of truth.
- **`User.tasks` cascade is a structural change.** Adding `cascade='all, delete-orphan'` removes the need for the manual loop in `delete_user`, but if any other code depends on the manual loop semantics, behaviour changes. Mitigation: simplify `delete_user` controller to `db.session.delete(user); db.session.commit()` and verify by smoke-deleting a user with tasks.
- **`seed.py` invocation timing.** Seed must run before smoke tests but probably should NOT run on every app boot (it inserts test data). Mitigation: run `python seed.py` once after DB init, before booting the server for smoke tests; document the boot+seed sequence in the validation block.
- **Port collision history.** Ports 5000 (AirPlay), 5050 (project 1 cached if not killed), 3030 (Docker), 3131 (project 2 cached). Use 5151 for project 3.
- **Existing relative imports.** Files like `routes/task_routes.py` use `from database import db`, `from models.task import Task`. After moving to `src/`, those imports must become `from src.models import db` etc. Mitigation: do this as a mechanical pass file-by-file; the layering grep checks catch any miss.

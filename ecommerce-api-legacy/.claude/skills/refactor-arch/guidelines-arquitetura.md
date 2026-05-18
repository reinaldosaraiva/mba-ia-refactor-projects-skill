---
schema_version: 1
target_layout: mvc
layers: [config, models, views, controllers, services, middlewares]
---

# Phase-3 target architecture

The contract for what the refactored project must look like after Phase 3. Anchored to the example tree in `desafio.md` lines 74-86 and to the MVC pattern. Framework-specific bindings live at the bottom of this file.

## Target directory tree

```
<project-root>/
├── src/
│   ├── config/
│   │   ├── settings.py     (or settings.js)
│   │   └── constants.py
│   ├── models/
│   │   ├── <domain>_model.py    (one file per entity)
│   │   └── ...
│   ├── views/
│   │   └── routes.py       (Flask: blueprints; Express: Routers)
│   ├── controllers/
│   │   ├── <domain>_controller.py
│   │   └── ...
│   ├── services/
│   │   └── <concern>_service.py    (notification, cache, payment, audit)
│   ├── middlewares/
│   │   └── error_handler.py
│   ├── schemas/            (validation schemas — non-MVC, alongside)
│   ├── errors/             (custom exceptions — non-MVC, alongside)
│   └── utils/              (pure helpers — non-MVC, alongside)
└── app.py                  (or app.js — composition root only)
```

The entry point (`app.py` / `app.js`) lives at the repository root, *outside* `src/`. It is the composition root: it builds the framework instance, registers middleware, mounts routes, and starts the server. It contains no business logic.

`reports/`, `tests/`, `.env.example`, and `requirements.txt` / `package.json` live at the repository root alongside the entry point. None of them are part of the source tree.

## Per-layer roles

### src/config/

Holds environment-loaded configuration and named constants. Reads from `os.environ` / `process.env`. Provides no defaults for secrets; provides safe defaults only for non-sensitive flags (DEBUG, PORT). Imports nothing from `src/`.

### src/models/

Data-access layer. One module per domain entity (`produto_model.py`, `pedido_model.py`, `task_model.py`). Owns ORM mappings, queries, and persistence operations. Returns plain data structures or model instances — never HTTP objects, never response envelopes. Imports `src/config/` only.

### src/views/

The HTTP edge. Maps URL → controller call. Each route function is at most 5–10 lines: parse input via schema, call controller, wrap result in response envelope. Routes do not import models directly; they go through controllers. For Flask, prefer one Blueprint per domain in `src/views/<domain>_routes.py` (or a single `routes.py` registering all). For Express, one Router per domain.

### src/controllers/

The orchestration layer. One module per domain. Each function takes parsed input (already validated), calls one or more models and services, and returns a domain result. Controllers own business rules and side-effect dispatch. They import models and services; they do not import views.

### src/services/

Cross-cutting concerns: notifications, caching, payments, audit, authentication strategy. Each service is an interface or a class with a stable contract so it can be mocked in tests. Services import models when they need persistence; they do not import controllers or views.

### src/middlewares/

Framework-level interceptors that run on every request or every error: error handler, auth check, request logging, CORS. Middlewares do not own business logic. The error handler in particular is the single place that maps exceptions to HTTP responses through the canonical envelope.

### app.py / app.js (composition root)

The only file that imports from all six layers. It builds the framework instance, applies middleware, registers routes, opens the DB connection (or installs the app-context teardown), then starts the server. Reads the entire config object from `src/config/settings`. No `if request...`, no business rules, no SQL.

## Layering rules

Direction of allowed imports:

```
            app (composition root)
             │
   ┌─────────┼─────────┐
   ▼         ▼         ▼
middlewares  views ── controllers ── services
                          │              │
                          ▼              ▼
                       models <───── (optional)
                          │
                          ▼
                        config
```

Mechanical checks (operator runs each after Phase 3):

```bash
# Routes must not import models directly
grep -rEn 'from src\.models' src/views/ && echo "VIOLATION: views import models"
# Models must not import controllers or views
grep -rEn 'from src\.(controllers|views)' src/models/ && echo "VIOLATION: models import upward"
# Controllers must not import views
grep -rEn 'from src\.views' src/controllers/ && echo "VIOLATION: controllers import views"
# Middlewares own no business logic — heuristic: no imports from models or controllers
grep -rEn 'from src\.(models|controllers)' src/middlewares/ && echo "VIOLATION: middleware reaches into domain"
# Composition root owns the wiring — app.py should be the only file importing from >= 3 src/ subdirs
grep -cE 'from src\.' app.py
```

A clean refactor returns no violations from the first four checks and shows ≥ 3 distinct `src/*` imports from the last (the composition).

## Naming convention

Inherits the workspace standard from `~/CLAUDE.md`:

| Element | Convention | Examples |
|---------|------------|----------|
| Files | `<domain>_<role>.<ext>` (singular) | `produto_model.py`, `pedido_controller.py`, `notification_service.py` |
| Classes | singular PascalCase | `Produto`, `Pedido`, `NotificationService` |
| Routes (URL paths) | plural snake-case | `/produtos`, `/pedidos`, `/api/v1/tasks` |
| DB tables | plural snake-case | `produtos`, `usuarios`, `tasks` |

Constants in `src/config/constants.py` use UPPER_SNAKE_CASE. Enums use PascalCase with member names in UPPER_SNAKE_CASE or PascalCase consistent across the project.

## Where non-MVC bits live

These directories sit alongside the MVC layers, not within them:

- **`src/schemas/`** — input validation schemas (marshmallow / pydantic / zod / joi / express-validator). Imported by controllers and by views. One schema module per domain.
- **`src/errors/`** — custom exception classes (`AppError`, `NotFoundError`, `ValidationError`, `AuthError`). Raised by controllers/models, caught by the error-handler middleware. Each error class declares its `code` (string) and `http` (status) so the middleware can map deterministically.
- **`src/utils/`** — pure helpers (date formatting, percentage calculation, generic string operations). No imports from `models`, `controllers`, `views`. If a util needs DB access, it belongs in a service or a model, not in utils.

Schemas, errors, and utils are not layers in the MVC sense — they are libraries the layers consume.

## Framework-specific bindings

### Flask (Python)

- Composition root: `app.py` at repo root, imports `from src.config import settings`, builds `app = Flask(__name__)`, applies CORS, registers blueprints from `src.views`, registers the error handler from `src.middlewares.error_handler`.
- Views: `src/views/<domain>_routes.py` defines `<domain>_bp = Blueprint(...)` and registers handlers; `src/views/__init__.py` exports `register_blueprints(app)` that wires every blueprint.
- Models: `src/models/<domain>_model.py` defines `class Produto(db.Model)` (Flask-SQLAlchemy) or function modules wrapping a connection (raw sqlite3). Initialise SQLAlchemy in `src/models/__init__.py` exporting `db = SQLAlchemy()`; `app.py` calls `db.init_app(app)`.
- Error handler: `src/middlewares/error_handler.py` exposes `register(app)` that wires `@app.errorhandler(AppError)` and `@app.errorhandler(Exception)` returning the canonical envelope.

### Express (Node.js)

- Composition root: `app.js` at repo root, imports `const settings = require('./src/config/settings')`, builds `const app = express()`, applies `express.json()`, mounts Routers from `src/views`, then `app.use(require('./src/middlewares/error_handler'))` *last* so it catches errors from preceding handlers.
- Views: `src/views/<domain>_routes.js` exports a `Router` instance with the handler functions attached; `app.js` mounts each at the appropriate prefix.
- Models: `src/models/<domain>_model.js` exposes async functions returning plain objects; database client comes from `src/config/database.js` constructed once and exported.
- Error handler: `src/middlewares/error_handler.js` exports `function (err, req, res, next) { ... }` with the four-argument signature Express requires for error-handling middleware.

## Acceptance signals for Phase 3

A refactor satisfies this contract when every item below is true. The operator records the result of each in the Phase-2 audit report's `Validation` section.

1. The directory tree above is present; `src/{config,models,views,controllers,services,middlewares}` all exist with at least one file each (services/middlewares may have only the error-handler / notification stub if the domain is small).
2. The composition root (`app.py` / `app.js`) is the only file at repository root that imports from `src/`; it has no business logic.
3. No secrets remain in tracked source. `git grep` for the original literals returns zero matches outside `src/config/`.
4. The five layering-rule grep checks above return no violations.
5. The application boots with the original entry-point command (`python app.py` / `node app.js` / `flask run`).
6. The smoke-test endpoint table in the audit report has zero `Pass? = NO` rows; or, if any rows are NO, the residual is justified in writing.

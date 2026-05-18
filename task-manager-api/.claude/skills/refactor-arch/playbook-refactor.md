---
total_recipes: 8
catalog_slugs_covered: [god-class-or-god-module, hardcoded-credentials, sql-injection-string-concat, business-logic-in-route-or-controller, n+1-query, bare-except-or-catch-all, duplicate-validation-logic, deprecated-api-call, magic-numbers-or-inline-whitelist, inconsistent-response-envelope]
stacks_covered: [python-flask, python-generic, nodejs-express, nodejs-generic]
schema_version: 1
---

# Refactor playbook

Concrete transformation recipes consumed by the `/refactor-arch` skill during Phase 3 (refactor). Each recipe targets one or more catalog slugs from `catalog-antipatterns.md`. Before/After blocks are minimal but representative — they show the shape change, not a full diff.

The target architecture across all recipes is the MVC layout defined in `desafio.md` lines 74-86 and in `guidelines-arquitetura.md` (authored in S003):

```
src/
├── config/settings.py        # env-loaded config + constants
├── models/<domain>_model.py  # data access, ORM mappings
├── views/routes.py           # URL → controller mapping (thin)
├── controllers/<domain>_controller.py  # request handling, calls models + services
├── services/<concern>_service.py       # cross-cutting concerns (auth, email, cache)
├── middlewares/error_handler.py        # @app.errorhandler / app.use
└── app.py                    # composition root (Flask app or Express app)
```

---

## extract-config-to-env-or-settings-module

- **Fixes catalog entries:** hardcoded-credentials
- **Applies to:** any
- **When to apply:** the audit finds a literal credential, signing key, SMTP password, or payment-provider key in any non-config file.
- **Steps:**
  1. Create `src/config/settings.py` (Python) or `src/config/settings.js` (Node) if it does not exist.
  2. For every flagged literal, define a config attribute that reads from `os.environ` (Python) or `process.env` (Node), with a safe default *only* for non-secret values (DEBUG, PORT). Secrets have no default — let the app fail fast.
  3. Replace the literal at its call site with an import from the config module.
  4. Add a `.env.example` documenting every required variable.
  5. Add `.env` to `.gitignore` if not already present.
  6. Where the same literal leaked through a log or HTTP response (e.g. `/health` exposing the secret), remove that exposure.

### Before

```python
# app.py (Flask)
from flask import Flask
app = Flask(__name__)
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```

### After

```python
# src/config/settings.py
import os
SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# src/app.py
from flask import Flask
from src.config import settings
app = Flask(__name__)
app.config["SECRET_KEY"] = settings.SECRET_KEY
app.config["DEBUG"] = settings.DEBUG
```

### Validation hint

Run `git grep -nE "(SECRET_KEY|password|token|api_key|pk_live_|sk_live_)\s*[=:]\s*['\"][a-zA-Z0-9_-]+['\"]" -- ':!src/config/' ':!*.env*' ':!*test*'` — expect zero matches in source. App must boot successfully when `SECRET_KEY` is exported and fail-fast (KeyError) when it is not.

---

## split-god-class-into-controllers-by-domain

- **Fixes catalog entries:** god-class-or-god-module
- **Applies to:** any
- **When to apply:** the audit finds a file > 200 LOC mixing handlers/data-access/business-rules for ≥ 2 domain entities, or a `*Manager` class doing constructor-DB-init + route-registration + business logic.
- **Steps:**
  1. List the distinct domain entities the god-module touches (e.g. produto, usuario, pedido, relatório).
  2. Create one controller module per entity under `src/controllers/`. Each module owns the request/response handling for that entity only.
  3. Move data-access calls into one model module per entity under `src/models/` (or `src/repositories/`).
  4. Create `src/views/routes.py` whose only job is to import controllers and bind URL rules.
  5. Reduce the original entry-point (`app.py`/`app.js`) to a composition root: build the framework instance, register the error-handler middleware, and call `routes.register(app)`.
  6. Delete the god-class after every consumer has been re-wired.

### Before

```python
# controllers.py (290 lines, 17 handlers, 4 domains, business logic + notifications inline)
def listar_produtos(): ...
def criar_produto(): ...
def listar_usuarios(): ...
def criar_pedido():
    # validation + model write + notifications via print() + response formatting
    ...
def relatorio_vendas(): ...
```

### After

```python
# src/controllers/produto_controller.py
from flask import request, jsonify
from src.models import produto_model
def listar(): return jsonify(produto_model.todos())
def criar(): ...

# src/controllers/pedido_controller.py
from src.services.notification_service import NotificationService
def criar(notification: NotificationService):
    ...
    notification.pedido_criado(pedido_id, usuario_id)
    return ...

# src/views/routes.py
from src.controllers import produto_controller, pedido_controller
def register(app):
    app.add_url_rule("/produtos", "produtos.listar", produto_controller.listar, methods=["GET"])
    app.add_url_rule("/pedidos", "pedidos.criar", pedido_controller.criar, methods=["POST"])
```

### Validation hint

`wc -l src/controllers/*.py` shows every controller < 120 LOC. Each controller imports models for **one** domain only (`grep -l "from src.models" src/controllers/*.py | xargs -I{} sh -c 'echo {}: $(grep -c "from src.models" {})'`). The original god-module file no longer exists or contains only an import-redirect stub.

---

## replace-raw-sql-with-parameterised-queries

- **Fixes catalog entries:** sql-injection-string-concat
- **Applies to:** python-flask, python-generic, nodejs-express, nodejs-generic
- **When to apply:** any `cursor.execute(<concat>)` / `db.run(\`...${x}\`)` pattern found by the audit.
- **Steps:**
  1. For each flagged call, replace concatenation/interpolation with the driver's placeholder syntax — `?` for sqlite3 (Python and Node), `%s` for psycopg2, `:name` for sqlalchemy.text, `$1` for postgres node-postgres.
  2. Pass the request-derived values as a tuple/array second argument to `execute()`.
  3. If the project is building dynamic WHERE clauses (search endpoints), build the SQL fragment with whitelisted column names and use placeholders only for the values.
  4. Delete any endpoint that executes raw user-supplied SQL (`/admin/query`, `/debug/exec`).
  5. As a follow-up, migrate models to SQLAlchemy or another ORM to make injection impossible by construction.

### Before

```python
# models.py
def get_produto_por_id(id):
    cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))

def login_usuario(email, senha):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
    )

def buscar_produtos(termo, categoria):
    query = "SELECT * FROM produtos WHERE 1=1"
    if termo:    query += " AND nome LIKE '%" + termo + "%'"
    if categoria: query += " AND categoria = '" + categoria + "'"
    cursor.execute(query)
```

### After

```python
# src/models/produto_model.py
def get_por_id(id):
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))

# src/models/usuario_model.py
def login(email, senha_hash):  # senha now hashed before this call
    cursor.execute(
        "SELECT id, nome, email, tipo FROM usuarios WHERE email = ? AND senha = ?",
        (email, senha_hash),
    )

# src/models/produto_model.py
def buscar(termo=None, categoria=None):
    clauses, params = ["1=1"], []
    if termo:
        clauses.append("(nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        clauses.append("categoria = ?")
        params.append(categoria)
    sql = "SELECT * FROM produtos WHERE " + " AND ".join(clauses)
    cursor.execute(sql, params)
```

### Validation hint

`git grep -nE "execute\s*\(\s*[fF]?[\"'][^?]*\+" -- '*.py'` returns nothing. `git grep -nE "db\.(run|get|all)\s*\(\s*\`[^\`]*\\\$\{"` returns nothing in Node files. Login endpoint with payload `{"email": "x' OR 1=1 --", "senha": "y"}` returns 401, not 200.

---

## eager-load-relationships-to-fix-n+1

- **Fixes catalog entries:** n+1-query
- **Applies to:** any
- **When to apply:** the audit finds a query inside a `for`/`forEach` loop after an initial collection query, or a route whose latency grows linearly with row count.
- **Steps:**
  1. Identify the parent collection and the related rows being looked up per parent.
  2. Replace the loop+per-row-query with a single JOIN (raw SQL) or an eager-loading option (`joinedload`/`selectinload` in SQLAlchemy, `include` in Prisma, `populate` in Mongoose, knex `.withGraphFetched`).
  3. Group the joined rows in code (Python: `itertools.groupby` after sort by parent id; JS: reduce by parent id into a Map).
  4. If the relationship is many-to-many or has counts, prefer a second batched query (`WHERE parent_id IN (?, ?, ?, ...)`) over join multiplication.
  5. Move the resulting batched access into a repository method on the model module — keep controllers ignorant of the optimisation.

### Before

```python
# models.py — get_pedidos_usuario does 1 + N + N×M queries
def get_pedidos_usuario(usuario_id):
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    pedidos = cursor.fetchall()
    result = []
    for p in pedidos:
        cursor2 = db.cursor()
        cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (p["id"],))
        itens = cursor2.fetchall()
        for it in itens:
            cursor3 = db.cursor()
            cursor3.execute("SELECT nome FROM produtos WHERE id = ?", (it["produto_id"],))
            ...
```

### After

```python
# src/models/pedido_model.py — single JOIN, group by pedido in Python
from collections import defaultdict
def por_usuario(usuario_id):
    cursor.execute(
        """
        SELECT p.id AS pedido_id, p.status, p.total, p.criado_em,
               ip.produto_id, ip.quantidade, ip.preco_unitario,
               pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        WHERE p.usuario_id = ?
        ORDER BY p.id
        """,
        (usuario_id,),
    )
    grouped = defaultdict(lambda: {"itens": []})
    for row in cursor.fetchall():
        head = grouped[row["pedido_id"]]
        head.update({"id": row["pedido_id"], "status": row["status"], "total": row["total"]})
        if row["produto_id"] is not None:
            head["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(grouped.values())
```

### Validation hint

Enable SQL echo (Python: `sqlite3.connect(..., factory=...)` with a counting wrapper; Node: pre-route middleware logging every `db.run`). Hit the affected endpoint with seed data containing 10+ parents; expect O(1) queries, not O(N). Add a regression test using a query-count fixture.

---

## move-business-logic-from-route-to-controller

- **Fixes catalog entries:** business-logic-in-route-or-controller, duplicate-validation-logic
- **Applies to:** any
- **When to apply:** route handler > 40 LOC, route doing aggregation/dispatch/computation, or duplicate validation blocks between POST and PUT for the same resource.
- **Steps:**
  1. Identify the pure-business portion of the route (validation, computation, side-effect dispatch).
  2. Move it to `src/controllers/<domain>_controller.py` as a function that takes parsed input and returns a result (no HTTP types in or out).
  3. Move validation rules to `src/schemas/<domain>_schema.py` using marshmallow / pydantic / zod / joi / express-validator. Both POST and PUT import the same schema; PUT marks fields as optional.
  4. Wrap notification/email/audit side effects behind `src/services/<concern>_service.py` interfaces so they are mockable.
  5. The route file now only: parse → call schema.validate → call controller → wrap in response envelope.
  6. Run the schema in `partial=True` mode for updates to allow missing fields.

### Before

```python
# routes/report_routes.py — 89-line summary_report
@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    total_tasks = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    ...
    all_tasks = Task.query.all()
    overdue_count = 0
    overdue_list = []
    for t in all_tasks:
        if t.due_date and t.due_date < datetime.utcnow() and t.status not in ('done', 'cancelled'):
            overdue_count += 1
            overdue_list.append({...})
    ...
    return jsonify(report), 200
```

### After

```python
# src/controllers/report_controller.py
from src.models import task_repository
from src.config.constants import TERMINAL_STATUSES
from datetime import datetime, UTC
def build_summary():
    stats = task_repository.aggregate_by_status_and_priority()
    overdue = task_repository.overdue(reference=datetime.now(UTC), exclude=TERMINAL_STATUSES)
    recent = task_repository.recent_activity(window_days=7)
    productivity = task_repository.per_user_productivity()
    return {
        "overview": stats.overview, "tasks_by_status": stats.by_status,
        "tasks_by_priority": stats.by_priority, "overdue": overdue,
        "recent_activity": recent, "user_productivity": productivity,
    }

# src/views/report_routes.py
from flask import Blueprint, jsonify
from src.controllers import report_controller
report_bp = Blueprint('reports', __name__)
@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(report_controller.build_summary()), 200
```

### Validation hint

`awk '/@app\.route|@.*_bp\.route/,/^def /' src/views/*.py | grep -c '^def ' ` shows every route function < 15 LOC (count handler lines via inspection or a helper script). No `Task.query` / `User.query` / direct ORM calls in any route file: `git grep -l '\.query\.' src/views/` returns nothing. Same schema imported by POST and PUT for each resource.

---

## replace-bare-except-with-typed-handler-and-error-middleware

- **Fixes catalog entries:** bare-except-or-catch-all, inconsistent-response-envelope
- **Applies to:** any
- **When to apply:** the audit finds bare `except:` blocks, `except Exception as e: ... str(e)` leak patterns, empty Node catches, or response-shape drift across endpoints.
- **Steps:**
  1. Create `src/middlewares/error_handler.py` (Flask) or `src/middlewares/error_handler.js` (Express) exporting one error handler that logs via `logging.exception` / `winston.error` and returns the canonical envelope `{"status": "error", "error": {"code": <str>, "message": <str>}}`.
  2. Create `src/views/response.py` / `src/views/response.js` exporting `success(data, message=None, http=200)` returning `{"status": "ok", "data": ..., "message": ...}`.
  3. Define domain exceptions (`NotFoundError`, `ValidationError`, `AuthError`) under `src/errors/`; map each to an HTTP status in the error handler.
  4. Rip out every per-route `try/except`. Routes raise; the handler responds.
  5. Replace every `res.send("text")` / `jsonify({"erro": ...})` with `success(...)` / raising a typed error.
  6. Register the error handler last (Flask: `app.register_error_handler`; Express: `app.use(error_handler)` after all routes).

### Before

```python
# code-smells-project/controllers.py — same pattern in 17 handlers
def buscar_produto(id):
    try:
        produto = models.get_produto_por_id(id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        else:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
```

### After

```python
# src/errors/__init__.py
class AppError(Exception):
    code = "internal_error"; http = 500
class NotFoundError(AppError):
    code = "not_found"; http = 404

# src/middlewares/error_handler.py
import logging
from flask import jsonify
def register(app):
    @app.errorhandler(Exception)
    def handle(exc):
        logging.exception(exc)
        if isinstance(exc, AppError):
            return jsonify({"status": "error", "error": {"code": exc.code, "message": str(exc)}}), exc.http
        return jsonify({"status": "error", "error": {"code": "internal_error", "message": "Internal Server Error"}}), 500

# src/views/response.py
from flask import jsonify
def success(data, message=None, http=200):
    payload = {"status": "ok", "data": data}
    if message: payload["message"] = message
    return jsonify(payload), http

# src/controllers/produto_controller.py
from src.errors import NotFoundError
from src.views.response import success
from src.models import produto_model
def buscar(id):
    produto = produto_model.por_id(id)
    if not produto: raise NotFoundError(f"Produto {id} não encontrado")
    return success(produto)
```

### Validation hint

`git grep -nE '^\s*except\s*:\s*$' -- '*.py'` returns nothing. `git grep -nE 'catch\s*\(\s*\w*\s*\)\s*\{\s*\}' -- '*.js'` returns nothing. All successful responses share keys `{status, data}`; all errors share `{status, error: {code, message}}`. Hit a 500-inducing path; response payload contains generic message (not a Python traceback).

---

## replace-deprecated-api-call-with-current-equivalent

- **Fixes catalog entries:** deprecated-api-call
- **Applies to:** any
- **When to apply:** any of the deprecated signals enumerated in the catalog entry. Required per `desafio.md` line 144.
- **Steps:**
  1. Audit reports the offending call site with its current and target API.
  2. Replace the deprecated symbol with its current equivalent in place.
  3. If the deprecated call had side effects (e.g. `before_first_request` running once), wire the replacement into the new startup hook (`with app.app_context(): ...` at app construction, or an explicit `init()` function called from the composition root).
  4. Bump the affected library version in `requirements.txt` / `package.json` if the deprecation is tied to a version range.
  5. Add the deprecation pattern to a project lint rule (ruff, eslint) so it cannot regress.

### Before

```javascript
// ecommerce-api-legacy/src/AppManager.js
const sqlite3 = require('sqlite3').verbose();
// ...
const buf = new Buffer(payload);
const cipher = crypto.createCipher('aes-256-cbc', key);
```

```python
# code-smells-project/app.py (hypothetical deprecation site)
from flask import Flask
app = Flask(__name__)
@app.before_first_request
def init():
    get_db()
```

### After

```javascript
// src/config/database.js
const sqlite3 = require('sqlite3');  // .verbose() chain dropped (no-op in modern versions)
// ...
const buf = Buffer.from(payload);
const iv = crypto.randomBytes(16);
const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
```

```python
# src/app.py
from flask import Flask
from src.config.database import init_db
app = Flask(__name__)
with app.app_context():
    init_db()  # replaces before_first_request which was removed in Flask 2.3+
```

### Validation hint

`grep -nE "require\(['\"]sqlite3['\"]\)\.verbose\(\)" src/` → no matches. `grep -nE "new Buffer\(" src/` → no matches. `grep -nE "createCipher\(" src/` → no matches (only `createCipheriv`). `grep -nE "before_first_request" src/` → no matches. App boots; first-request initialisation observed in startup logs once, not per request.

---

## lift-magic-numbers-and-whitelists-into-constants-module

- **Fixes catalog entries:** magic-numbers-or-inline-whitelist
- **Applies to:** any
- **When to apply:** the audit finds numeric thresholds, inline status lists, or whitelist arrays embedded in routes/controllers, OR a constants module that exists but is not imported by the code that needs it.
- **Steps:**
  1. Create or consolidate `src/config/constants.py` / `src/config/constants.js`. Group constants by domain (TASK_*, USER_*, PRODUCT_*).
  2. For every flagged literal, define a named constant (UPPER_SNAKE_CASE) with a comment explaining the business rule when it is not self-evident.
  3. Replace the literal at its call site with an import from the constants module.
  4. Move enum-style string sets into an actual Enum (`enum.Enum` in Python, frozen object in JS) to enable static checking.
  5. If a parallel constants module already exists but is dead code (defined but never imported), either adopt it as the canonical source or delete it explicitly in the commit.
  6. Verify by grepping the original literals — they should no longer appear outside the constants file.

### Before

```python
# routes/task_routes.py
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    ...
    if len(title) < 3: return jsonify({'error': 'Título muito curto'}), 400
    if len(title) > 200: return jsonify({'error': 'Título muito longo'}), 400
    if priority < 1 or priority > 5: return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400
    if status not in ['pending', 'in_progress', 'done', 'cancelled']:
        return jsonify({'error': 'Status inválido'}), 400
    ...

# utils/helpers.py  (already defines these constants but no route imports them)
VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
```

### After

```python
# src/config/constants.py
from enum import Enum
class TaskStatus(str, Enum):
    PENDING = "pending"; IN_PROGRESS = "in_progress"; DONE = "done"; CANCELLED = "cancelled"
TASK_TITLE_MIN_LEN = 3
TASK_TITLE_MAX_LEN = 200
TASK_PRIORITY_MIN = 1
TASK_PRIORITY_MAX = 5
TERMINAL_STATUSES = {TaskStatus.DONE, TaskStatus.CANCELLED}

# src/schemas/task_schema.py
from marshmallow import Schema, fields, validate
from src.config.constants import (
    TASK_TITLE_MIN_LEN, TASK_TITLE_MAX_LEN,
    TASK_PRIORITY_MIN, TASK_PRIORITY_MAX, TaskStatus,
)
class TaskCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(TASK_TITLE_MIN_LEN, TASK_TITLE_MAX_LEN))
    priority = fields.Int(validate=validate.Range(TASK_PRIORITY_MIN, TASK_PRIORITY_MAX))
    status = fields.Str(validate=validate.OneOf([s.value for s in TaskStatus]))
```

### Validation hint

`git grep -nE "(< 3|> 200|< 1|> 5)\b" src/views/ src/controllers/` returns nothing (or only matches where the constant import is on the same screen). `git grep -nE "\\['pending', *'in_progress'" src/` returns nothing outside `src/config/constants.py`. Importing `from src.config.constants import TaskStatus` works from any route/controller. Old `utils/helpers.py` parallel constants either redirect to `src/config/constants` or are deleted in the same commit.

---

### Recipe → catalog reverse coverage

This table mirrors the catalog↔playbook coverage matrix in `catalog-antipatterns.md` and acts as a lint anchor: every catalog slug must appear in the `Fixes catalog entries:` field of at least one recipe above.

| Catalog slug | Recipe that fixes it |
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

10 catalog slugs / 8 recipes — full coverage. Recipe #5 (move-business-logic) and recipe #6 (replace-bare-except) each fix two catalog entries.

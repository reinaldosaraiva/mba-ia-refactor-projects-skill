================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Generated: 2026-05-18

## Summary
CRITICAL: 3 | HIGH: 2 | MEDIUM: 2 | LOW: 2

## Findings

### [CRITICAL] SQL Injection via string concatenation across the data layer
File: models.py:28, 47-49, 57-60, 68, 92, 109-110, 126-128, 140, 148-150, 155, 157-159, 163-165, 174, 188, 192, 220, 224, 279-280, 285-299
File: app.py:59-78
Description: 14 of the 22 `cursor.execute(...)` calls in `models.py` build their SQL by concatenating Python strings with request-derived data (`+ str(id)`, `+ email + "' AND senha = '" + senha`). The dynamic search builder in `buscar_produtos` (models.py:285-299) concatenates `termo` directly into a `LIKE '%...%'` clause. Endpoint `/admin/query` in `app.py:59-78` accepts arbitrary JSON-supplied SQL and executes it verbatim.
Impact: Authentication bypass (login query is concatenated), full read/write of every table, plus `/admin/query` is an unauthenticated arbitrary-SQL gateway.
Recommendation: Apply playbook recipe `replace-raw-sql-with-parameterised-queries`. Delete `/admin/reset-db` and `/admin/query` as part of the refactor.

### [CRITICAL] Hardcoded credentials, debug-enabled prod, secret leaked through /health
File: app.py:7-8, 88
File: controllers.py:289
File: database.py:31, 76-79
File: models.py:127-128
Description: `SECRET_KEY = "minha-chave-super-secreta-123"` is a literal string committed to `app.py:7`; the same literal is then echoed back in the `/health` response (`controllers.py:289`). `DEBUG = True` is set in both `app.config["DEBUG"]` (line 8) and `app.run(debug=True)` (line 88). The `usuarios.senha` column stores plaintext passwords (database.py:31 schema, lines 76-79 seed with literal `"admin123"`, `models.py:127-128` INSERTs raw passwords).
Impact: Source-tree access compromises every session (signing key forgery) and grants payment-grade DB takeover; Werkzeug debug mode enables RCE via the interactive debugger PIN; plaintext passwords trivially leakable.
Recommendation: Apply playbook recipe `extract-config-to-env-or-settings-module`. Hash passwords via the standard pattern in that recipe's follow-up steps.

### [CRITICAL] God modules — controllers.py and models.py each mix 4 domains
File: controllers.py:1-292
File: models.py:1-314
Description: `controllers.py` holds 17 handler functions for produtos, usuarios, pedidos, login, relatórios, and health (4 domain entities + cross-cutting). Each handler does parsing, validation, business logic, side-effect notifications (`print("ENVIANDO EMAIL")` lines 208-210, 248-250), logging, and response formatting. `models.py` holds raw SQL data access plus business rules (discount tiers, lines 256-262) for the same 4 entities. Plus `app.py:47-78` adds two unauthenticated admin endpoints inline.
Impact: Impossible to test any handler in isolation; every domain change risks breaking the others; admin endpoints are attack surface; the file pair owns 78% of the codebase.
Recommendation: Apply playbook recipe `split-god-class-into-controllers-by-domain`. Decompose into `src/controllers/{produto,usuario,pedido,relatorio}_controller.py` and `src/models/{produto,usuario,pedido}_model.py`.

### [HIGH] Business logic in handlers — notifications and discount tiers
File: controllers.py:208-210, 247-250
File: models.py:256-262
Description: Pedido-created notification is implemented as three `print()` statements inside `criar_pedido` (controllers.py:208-210). Status-change notifications are `print()` calls in `atualizar_status_pedido` (controllers.py:247-250). Discount-tier business rules (`if faturamento > 10000: desconto = ...`) live inside the data-access function `relatorio_vendas` (models.py:256-262).
Impact: Cannot swap notification backend; cannot unit-test discount policy without a DB; business rules invisible to anyone reading the controller layer.
Recommendation: Apply playbook recipe `move-business-logic-from-route-to-controller`. Extract notifications behind `src/services/notification_service.py`; move discount tiers into `src/controllers/relatorio_controller.py`.

### [HIGH] N+1 queries in pedido listings and report
File: models.py:171-201
File: models.py:203-233
File: models.py:235-273
Description: `get_pedidos_usuario(usuario_id)` runs one query for pedidos, then per pedido one query for itens, then per item one query for the produto name — O(P × I) queries (lines 171-201). `get_todos_pedidos()` repeats the same pattern over every pedido (lines 203-233). `relatorio_vendas()` runs 5 independent `COUNT/SUM` queries that could be a single aggregate (lines 239-254).
Impact: Listing endpoint latency grows linearly with order volume; SQLite global lock amplifies it; report endpoint hits the DB 5× per request unnecessarily.
Recommendation: Apply playbook recipe `eager-load-relationships-to-fix-n+1`. Single JOIN across pedidos × itens_pedido × produtos with Python-side grouping; consolidate report into one aggregate query.

### [MEDIUM] Bare exception handlers swallow tracebacks and leak internals
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
Description: Every one of the 16 route handlers in `controllers.py` ends with `try: ... except Exception as e: return jsonify({"erro": str(e)}), 500`. The raw exception message is returned to the client.
Impact: Stack traces and SQL error messages reach end users (information disclosure — table names, query structure leak to attackers); structured logging is impossible; debug-mode tracebacks would arrive at every consumer.
Recommendation: Apply playbook recipe `replace-bare-except-with-typed-handler-and-error-middleware`. Install one `@app.errorhandler(Exception)` in `src/middlewares/error_handler.py`; remove per-route try/except blocks.

### [MEDIUM] Duplicate validation between create and update with drift
File: controllers.py:28-54
File: controllers.py:72-91
Description: `criar_produto` (lines 28-54) and `atualizar_produto` (lines 72-91) repeat the same 7-check validation block. The update path silently **drops the category whitelist check** (line 52 has `categoria not in categorias_validas`; the update path between lines 72-91 has no such check), allowing arbitrary `categoria` values via PUT.
Impact: Maintenance hazard (rules drift, already drifted on category); the missing category check is an actual business bug, not just a code smell.
Recommendation: Apply playbook recipe `move-business-logic-from-route-to-controller`. Extract validation into `src/schemas/produto_schema.py` with marshmallow/pydantic; both POST and PUT import the same schema with `partial=True` for updates.

### [LOW] Magic numbers and inline whitelists scattered through validation
File: controllers.py:47-50, 52-54, 242
File: models.py:256-262
Description: Length thresholds (`< 2`, `> 200`) inline at controllers.py:47-50; category whitelist `["informatica", "moveis", ...]` inline at line 52-54; pedido status whitelist `["pendente", "aprovado", "enviado", "entregue", "cancelado"]` inline at line 242. Discount thresholds (`> 10000`, `> 5000`, `> 1000`) and rates (`0.1`, `0.05`, `0.02`) inline in models.py:256-262.
Impact: Business rules invisible to readers; cannot configure per environment; rules drift across copies (category whitelist already missing from update path).
Recommendation: Apply playbook recipe `lift-magic-numbers-and-whitelists-into-constants-module`. Move thresholds and whitelists into `src/config/constants.py`; routes/schemas import from there.

### [LOW] Inconsistent response envelope across endpoints
File: controllers.py:9, 12, 18, 20, 22, 29, 31, 33, 35, 44, 46, 48, 50, 54, 58, 62, 70, 73, 75, 77, 79, 88, 90, 93, 96 (and 30+ more)
Description: Same controller file mixes at least six envelope shapes: `{"dados": ..., "sucesso": True}`, `{"dados": ..., "sucesso": True, "mensagem": ...}`, `{"dados": ..., "total": ..., "sucesso": True}`, `{"erro": ...}`, `{"erro": ..., "sucesso": False}`, `{"sucesso": True, "mensagem": ...}` (no `dados`). The /health endpoint returns yet another shape including a raw secret (controllers.py:276-289).
Impact: Client code cannot programmatically discriminate success vs error; type-safe consumers drift; testing duplicates response-shape assertions per route.
Recommendation: Apply playbook recipe `replace-bare-except-with-typed-handler-and-error-middleware`. The recipe ships a `src/views/response.py::success()/error()` envelope helper as part of the error-middleware install.

================================
Total: 9 findings
================================

## Calibration cross-check (S001)

`plans/P001-S001-findings.md` listed 11 findings for project 1 with distribution 4 CRITICAL / 2 HIGH / 2 MEDIUM / 3 LOW. This audit produced 9 findings with distribution 3 / 2 / 2 / 2. Delta:

- **−1 CRITICAL** — S001 included `global-mutable-state` (module-level `db_connection`, `check_same_thread=False`, no per-request connection). The v1 catalog (S002) does not have a `global-mutable-state` entry; the closest slug is in the playbook seed list but never made it into the catalog. **Recorded as a residual; recommend adding to the v1.1 catalog post-workstream.**
- **−1 LOW** — S001 included `string-concat-for-messages-instead-of-f-string` as a separate style finding. The v1 catalog folds this into the `sql-injection-string-concat` detection signals (Python concatenation is what enables the injection). **Acceptable.**

Acceptance per `desafio.md` lines 279-282 and design contract I-10:

- ≥ 5 findings: YES (9)
- ≥ 1 CRITICAL or HIGH: YES (3 CRITICAL + 2 HIGH = 5)
- Findings ordered CRITICAL → LOW: YES
- Every finding has `file:line`: YES
- Every recommendation names a playbook slug verbatim: YES

> Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

Operator response: `y` (2026-05-18, recorded in P001-S004 chat).

================================
PHASE 3: REFACTORING COMPLETE
================================

## New project structure

```
code-smells-project/
├── src/
│   ├── config/{settings.py, constants.py}
│   ├── errors/__init__.py
│   ├── middlewares/error_handler.py
│   ├── services/notification_service.py
│   ├── models/{__init__.py, produto_model.py, usuario_model.py, pedido_model.py}
│   ├── schemas/{produto_schema.py, usuario_schema.py, pedido_schema.py}
│   ├── controllers/{produto, usuario, pedido, relatorio, health}_controller.py
│   └── views/{__init__.py (register_blueprints), response.py, produto_routes.py,
│              usuario_routes.py, pedido_routes.py, relatorio_routes.py,
│              health_routes.py}
├── app.py            (composition root only — 22 LOC, no business logic)
├── .env.example
├── requirements.txt
└── .claude/skills/refactor-arch/  (UNCHANGED)
```

Legacy files removed: `controllers.py` (292 LOC), `models.py` (314 LOC), `database.py` (86 LOC), `loja.db` (deleted; regenerated on first boot).

## Layering rule checks (per guidelines-arquitetura.md)

```
1. views must NOT import models directly       → OK
2. models must NOT import controllers or views → OK
3. controllers must NOT import views           → OK
4. middlewares own no business logic           → OK
```

## Validation

Boot command: `SECRET_KEY=test-key-do-not-commit DEBUG=false PORT=5050 python app.py`
Boot outcome: OK — server listening on `http://0.0.0.0:5050`. Default port 5000 is occupied by macOS AirPlay; PORT env var was honoured via `src/config/settings.py`.

| # | Endpoint | Method | HTTP | Pass? | Notes |
|---|----------|--------|------|-------|-------|
| 1 | `/` | GET | 200 | YES | welcome JSON |
| 2 | `/health` | GET | 200 | YES | secret_key count in response = 0 (leak fixed) |
| 3 | `/produtos` | GET | 200 | YES | |
| 4 | `/produtos/1` | GET | 200 | YES | seeded item |
| 5 | `/produtos/busca?q=Notebook` | GET | 200 | YES | dynamic WHERE works |
| 6 | `/produtos` | POST | 201 | YES | created id=11 |
| 7 | `/produtos/1` | PUT | 200 | YES | updated seed item |
| 8 | `/produtos/11` | DELETE | 200 | YES | |
| 9 | `/usuarios` | GET | 200 | YES | |
| 10 | `/usuarios` | POST | 201 | YES | created Carlos |
| 11 | `/login` | POST (`joao@email.com`/`123456`) | 200 | YES | seeded login |
| 12 | `/login` | POST (`x' OR 1=1 --`/`y`) | 401 | YES | **SQL injection fix verified** |
| 13 | `/pedidos` | POST | 201 | YES | usuario_id=2 + 1 item |
| 14 | `/pedidos` | GET | 200 | YES | N+1 fixed (single JOIN) |
| 15 | `/pedidos/usuario/2` | GET | 200 | YES | N+1 fixed |
| 16 | `/pedidos/1/status` | PUT (`aprovado`) | 200 | YES | notification dispatched via service |
| 17 | `/relatorios/vendas` | GET | 200 | YES | discount tiers in controller; 1 aggregate query |
| 18 | `/admin/reset-db` | POST | 404 | YES (expected) | endpoint deleted by Phase 3 |
| 19 | `/admin/query` | POST | 404 | YES (expected) | endpoint deleted by Phase 3 |

**Regressions: none.** All 17 functional endpoints respond with the expected status; the 2 admin endpoints correctly return 404 by design.

## Catalog coverage applied

| Catalog slug | Status |
|---|---|
| sql-injection-string-concat | FIXED — all queries parameterised; injection payload → 401 |
| hardcoded-credentials | FIXED — SECRET_KEY/DEBUG/DB_PATH in `src/config/settings.py` (env-loaded); secret no longer in /health |
| god-class-or-god-module | FIXED — `controllers.py` and `models.py` split into per-domain modules |
| business-logic-in-route-or-controller | FIXED — notifications via `NotificationService`; discount tiers in `relatorio_controller` |
| n+1-query | FIXED — pedido listings use one JOIN + Python grouping; report uses one aggregate query |
| bare-except-or-catch-all | FIXED — 16 try/except blocks removed; one `@app.errorhandler` in `src/middlewares/error_handler.py` |
| duplicate-validation-logic | FIXED — `src/schemas/produto_schema.py::_validate_common` shared by create/update; category whitelist drift gone |
| magic-numbers-or-inline-whitelist | FIXED — thresholds and whitelists in `src/config/constants.py` |
| inconsistent-response-envelope | FIXED — all responses through `src/views/response.py::success()/error()` |

## Residuals (intentionally not fixed in v1)

- **Password hashing.** The audit's hardcoded-credentials finding extends to plaintext passwords in `usuarios.senha`. The v1 playbook recipe `extract-config-to-env-or-settings-module` covers config secrets, not password hashing. Bcrypt/argon2 introduction requires schema migration and would change the seeded users' login behaviour — out of scope for the boot+endpoint validation contract. Recommended for a follow-up session.
- **Global-mutable-state (S001 critical not in v1 catalog).** The module-level `db_connection` singleton with `check_same_thread=False` was independently fixed in this refactor by adopting the Flask `g` pattern (per-request connection with `teardown_appcontext`), so the underlying defect is gone even though the catalog had no slug for it. Recommended catalog addition: `global-mutable-state` for v1.1.

================================
Total: 9 findings, 9 fixed (with 2 residuals documented above)
================================

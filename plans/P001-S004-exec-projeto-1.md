# P001-S004 — Execute /refactor-arch on code-smells-project

## Zero-context bootstrap

If resuming with no prior conversation:

1. Read `plans/CURRENT.md` to confirm this is the active session.
2. Read `plans/P001-skill-refactor-arch.md` for workstream context.
3. Read `plans/P001-design-contract.md` — focus on **I-4** (Phase-2 confirmation gate is non-negotiable), **I-5** (Phase-3 validates via boot + smoke test recorded in results), **I-6** (no secret leakage in refactored source), **I-7** (target MVC), **I-10** (≥ 5 findings with ≥ 1 CRITICAL/HIGH).
4. Read the six skill files under `code-smells-project/.claude/skills/refactor-arch/` so the runtime knows what it is executing.
5. Read `desafio.md` lines 148-156 (project-1-specific checklist) and lines 276-283 (acceptance criteria).
6. Execute the tasks below in order. **Stop after Phase 2** and wait for explicit user confirmation before Phase 3.

## Goal

First real execution of `/refactor-arch`. Target: `code-smells-project/` (Python + Flask, the project that also owns the skill tree). Three outcomes required:

1. Phase 1 prints a Phase-1 summary block that matches the format in `analise-projeto.md`.
2. Phase 2 writes `reports/audit-project-1.md` per `template-relatorio.md`, satisfies acceptance criteria (≥ 5 findings, ≥ 1 CRITICAL/HIGH), then halts on the verbatim confirmation prompt from SKILL.md.
3. After explicit user `y`, Phase 3 refactors `code-smells-project/` into the MVC tree from `guidelines-arquitetura.md`, boots the app, smoke-tests every original endpoint, and records the validation block in the same report file. Refactor must be committed.

This session closes with verdict `PASS` (delivery round) when all three are demonstrably true, evidenced in `reports/audit-project-1.md` and `plans/P001-S004-results.md`.

## Operating mode

The agent executing this session **is** the skill's runtime. The flow:

- Treat SKILL.md as the prompt that drives behaviour.
- Treat the five reference files as authoritative knowledge — do not improvise detection signals or transformation recipes that contradict them.
- Phase-2 gate is enforced literally: after writing and printing the audit report, the agent surfaces the prompt `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` and **ends its turn** waiting for the human user to type `y`/`yes` or anything else. Do not self-approve.

## Prerequisite reads (only these)

| Path | Why |
|------|-----|
| `code-smells-project/.claude/skills/refactor-arch/SKILL.md` | The runtime prompt |
| `code-smells-project/.claude/skills/refactor-arch/analise-projeto.md` | Phase-1 heuristics |
| `code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md` | Phase-2 catalog |
| `code-smells-project/.claude/skills/refactor-arch/template-relatorio.md` | Phase-2 report format |
| `code-smells-project/.claude/skills/refactor-arch/playbook-refactor.md` | Phase-3 recipes |
| `code-smells-project/.claude/skills/refactor-arch/guidelines-arquitetura.md` | Phase-3 target layout |
| `code-smells-project/app.py` | Routes register here — sets the smoke-test endpoint set |
| `code-smells-project/controllers.py` | Handler bodies (must be split across `src/controllers/`) |
| `code-smells-project/models.py` | Data access (must be split across `src/models/` with parameterised SQL) |
| `code-smells-project/database.py` | Schema DDL + seed (must move to startup hook + `src/config/`) |
| `code-smells-project/requirements.txt` | Dependency list |
| `plans/P001-S001-findings.md` | Cross-check: Phase 2 must rediscover the 11 findings (or document why fewer) |

The S001 findings file is read **for cross-check only after Phase 2 has produced its own report**. Do not consult it during Phase 2 detection — that would defeat the audit's purpose. Use it after the report is written, as a calibration check: if Phase 2 produced < 5 findings, the catalog detection signals are mis-tuned and the agent must augment the report by re-running the signals manually before halting.

## Tasks — Phase 1 (project analysis)

1. Apply each heuristic from `analise-projeto.md` against `code-smells-project/` using the mechanical signals (find/grep commands) the file specifies.
2. Construct the summary block. Expected output (subject to verification — do not pre-fill):
   - `Language: python`
   - `Framework: python-flask <version-from-requirements>` (e.g. `Flask 3.1.x`)
   - `Dependencies: flask, flask-cors`
   - `Domain: E-commerce API (produtos, usuarios, pedidos, itens_pedido)`
   - `Architecture: flat — 4 source files at root, no layer folders`
   - `Source files: 4`
   - `DB tables: produtos, usuarios, pedidos, itens_pedido`
3. Print the summary block to stdout. Continue to Phase 2 without halting.

## Tasks — Phase 2 (audit)

4. Iterate every catalog entry in `catalog-antipatterns.md`. Filter to entries whose `Stacks` field includes `any`, `python-flask`, or `python-generic`.
5. For each entry, run its `Detection signals` against `code-smells-project/`. Record every match as a candidate finding.
6. Group candidate matches by catalog entry. Each catalog entry produces one finding heading; the `File:` line lists all matching paths (one per line if multi-site).
7. Order findings strictly CRITICAL → HIGH → MEDIUM → LOW. Within a severity, sort by file path then line number.
8. Write `reports/audit-project-1.md` using the layout in `template-relatorio.md`:
   - Header block (Project: `code-smells-project`, Stack: `Python + Flask`, Files: `4 analyzed | ~780 lines`).
   - Summary line with exact counts.
   - Findings (each with File / Description / Impact / Recommendation pointing at a playbook slug verbatim).
   - Footer `Total: <N> findings`.
9. Print the report to stdout.
10. **Cross-check against S001 calibration**: open `plans/P001-S001-findings.md` and count findings reported there for project 1 (target: 11, distribution 4/2/2/3). If your Phase 2 produced < 5 findings, the catalog is mis-tuned — re-run detection signals more thoroughly and amend the report. If your Phase 2 produced ≥ 5 findings including ≥ 1 CRITICAL/HIGH, proceed to step 11.
11. Surface the verbatim halt prompt as the **last line of the turn**:

    > Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]

12. **End the turn here.** Do not execute Phase 3. Do not summarise. Do not propose alternatives. Wait for the user's next message.

## Tasks — Phase 3 (refactor + validate)

Execute only after the user explicitly responds `y` or `yes`.

13. Read `playbook-refactor.md` once. For each finding in the Phase-2 report, locate the linked recipe.
14. Create the target directory tree inside `code-smells-project/`:
    ```
    code-smells-project/
    ├── src/
    │   ├── config/{settings.py, constants.py}
    │   ├── models/{produto_model.py, usuario_model.py, pedido_model.py, ...}
    │   ├── views/routes.py
    │   ├── controllers/{produto_controller.py, usuario_controller.py, pedido_controller.py, relatorio_controller.py}
    │   ├── services/notification_service.py
    │   ├── middlewares/error_handler.py
    │   ├── schemas/{produto_schema.py, usuario_schema.py, pedido_schema.py}
    │   └── errors/__init__.py
    ├── app.py        (now a thin composition root)
    ├── requirements.txt
    └── .claude/      (UNCHANGED — preserve the skill tree)
    ```
15. Apply the playbook recipes in this order to limit risk:
    1. `extract-config-to-env-or-settings-module` — move `SECRET_KEY`, `DEBUG`, `DB_PATH` into `src/config/settings.py`. Add `.env.example`. Add `.env` to `.gitignore` if missing.
    2. `replace-deprecated-api-call-with-current-equivalent` — none expected in project 1, but run the check.
    3. `replace-raw-sql-with-parameterised-queries` — convert every `cursor.execute("..." + ...)` to placeholder syntax. This is the single most security-critical change.
    4. `eager-load-relationships-to-fix-n+1` — rewrite `get_pedidos_usuario` and `get_todos_pedidos` as one JOIN each, group by pedido in Python.
    5. `split-god-class-into-controllers-by-domain` — split `controllers.py` into 4 controller modules under `src/controllers/`; split `models.py` into 4 model modules under `src/models/`.
    6. `move-business-logic-from-route-to-controller` — pull discount tiers out of `relatorio_vendas`; pull notification side-effects out of pedido handlers into `src/services/notification_service.py` (interface + stub impl).
    7. `replace-bare-except-with-typed-handler-and-error-middleware` — install `src/middlewares/error_handler.py`; remove per-route try/except; create `src/errors/{AppError, NotFoundError, ValidationError}`; route every success through `src/views/response.py::success()`.
    8. `lift-magic-numbers-and-whitelists-into-constants-module` — move thresholds and whitelists into `src/config/constants.py`; routes/schemas import from there.
16. Delete the unsafe admin endpoints from the old `app.py`: `/admin/reset-db` (line 47-57) and `/admin/query` (line 59-78). Remove the secret leakage from `/health` (line 289).
17. Reshape `app.py` to be a composition root only: build `Flask(__name__)`, load settings, register blueprints from `src/views`, register the error handler, initialise DB via app context. No business logic.
18. Run the layering-rule grep checks from `guidelines-arquitetura.md`. Fix any violation before continuing.
19. Boot the refactored app. Command: `cd code-smells-project && SECRET_KEY=test-key-do-not-commit DEBUG=false python app.py` (in background or with a 3-second probe). Capture the boot output. If it does not start, fix and retry; do not proceed to step 20 with a broken boot.
20. Smoke-test the original endpoint set (one call per route family). Use `curl` against `http://localhost:5000`:
    - `GET /` (welcome) → expect 200
    - `GET /health` → expect 200, response **must not** contain `secret_key`
    - `GET /produtos` → expect 200
    - `GET /produtos/1` → expect 200 (seeded)
    - `GET /produtos/busca?q=Notebook` → expect 200
    - `POST /produtos` with valid body → expect 201
    - `PUT /produtos/1` with valid body → expect 200
    - `DELETE /produtos/1` → expect 200
    - `GET /usuarios` → expect 200
    - `POST /usuarios` with valid body → expect 201
    - `POST /login` with seeded credentials → expect 200
    - `POST /login` with `{"email": "x' OR 1=1 --", "senha": "y"}` → expect 401 (verifies SQL-injection fix)
    - `POST /pedidos` with valid usuario_id + itens → expect 201
    - `GET /pedidos` → expect 200
    - `GET /pedidos/usuario/2` → expect 200
    - `PUT /pedidos/1/status` with `{"status": "aprovado"}` → expect 200
    - `GET /relatorios/vendas` → expect 200
    - `POST /admin/reset-db` → expect 404 (deleted by Phase 3)
    - `POST /admin/query` → expect 404 (deleted by Phase 3)
21. Append a `## Validation` section to `reports/audit-project-1.md` with the boot command, boot outcome, and the endpoint table (Method × Endpoint × HTTP status × Pass?). Mark `Pass? = NO` for any endpoint that regresses; mark `Pass? = YES` for the two admin endpoints expected to 404 (they are deliberately deleted, not regressed).
22. If any non-admin endpoint regresses, **revert the specific change that broke it** (likely one of the SQL parameterisations, since those are the touchiest), re-run the smoke test, and only then proceed.

## Tasks — closeout

23. Write `plans/P001-S004-results.md` with **Verdict:** PASS in the first 5 lines. Include:
    - Phase 1 summary block (verbatim).
    - Phase 2 finding counts and the `reports/audit-project-1.md` path.
    - Phase 3 boot command + endpoint validation table summary (pass / total).
    - Residuals (any catalog slug intentionally not fixed and why).
    - Commit hash (filled in follow-up commit).
24. Update `plans/INDEX.md`: S004 row to `done | PASS`, S005 row to `authorable`.
25. Update `plans/CURRENT.md`: between sessions, ready to author S005.
26. Clear `plans/LOCKS.json`.
27. Two-commit pattern:
    - Bootstrap commit: covers everything (refactored project tree under `code-smells-project/src/`, modified `code-smells-project/app.py`, new `reports/audit-project-1.md`, plan artefacts).
    - Follow-up commit: records the bootstrap hash in the results file.

## Definition of done

- `reports/audit-project-1.md` exists at workspace root, format matches `template-relatorio.md`, severity tally satisfies `desafio.md` line 280 (≥ 5 findings) and line 281 (≥ 1 CRITICAL/HIGH).
- Phase-2 halt prompt surfaced literally; user confirmation `y` recorded in conversation before Phase 3 began.
- `code-smells-project/src/{config,models,views,controllers,services,middlewares}` exists; each layer has at least one populated file; layering-rule grep checks return no violations.
- `code-smells-project/.claude/skills/refactor-arch/` tree **unchanged** (verify with `git diff --stat code-smells-project/.claude`).
- No secret literal remains in tracked source outside `src/config/` and `.env.example`. Verify with the recipe's validation grep.
- App boots with `python app.py` (after exporting `SECRET_KEY`).
- Smoke-test endpoint table in `reports/audit-project-1.md` has 0 regressions (admin-deleted endpoints count as expected 404, not regressions).
- `INDEX.md`, `CURRENT.md`, `LOCKS.json` updated.
- Two commits landed.

## Out of scope (defer)

- Copying the skill to `ecommerce-api-legacy/` or `task-manager-api/` — S005, S006.
- Editing the skill files — they are frozen for the duration of execution sessions.
- Author tests beyond smoke. The brief does not require pytest coverage; smoke tests are the validation contract (`desafio.md` line 282).

## Risks specific to this session

- **Catalog detection signals mis-tuned.** If Phase 2 produces < 5 findings, the catalog signals do not match the code shape. Mitigation: step 10 cross-checks against the S001 dossier; if short, augment the report by re-running detection patterns more aggressively (e.g. looser regex) before halting.
- **SQL parameterisation breaks dynamic search.** The `buscar_produtos` function builds dynamic WHERE clauses; naïve param replacement may produce malformed SQL. Mitigation: follow the recipe's `Before/After` for that exact shape (whitelist clause names, parameterise values).
- **N+1 fix changes response shape.** The current `get_pedidos_usuario` returns a nested structure with `produto_nome` per item. After the JOIN + group-by, ensure the output JSON is byte-identical (or at least key-compatible) with what the test client expects. Mitigation: smoke test inspects key names, not just status codes, for `/pedidos/*` responses.
- **Skill tree gets accidentally moved.** Phase 3 reshapes the project; the `code-smells-project/.claude/` directory must remain at its current path because the skill is invoked from `code-smells-project/`. Mitigation: never move or rename `.claude/`; the layering grep check excludes that path.
- **Boot hangs on Werkzeug debug.** Phase 3 sets `DEBUG=false` to avoid the interactive debugger; if `app.run(debug=True)` survives the refactor by accident, the smoke test will hang. Mitigation: read `DEBUG` from settings; the test environment exports `DEBUG=false`.
- **Database file persistence.** `loja.db` persists across runs; the first refactored boot may operate against a DB seeded by the old code path. Mitigation: delete `code-smells-project/loja.db` before the first refactored boot (the schema is regenerated on startup, and seeds are idempotent under the new code path).
- **Endpoint regressions disguised as 404s.** A route may legitimately return 404 (item not found) — the smoke test must distinguish "endpoint exists and returned 404 because no such resource" from "route was lost in refactor". Mitigation: every smoke test row records both the HTTP status and a one-word pass criterion (e.g. `200`, `201`, `200 (item exists)`, `404 (admin route deleted)`).

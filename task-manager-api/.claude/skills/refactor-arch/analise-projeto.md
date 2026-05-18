---
schema_version: 1
detection_axes: [language, framework, database, domain, architecture]
---

# Phase-1 detection heuristics

Lookup tables consumed by the skill during Phase 1. Every signal is expressible as a `find` / `grep` / `head` invocation an operator can run mechanically. Do not paraphrase into prose; keep the signals in tables so they remain audit-friendly.

Exclude these paths from every scan: `node_modules/`, `__pycache__/`, `.venv/`, `venv/`, `env/`, `dist/`, `build/`, `.git/`, `.next/`, `target/`, `vendor/`.

## Language detection

Decide on the language by combining file-extension counts with secondary signals (shebang, manifest filenames).

| Extension | Language tag | Notes |
|-----------|--------------|-------|
| `.py` | `python` | Python 2 vs 3: check `print(` (statement → Py2) vs `print(` (function → Py3); modern projects assume Py3. |
| `.js` | `javascript` | If `tsconfig.json` exists nearby, prefer TypeScript context for advice. |
| `.ts`, `.tsx` | `typescript` | TS implies a build step (`tsc`/`vite`/`esbuild`). |
| `.rb` | `ruby` | Look at `Gemfile` next. |
| `.go` | `go` | Confirm with `go.mod`. |
| `.java`, `.kt` | `jvm` | Build files: `pom.xml`, `build.gradle`. |
| `.php` | `php` | `composer.json` confirms. |
| `.rs` | `rust` | `Cargo.toml` confirms. |

Mechanical signals:

```bash
find . -type f \( -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.rb' -o -name '*.go' -o -name '*.java' -o -name '*.php' -o -name '*.rs' \) \
  -not -path '*/node_modules/*' -not -path '*/__pycache__/*' -not -path '*/.venv/*' -not -path '*/dist/*' -not -path '*/.git/*' \
  | awk -F. '{print $NF}' | sort | uniq -c | sort -rn
# Shebang on entry-point candidates
head -1 ./*.{py,js,sh,rb} 2>/dev/null | grep -E '^#!'
```

Decision rule: language is the extension with the highest count among source-shaped files. Ties broken by manifest file presence (Python → `requirements.txt`/`pyproject.toml`, Node → `package.json`, etc.).

Output: `Language: <python|javascript|typescript|ruby|go|jvm|php|rust>`.

## Framework detection

After language is known, infer the framework from dependency files. Multiple frameworks may coexist (Flask + flask-sqlalchemy); list the primary HTTP framework first.

| Language | Manifest | Primary indicator | Framework tag |
|----------|----------|-------------------|---------------|
| python | `requirements.txt`, `pyproject.toml`, `Pipfile` | `Flask`, `flask` | `python-flask` |
| python | (same) | `fastapi` | `python-fastapi` |
| python | (same) | `Django`, `django` | `python-django` |
| python | (same) | none of the above + `app.py` with HTTP | `python-generic` |
| javascript / typescript | `package.json` `dependencies` | `express` | `nodejs-express` |
| javascript / typescript | (same) | `fastify` | `nodejs-fastify` |
| javascript / typescript | (same) | `koa` | `nodejs-koa` |
| javascript / typescript | (same) | `next` | `nodejs-next` |
| javascript / typescript | (same) | none of the above + `app.js`/`server.js` with HTTP | `nodejs-generic` |
| ruby | `Gemfile` | `rails` | `ruby-rails` |
| ruby | `Gemfile` | `sinatra` | `ruby-sinatra` |
| go | `go.mod` | `gin-gonic/gin` | `go-gin` |
| go | `go.mod` | `gofiber/fiber` | `go-fiber` |
| go | `go.mod` | (others) | `go-generic` |

Mechanical signals:

```bash
# Python
[ -f requirements.txt ] && cat requirements.txt
[ -f pyproject.toml ] && grep -E 'flask|fastapi|django|sqlalchemy' pyproject.toml
# Node
[ -f package.json ] && grep -E '"(express|fastify|koa|next)"' package.json
[ -f package.json ] && grep -E '"(sqlite3|pg|mysql2|mongoose|prisma|knex)"' package.json
# Version extraction
[ -f requirements.txt ] && grep -iE '^(flask|fastapi|django)' requirements.txt | head -3
[ -f package.json ] && grep -E '"(express|fastify|koa)":' package.json | head -3
```

Output: `Framework: <tag> <version-or-blank>` plus `Dependencies: <top-level deps comma-separated, max 6>`.

## Database detection

DB inference combines driver imports, manifest entries, and filesystem scans for schema/data files.

| DB | Driver / ORM indicators | Filesystem signal |
|----|-------------------------|-------------------|
| sqlite | `import sqlite3` (py), `require('sqlite3')`/`better-sqlite3` (node) | `*.db`, `*.sqlite`, `*.sqlite3` files in repo |
| postgres | `psycopg2`, `psycopg`, `pg` (node), `asyncpg` | `DATABASE_URL` env / `postgres://` URI in config |
| mysql / mariadb | `mysqlclient`, `mysql2`, `pymysql` | `mysql://` URI |
| mongodb | `pymongo`, `mongoose` | `mongodb://` URI |
| sqlalchemy (any backend) | `from sqlalchemy`, `Flask-SQLAlchemy` | model files with `db.Model`, `class X(Base):` |
| prisma | `@prisma/client` | `schema.prisma` file |

Mechanical signals:

```bash
# Driver imports (python)
grep -rEn '^(import|from)\s+(sqlite3|psycopg2|psycopg|pymongo|sqlalchemy|flask_sqlalchemy)' --include='*.py' .
# Driver imports (node)
grep -rEn "require\\(['\"](sqlite3|pg|mysql2|mongoose|@prisma)" --include='*.js' --include='*.ts' .
# Schema strings
grep -rEn 'CREATE TABLE' --include='*.py' --include='*.js' --include='*.sql' .
# SQLAlchemy table mappings (table names)
grep -rEn "__tablename__\\s*=" --include='*.py' .
# SQL files in repo
find . -name '*.sql' -not -path '*/node_modules/*' -not -path '*/.git/*'
```

Output: `DB tables: <comma-separated tables when extractable>` or `DB tables: n/a` when not extractable. Always list at least the DB engine in the framework `Dependencies:` line so the operator can disambiguate.

## Domain detection

The application domain is inferred from three sources, combined:

1. **DB tables.** Table names usually name the domain entities (`produtos`, `pedidos`, `tasks`, `enrollments`, `payments`).
2. **Route paths.** Top-level URL segments echo the resources (`/produtos`, `/checkout`, `/tasks`, `/reports`).
3. **Domain words in README.** A README header line often names the application (`"API da Loja"`, `"Task Manager API"`, `"LMS"`).

Mechanical signals:

```bash
# Top route paths (Flask / Express)
grep -rEhn "@app\\.route\\(['\"]|@.*_bp\\.route\\(['\"]|app\\.(get|post|put|delete|patch)\\(['\"]" --include='*.py' --include='*.js' --include='*.ts' . \
  | grep -oE "['\"][^'\"]+['\"]" | sort -u | head -20
# README headline
grep -m1 '^#' README.md 2>/dev/null
# Entity nouns from SQLAlchemy
grep -rEn "__tablename__|class\\s+\\w+\\(db\\.Model" --include='*.py' . | head -10
```

Output: `Domain: <one-sentence summary derived from the entities and resources observed>`. Examples: `E-commerce API (produtos, pedidos, usuarios)`, `LMS API (users, courses, enrollments, payments, audit)`, `Task Manager API (tasks, users, categories, reports)`.

## Architecture detection

Classify the current shape so Phase 3 knows how invasive the refactor must be.

| Class | Definition | Typical signs |
|-------|------------|---------------|
| `flat` | ≤ 5 source files at the project root, no MVC folders, all concerns mixed in one or two files | `app.py + models.py + controllers.py + database.py` at root with no `src/` |
| `partially-organised` | Some MVC folders present (typically `models/`, `routes/`, `services/`) but not all; no `controllers/`, no `config/`, no `middlewares/`; business logic still in routes | `app.py + models/ + routes/ + utils/` |
| `layered` | Full MVC: `src/{config,models,views or routes,controllers,services,middlewares}` plus thin entry point | A complete `src/` tree with all six layers |

Mechanical signals:

```bash
# Top-level shape
find . -maxdepth 2 -type d -not -path '*/.git*' -not -path '*/node_modules*' -not -path '*/__pycache__*' -not -path '*/.venv*' | sort
# Source file count at root
ls -1 *.py *.js *.ts 2>/dev/null | wc -l
# Presence of MVC layer folders
for d in src/config src/models src/views src/controllers src/services src/middlewares config models views controllers services middlewares routes; do
  [ -d "$d" ] && echo "FOUND $d"
done
```

Output: `Architecture: <flat | partially-organised | layered>`. Append a short reason: `Architecture: flat — tudo em 4 arquivos, sem separação de camadas` (matches the brief's example on `desafio.md` line 36).

## Putting it together

The Phase-1 summary block printed by the skill uses these fields in this order, no others, no fewer:

```
Language:      <from Language detection>
Framework:     <from Framework detection>
Dependencies:  <from Framework detection>
Domain:        <from Domain detection>
Architecture:  <from Architecture detection>
Source files:  <count of source files, vendor folders excluded>
DB tables:     <from DB detection or "n/a">
```

If any field cannot be filled, write `unknown` — do not omit the line. Downstream tooling (the Phase-2 audit and the operator) relies on the line set being stable.

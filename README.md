# Skill `/refactor-arch` — Auditoria e Refatoração Arquitetural Automatizadas

> Workstream **P001**. Entrega cobrindo **3 projetos legados** em **2 stacks** (Python/Flask × 2, Node.js/Express × 1).
> Brief original em [`desafio.md`](desafio.md). Ciclo de vida em [`plans/INDEX.md`](plans/INDEX.md). Skill canônica em [`code-smells-project/.claude/skills/refactor-arch/`](code-smells-project/.claude/skills/refactor-arch/) — copiada **bit-identical** para os outros dois projetos.

A skill executa três fases sequenciais sobre qualquer codebase backend:

1. **Fase 1 — Análise:** detecta linguagem, framework, dependências, banco, domínio e arquitetura; imprime um bloco-resumo.
2. **Fase 2 — Auditoria:** cruza o código contra o catálogo de anti-patterns, grava `reports/audit-project-<N>.md` com cada achado em `file:line`, e **pausa pedindo confirmação** antes de tocar em qualquer arquivo.
3. **Fase 3 — Refatoração:** reestrutura o projeto para o padrão MVC do [`guidelines-arquitetura.md`](code-smells-project/.claude/skills/refactor-arch/guidelines-arquitetura.md), centraliza error handling, extrai segredos para `src/config/`, depois **boota a aplicação e curl-testa os endpoints** como validação.

Resultado: 3 refatorações reais, 31 achados na análise manual, 25 findings no agregado dos relatórios, 46 endpoints respondendo após Fase 3, **0 regressões**.

---

## A) Análise Manual

Esta seção destila o dossiê [`plans/P001-S001-findings.md`](plans/P001-S001-findings.md) (31 achados, 1 fonte da verdade para esta entrega). Cada linha das tabelas abaixo aponta o `file:line` exato do problema no código original.

### Projeto 1 — `code-smells-project/` (Python + Flask)

Stack: Flask 3.x + flask-cors + raw `sqlite3` (sem ORM). 4 arquivos `.py` no diretório raiz, ~780 LOC. Domínio: API de E-commerce (produtos, usuarios, pedidos, itens_pedido, relatórios de vendas). Arquitetura inicial: **monolítica flat** — `app.py` (entrypoint + admin endpoints), `controllers.py` (17 handlers), `models.py` (acesso a dados via SQL bruto), `database.py` (conexão singleton + DDL + seed).

| Severidade | Achado | File:line | Por que importa |
|---|---|---|---|
| CRITICAL | SQL Injection via concatenação em toda a camada de dados | `models.py:28, 47-49, 109-110, 126-128, 174, 220, 279-280, 285-299` + `app.py:59-78` (`/admin/query`) | 100% das queries usam `"..." + variavel`; endpoint `/admin/query` executa SQL arbitrário do request — bypass de auth, leitura/escrita total. |
| CRITICAL | Credenciais hardcoded, DEBUG=True em prod, segredo vazando via `/health` | `app.py:7-8, 88` + `controllers.py:289` + `database.py:31, 76-79` | `SECRET_KEY` literal no source e ecoada na resposta de `/health`; Werkzeug debug mode habilita RCE pelo PIN do debugger; senhas em texto puro no seed. |
| CRITICAL | God class `controllers.py` misturando 4 domínios + side effects | `controllers.py:1-292` | 17 handlers de produtos/usuarios/pedidos/login/relatórios/health no mesmo arquivo; notificações como `print()` (linhas 208-210); impossível testar em isolamento. |
| CRITICAL | Conexão de DB global mutável compartilhada entre threads | `database.py:4, 9-10` | `db_connection` em escopo de módulo, `check_same_thread=False`; corrompe WAL sob qualquer concorrência; commits cruzam requests. |
| HIGH | N+1 ao listar pedidos | `models.py:171-201, 203-233` | `get_pedidos_usuario` faz 1 query de pedidos, N de itens, N×M de produtos — 500+ queries para 100 pedidos com 5 itens. |
| HIGH | Lógica de negócio em controllers (notificações, descontos, whitelists) | `controllers.py:208-210, 247-250` + `models.py:256-262` | Discount tiers `if faturamento > 10000` dentro da função de acesso a dados; whitelist de status hardcoded em route; notificações como `print()`. |
| MEDIUM | Validação duplicada entre POST e PUT com drift | `controllers.py:30-54` vs `controllers.py:72-91` | Update `atualizar_produto` perdeu silenciosamente o check de whitelist de categoria — bug real, não só smell. |
| MEDIUM | `except Exception` engolindo tracebacks e vazando internals | `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292` | 16 routes retornam `jsonify({"erro": str(e)}), 500` — nome de tabela e estrutura de query vazam para o cliente. |
| LOW | Magic numbers e whitelists inline na validação | `controllers.py:47-50, 52, 242` + `models.py:257-262` | `< 2`, `> 200`, `["informatica","moveis",...]`, status `["pendente","aprovado",...]`, descontos `10000/5000/1000` — regras invisíveis e propensas a drift. |
| LOW | Concatenação de strings para mensagens em vez de f-strings | `controllers.py:8, 11, 54, 161, 208-210, 248, 250` + 25 sites em `models.py` | Mesmo idioma de concatenação que viabiliza a SQL injection — sinal de codebase pré-3.6. |
| LOW | Envelope de resposta inconsistente | `controllers.py:9, 18, 29, 132, 141, 161, 180, 252` (e mais 30 sites) | 6 shapes diferentes (`{dados,sucesso}`, `{dados,sucesso,mensagem}`, `{dados,sucesso,total}`, `{erro}`, `{erro,sucesso:false}`, `{sucesso,mensagem}`) — type-safe clients impossíveis. |

**Distribuição:** CRITICAL 4 / HIGH 2 / MEDIUM 2 / LOW 3 — **total 11**, todos os mínimos do `desafio.md` atendidos.

### Projeto 2 — `ecommerce-api-legacy/` (Node.js + Express)

Stack: Express 4.x + sqlite3 5.x. 3 arquivos em `src/` (`app.js`, `AppManager.js`, `utils.js`), ~180 LOC. Domínio: LMS (Learning Management System) — users, courses, enrollments, payments, audit_logs, com fluxo completo de checkout. Arquitetura inicial: **god class flat** — `AppManager.js` faz constructor + init de DB + DDL + seed + routes + business logic + payment + audit; `utils.js` é uma kitchen-sink (config + cache + crypto fake); `app.js` é um bootstrap de 14 linhas.

| Severidade | Achado | File:line | Por que importa |
|---|---|---|---|
| CRITICAL | God class `AppManager` misturando schema, rotas, payment, audit e callback hell | `src/AppManager.js:4-141` | Construtor abre DB; `initDb()` semeia senha plaintext `'123'` (linha 18); `setupRoutes` registra 3 endpoints inline; checkout é pirâmide de callbacks de 7 níveis (linhas 28-78). |
| CRITICAL | Credenciais hardcoded em produção (DB pass, chave Stripe `pk_live_*`, SMTP, senha de seed) | `src/utils.js:1-7` + `src/AppManager.js:18, 68` | `paymentGatewayKey: "pk_live_1234567890abcdef"` no source — shape de chave Stripe live dispararia cobranças reais; senha default `"123456"` em fallback. |
| CRITICAL | Crypto fake (`badCrypto`) + log de cartão em texto puro + chave de pagamento em log | `src/utils.js:17-23` + `src/AppManager.js:45-46` | `badCrypto` é base64-truncate determinístico sem salt — reversível por lookup; `console.log` logo abaixo expõe número de cartão + chave Stripe em todo checkout (violação PCI-DSS); status do pagamento decidido por `cc.startsWith("4")`. |
| HIGH | N+1 com contadores manuais de callback no `/financial-report` | `src/AppManager.js:80-129` | Query por curso, por matrícula, por usuário, por pagamento; concorrência via decrementar `coursesPending`/`enrPending` — sem Promise.all, sem propagação de erro; o endpoint trava silenciosamente em qualquer erro de DB. |
| HIGH | Bug self-documented em produção: `DELETE /api/users/:id` deixa orfanatos | `src/AppManager.js:131-137` | Resposta literal: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` — o autor documentou o bug como mensagem de sucesso. |
| MEDIUM | Estado global mutável em `cache` e `totalRevenue` | `src/utils.js:9-10, 12-15, 25` | `let globalCache = {}` e `let totalRevenue = 0` em escopo de módulo, mutados por `logAndCache`, re-exportados; sem TTL, sem evicção, sem escopo por tenant. |
| MEDIUM | DB em memória (`:memory:`) wired em construtor de prod | `src/AppManager.js:7` | `new sqlite3.Database(':memory:')` — dados sumem em todo restart; escala horizontal impossível. |
| MEDIUM | Field names crípticos + validação mínima | `src/AppManager.js:29-35` | `req.body.usr, .eml, .pwd, .c_id, .card`; única validação é `if (!u || !e || !cid || !cc)` — sem schema, sem checks de formato. |
| LOW | API deprecated: `require('sqlite3').verbose()` | `src/AppManager.js:1` | Idioma pré-2018 do sqlite3-node, hoje é no-op; sinal de zero manutenção desde então. |
| LOW | Respostas mixando text/plain e JSON | `src/AppManager.js:35, 38, 41, 48, 51, 55, 70, 84, 135` | `res.send("Bad Request")` ↔ `res.status(200).json(...)` ↔ `res.send("Usuário deletado, mas...")` — sem envelope, sem contrato. |

**Distribuição:** CRITICAL 3 / HIGH 2 / MEDIUM 3 / LOW 2 — **total 10**.

### Projeto 3 — `task-manager-api/` (Python + Flask + SQLAlchemy)

Stack: Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 + flask-cors. ~1158 LOC distribuídas em `app.py`, `database.py`, `seed.py`, `models/{task,user,category}.py`, `routes/{task,user,report}_routes.py`, `services/notification_service.py`, `utils/helpers.py`. Domínio: Task Manager (tasks, users, categories, reports, notifications). Arquitetura inicial: **parcialmente organizada** — `models/`, `routes/`, `services/`, `utils/` existem; faltam `controllers/`, `config/`, `middlewares/`, `errors/`, `schemas/`. Lógica de negócio mora dentro das routes; o validator `process_task_data` em `utils/helpers.py` existe mas nenhuma route o importa; constantes definidas em `utils/helpers.py:110-116` também não são importadas em lugar nenhum.

| Severidade | Achado | File:line | Por que importa |
|---|---|---|---|
| CRITICAL | Credenciais SMTP hardcoded + `SECRET_KEY` literal | `services/notification_service.py:7-11` + `app.py:11-13` | `email_password='senha123'` no construtor; `SECRET_KEY = 'super-secret-key-123'` literal; abre todas as sessões Flask + relay SMTP em caso de leak de repositório. |
| HIGH | JWT fake + zero middleware de autenticação | `routes/user_routes.py:185-211` + `routes/{task,user,report}_routes.py` | `/login` retorna `'fake-jwt-token-' + str(user.id)` (linha 210); o token nunca é verificado; nenhum endpoint (incluindo DELETE) tem `@require_auth`. |
| HIGH | N+1 em `/tasks`, `/reports/summary`, `/users/<id>/tasks` | `routes/task_routes.py:14-59` + `routes/report_routes.py:30-43, 53-68` + `routes/user_routes.py:153-183` | `Task.query.all()` seguido de `User.query.get` + `Category.query.get` por linha; em `summary_report`, loop sobre todos os users com `Task.query.filter_by(user_id=u.id).all()` interno — quadrático. |
| HIGH | Lógica de negócio embutida em routes | `routes/task_routes.py:30-39, 71-80, 273-296` + `routes/report_routes.py:13-101` | Cálculo de overdue duplicado em 4 sites; `summary_report` constrói o relatório inteiro de 89 linhas dentro do handler HTTP; `task_stats` agrega estatísticas inline. |
| MEDIUM | Validação duplicada entre POST/PUT + validator paralelo morto em `utils/` | `routes/task_routes.py:92-144` vs `:166-213` + `utils/helpers.py:57-108` | Drift entre create e update (só create checa `len(title) < 3`); `process_task_data` (51 linhas) é um validador completo que **nenhuma route importa**. |
| MEDIUM | `except:` bare engolindo tracebacks em todo lugar | `routes/task_routes.py:62, 137, 204, 236` + `routes/report_routes.py:186, 207, 221` | 16 sites do padrão `except: return jsonify({'error': 'Erro interno'}), 500` — esconde o tipo real do erro, impede logging estruturado. |
| MEDIUM | `delete_user` faz cascade manual em vez de declarar na model | `routes/user_routes.py:140-142` | Loop deletando `Task.query.filter_by(user_id=user_id).all()` antes do user; o relationship existe (`u.tasks` na linha 22) mas sem `cascade='all, delete-orphan'` — frágil, invisível para migrations. |
| LOW | Imports não usados em quase todo arquivo | `app.py:7` + `routes/task_routes.py:7` + `routes/user_routes.py:6` + `routes/report_routes.py:8` + `utils/helpers.py:3-7` | `import os, sys, json, datetime` (só `datetime` usado), `import json, os, sys, time` (nenhum usado), etc. — bloat cognitivo. |
| LOW | Magic strings/numbers em routes mesmo com constantes prontas em `utils/helpers.py` | `routes/task_routes.py:32, 110, 113, 177, 182, 243` + `utils/helpers.py:110-116` | `VALID_STATUSES`, `MAX_TITLE_LENGTH`, etc., já existem; nenhuma route importa — drift garantido. |
| LOW | `type(x) == list` em vez de `isinstance(x, list)` | `routes/task_routes.py:141, 210` + `utils/helpers.py:103` | Não trata subclasses, viola idiom Python e quebra duck-typing. |

**Distribuição:** CRITICAL 1 / HIGH 3 / MEDIUM 3 / LOW 3 — **total 10**.

### Distribuição agregada

| Severidade | Projeto 1 | Projeto 2 | Projeto 3 | Total |
|---|---:|---:|---:|---:|
| CRITICAL | 4 | 3 | 1 | 8 |
| HIGH | 2 | 2 | 3 | 7 |
| MEDIUM | 2 | 3 | 3 | 8 |
| LOW | 3 | 2 | 3 | 8 |
| **Total** | **11** | **10** | **10** | **31** |
| Atende ≥1 CRIT/HIGH + ≥2 MED + ≥2 LOW? | ✓ | ✓ | ✓ | — |

---

## B) Construção da Skill

Esta seção descreve o que mora em `.claude/skills/refactor-arch/` e por que cada peça existe. A fonte canônica é [`code-smells-project/.claude/skills/refactor-arch/`](code-smells-project/.claude/skills/refactor-arch/); as cópias nos outros projetos são **bit-identical** (ver §Garantia de agnosticismo abaixo).

### Anatomia da skill

```
.claude/skills/refactor-arch/
├── SKILL.md                  # prompt da skill — 3 fases, gate de Fase 2, princípios operacionais
├── analise-projeto.md        # heurísticas Fase 1: lookup tables por extensão/manifest/imports
├── catalog-antipatterns.md   # 10 anti-patterns, severidade, stacks-keyed, sinais de detecção
├── template-relatorio.md     # contrato do reports/audit-project-<N>.md (campos, ordem, totais)
├── playbook-refactor.md      # 8 receitas de transformação com blocos Before/After de código
└── guidelines-arquitetura.md # contrato MVC alvo + regras de layering + checks gravados em grep
```

`SKILL.md` é o prompt do agente e contém **zero código Python ou JavaScript**. Tudo que é stack-específico mora nas tabelas dos arquivos de referência (campo `Stacks:` em cada entrada do catálogo; seção "Framework-specific bindings" em `guidelines-arquitetura.md`). É o que torna a skill agnóstica de tecnologia por construção (invariante I-1 em [`plans/P001-design-contract.md`](plans/P001-design-contract.md)).

### Decisões de design

- **Escala de severidade fixa.** CRITICAL → HIGH → MEDIUM → LOW exatamente como definido no `desafio.md` linhas 20-23 (invariante I-2). Relatórios ordenam estritamente nesta direção.
- **Três fases sequenciais com gate de Fase 2.** O agente é proibido de mexer em arquivos antes do operador digitar `y`/`yes` (invariante I-4); a sentença literal `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` está embutida em `SKILL.md` e é emitida como última linha da Fase 2.
- **Findings com `file:line` exato.** Nada de "código ruim em controllers"; cada entrada do relatório tem `path.ext:linha` ou `path.ext:início-fim` (invariante I-3). Recomendações terminam com o slug do recipe do playbook em backticks — esse slug é a chave de roteamento da Fase 3.
- **Catálogo stack-keyed, não hardcoded.** Toda entrada do catálogo declara `Stacks: any | python-flask | python-generic | nodejs-express | nodejs-generic`. O agente filtra por stack detectado em Fase 1 antes de aplicar sinais. Isso é o que permite a mesma skill rodar em Python e Node sem edits entre projetos.
- **Receitas com Before/After de código, não prosa.** Cada uma das 8 receitas do playbook traz um bloco `Before` e um `After` em código real; recomendação é um patch reproduzível, não um conselho.
- **Composition root explícito.** Toda refatoração converge para um `app.py`/`app.js` no root cujo único papel é instanciar o framework, registrar middleware, montar routes e fechar com `db.init_app(app)`/`app.listen(...)`. Lógica de negócio vive em `src/controllers/`.
- **Relatórios são a trilha de auditoria.** A seção "Operating principles" do `SKILL.md` é explícita: o chat não é registro; tudo que aconteceu em Fase 2 e Fase 3 fica em `reports/audit-project-<N>.md`.

### Catálogo de anti-patterns (10 entradas)

Fonte: [`catalog-antipatterns.md`](code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md). Distribuição: **3 CRITICAL / 2 HIGH / 3 MEDIUM / 2 LOW = 10**, excedendo o mínimo de ≥8 do `desafio.md` (linha 174). Inclui detecção explícita de APIs deprecated (`deprecated-api-call`), exigida pelo `desafio.md` linha 175.

| Slug | Severidade | Stacks | Detecção (sumário) |
|---|---|---|---|
| `god-class-or-god-module` | CRITICAL | any | arquivo > 200 LOC com handlers + SQL + validação + formatação para ≥2 domínios |
| `hardcoded-credentials` | CRITICAL | any | regex `(SECRET_KEY\|PASSWORD\|TOKEN)\s*[=:]\s*['\"]…['\"]` + shapes `pk_live_*`, `AKIA*`, `ghp_*` |
| `sql-injection-string-concat` | CRITICAL | python-flask, python-generic, nodejs-express, nodejs-generic | `cursor.execute(<concat>)`, `db.run(\`...${x}\`)`, endpoints tipo `/admin/query` |
| `business-logic-in-route-or-controller` | HIGH | any | handler > 40 LOC; route que lê de um modelo + escreve em outro + dispara notificação |
| `n+1-query` | HIGH | any | query em loop após query inicial; falta de `joinedload`/`include`/`Promise.all` |
| `bare-except-or-catch-all` | MEDIUM | any | `except:` vazio, `catch (err) {}` vazio, ausência de `@app.errorhandler`/`app.use(error)` |
| `duplicate-validation-logic` | MEDIUM | any | POST e PUT do mesmo recurso com blocos `if not data[...]` quase idênticos; módulos `validate*` órfãos |
| `deprecated-api-call` | MEDIUM | any | Flask `@app.before_first_request`, `flask.escape`; Python `datetime.utcnow()`, `crypt`, `cgi`; SQLAlchemy `Query.get`; Node `new Buffer(x)`, `createCipher`, `sqlite3.verbose()` |
| `magic-numbers-or-inline-whitelist` | LOW | any | literais em comparações dentro de routes/controllers; whitelists inline `if x in [...]`; módulos de constantes não importados |
| `inconsistent-response-envelope` | LOW | any | mistura de `jsonify(dict)`/`jsonify(list)`/`{"erro":…}`/`res.send("text")` sem helper único |

### Playbook de refatoração (8 receitas)

Fonte: [`playbook-refactor.md`](code-smells-project/.claude/skills/refactor-arch/playbook-refactor.md). Cada recipe carrega `Steps:`, `Before:`, `After:` e `Validation hint:`. Cobertura 1:N onde necessário — 2 recipes mapeiam para mais de uma entrada do catálogo (cobertura completa documentada no fim de `playbook-refactor.md`).

| Recipe | Fixes (slug do catálogo) | Aplicabilidade |
|---|---|---|
| `extract-config-to-env-or-settings-module` | hardcoded-credentials | any |
| `split-god-class-into-controllers-by-domain` | god-class-or-god-module | any |
| `replace-raw-sql-with-parameterised-queries` | sql-injection-string-concat | python-flask, python-generic, nodejs-express, nodejs-generic |
| `eager-load-relationships-to-fix-n+1` | n+1-query | any |
| `move-business-logic-from-route-to-controller` | business-logic-in-route-or-controller + duplicate-validation-logic | any |
| `replace-bare-except-with-typed-handler-and-error-middleware` | bare-except-or-catch-all + inconsistent-response-envelope | any |
| `replace-deprecated-api-call-with-current-equivalent` | deprecated-api-call | any |
| `lift-magic-numbers-and-whitelists-into-constants-module` | magic-numbers-or-inline-whitelist | any |

### Garantia de agnosticismo

A skill é tecnologicamente agnóstica por construção (invariante I-1). A evidência viva é binária e mecânica:

```
$ diff -rq code-smells-project/.claude/skills/refactor-arch \
           ecommerce-api-legacy/.claude/skills/refactor-arch
(saída vazia)

$ diff -rq code-smells-project/.claude/skills/refactor-arch \
           task-manager-api/.claude/skills/refactor-arch
(saída vazia)

$ diff -rq ecommerce-api-legacy/.claude/skills/refactor-arch \
           task-manager-api/.claude/skills/refactor-arch
(saída vazia)
```

Os 6 arquivos da skill são **bit-identical** nas 3 cópias. As três execuções (`/refactor-arch` em P1, P2, P3) usaram o mesmo prompt, o mesmo catálogo e o mesmo playbook — sem edits intermediários entre projetos. Heurísticas de detecção (`analise-projeto.md`) e filtros stack-keyed (`Stacks:` em cada entrada do catálogo) é o que separa o tratamento Python flat × Node flat × Python parcialmente organizado.

### Desafios encontrados

- **Improve-not-rewrite para o projeto 3.** O `task-manager-api/` já tinha `models/`, `routes/`, `services/`, `utils/` no root. A tentação era reescrever os 299 LOC de `routes/task_routes.py` do zero. A disciplina forçou **mover** os arquivos para `src/` e **adicionar** as camadas que faltavam (`config/`, `controllers/`, `middlewares/`, `errors/`, `schemas/`) — preservando o conteúdo funcional onde nenhum finding do catálogo o atacava. O risco está documentado na seção "Risks specific to this session" de [`plans/P001-S006-exec-projeto-3.md`](plans/P001-S006-exec-projeto-3.md).
- **SQLAlchemy 2.x deprecations no projeto 3.** `Model.query.get(id)` (16 sites) e `datetime.utcnow()` (18 sites) são deprecated em SQLAlchemy 2.x e Python 3.12 respectivamente. A recipe `replace-deprecated-api-call-with-current-equivalent` exigia uma única passagem mecânica + verificação por `grep -rEn '\.query\.get\(\|datetime\.utcnow' src/` retornando vazio.
- **N+1 em Node com contadores manuais (projeto 2).** Idioma diferente do Python-SQLAlchemy `joinedload`. A recipe `eager-load-relationships-to-fix-n+1` teve que ser genérica o suficiente para descrever JOIN raw (Node), `joinedload` (Python+SQLAlchemy), `include` (Prisma) e `populate` (Mongoose) com o mesmo texto. A passagem do `Promise.all`/single-JOIN no `financial-report` mostrou que funciona.
- **Enforcement do halt de Fase 2.** A tentação natural do agente é resumir e seguir; a frase verbatim `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` precisa ser a **última linha** da resposta e o agente precisa parar ali. A seção "Operating principles" do `SKILL.md` ("Confirm before destruction") é o que mantém o gate honesto.
- **Cobertura cross-stack do catálogo.** A entrada `deprecated-api-call` enumera deprecations Python *e* Node lado a lado em uma única entrada. Splittar em duas (Python-deprecated + Node-deprecated) teria inflado o catálogo para 12+ entradas com lógica redundante. A unificação ficou no campo `Detection signals:` por bloco de stack.

---

## C) Resultados

### Resumo dos relatórios de auditoria

| Projeto | Stack | LOC | Findings (C/H/M/L) | Total | Boot port | Residuais |
|---|---|---|---|---|---|---|
| Projeto 1 — [`code-smells-project/`](code-smells-project/) | Python + Flask 3.1.1 | ~780 | 3/2/2/2 | **9** | 5050 | password hashing (não-coberto pelo recipe v1); slug `global-mutable-state` faltando no catálogo (defect foi consertado estruturalmente via Flask `g` pattern) |
| Projeto 2 — [`ecommerce-api-legacy/`](ecommerce-api-legacy/) | Node.js + Express ^4.18.2 | ~180 | 2/2/2/2 | **8** | 3131 | `fake-or-broken-crypto`, `missing-orm-cascade`, `global-mutable-state`, `in-memory-db-in-prod`, `pii-or-card-in-logs` (5 slugs ausentes do catálogo v1) |
| Projeto 3 — [`task-manager-api/`](task-manager-api/) | Python + Flask 3.0.0 + SQLAlchemy 3.1.1 | ~1158 | 1/2/3/2 | **8** | 5151 | `fake-jwt-token-issuance`, `missing-auth-middleware` (cascade foi consertada estruturalmente via `User.tasks` cascade declaration) |
| **Total** | — | ~2118 | 6/6/7/6 | **25** | — | — |

Os 3 relatórios completos estão em [`reports/audit-project-1.md`](reports/audit-project-1.md), [`reports/audit-project-2.md`](reports/audit-project-2.md), [`reports/audit-project-3.md`](reports/audit-project-3.md).

### Antes e depois

#### Projeto 1 — `code-smells-project/`

```
ANTES                                    DEPOIS
─────────────────                        ─────────────────────────────
code-smells-project/                     code-smells-project/
├── app.py        (88 LOC)               ├── app.py            (22 LOC, composition root)
├── controllers.py (292 LOC, 17 handlers)├── .env.example
├── models.py    (314 LOC, raw SQL)      ├── requirements.txt
├── database.py  (86 LOC, DDL + seed)    └── src/
├── requirements.txt                         ├── config/{settings.py, constants.py}
└── loja.db (commitado, regen. on boot)      ├── errors/__init__.py
                                             ├── middlewares/error_handler.py
                                             ├── services/notification_service.py
                                             ├── models/{produto, usuario, pedido}_model.py
                                             ├── schemas/{produto, usuario, pedido}_schema.py
                                             ├── controllers/{produto, usuario,
                                             │   pedido, relatorio, health}_controller.py
                                             └── views/{response.py,
                                                 produto_routes.py, usuario_routes.py,
                                                 pedido_routes.py, relatorio_routes.py,
                                                 health_routes.py}
```

`controllers.py`/`models.py`/`database.py` removidos. Endpoints `/admin/reset-db` e `/admin/query` deletados (eram parte do attack surface). `/health` não vaza mais o `SECRET_KEY`. Detalhes do refactor em [`plans/P001-S004-results.md`](plans/P001-S004-results.md), commit `4abae1fd7597dbada9012cddca6a567682063b1d`.

#### Projeto 2 — `ecommerce-api-legacy/`

```
ANTES                                    DEPOIS
─────────────────                        ─────────────────────────────
ecommerce-api-legacy/                    ecommerce-api-legacy/
├── src/                                 ├── src/
│   ├── app.js     (14 LOC bootstrap)    │   ├── app.js  (~25 LOC, composition root)
│   ├── AppManager.js (141 LOC god)      │   ├── config/{settings.js, constants.js}
│   └── utils.js   (25 LOC kitchen-sink) │   ├── errors/index.js
├── api.http                             │   ├── middlewares/error_handler.js
└── package.json                         │   ├── services/{payment, audit, cache,
                                         │   │   legacy_crypto}_service.js
                                         │   ├── models/{db, user, course, enrollment,
                                         │   │   payment, audit, report}_model.js
                                         │   ├── controllers/{checkout, admin,
                                         │   │   user}_controller.js
                                         │   └── views/{response, checkout_routes,
                                         │       admin_routes, user_routes, index}.js
                                         ├── api.http
                                         ├── package.json
                                         └── .env.example
```

`AppManager.js` e `utils.js` removidos. Decisão `cc.startsWith("4")` agora é `PAYMENT_APPROVED_CARD_PREFIX` em constants. Chave Stripe e card-number não aparecem mais em log. Detalhes em [`plans/P001-S005-results.md`](plans/P001-S005-results.md), commit `d33fa8399d997cc067863ac5703326aebb0ec13e`.

#### Projeto 3 — `task-manager-api/`  (improve-not-rewrite)

```
ANTES                                    DEPOIS
─────────────────                        ─────────────────────────────
task-manager-api/                        task-manager-api/
├── app.py       (35 LOC)                ├── app.py    (50 LOC, composition root)
├── database.py  (3 LOC)                 ├── seed.py
├── seed.py                              ├── requirements.txt
├── requirements.txt                     ├── .env.example
├── models/{__init__, task,              └── src/
│           user, category}.py               ├── config/{settings.py, constants.py}
├── routes/{__init__, task_routes,           ├── errors/__init__.py
│           user_routes,                     ├── middlewares/error_handler.py
│           report_routes}.py                ├── services/notification_service.py
├── services/{__init__,                      ├── models/{__init__ (db=SQLAlchemy()),
│             notification_service}.py       │           task.py, user.py, category.py}
└── utils/{__init__, helpers.py              ├── schemas/{task, user, category}_schema.py
        (contém process_task_data           ├── controllers/{task, user, report,
        morto + constantes não               │               category}_controller.py
        importadas)}                         ├── views/{__init__ (register_blueprints),
                                             │           response.py, task_routes.py,
                                             │           user_routes.py, report_routes.py,
                                             │           category_routes.py}
                                             └── utils/helpers.py  (apenas funções puras +
                                                  now_utc(); constantes movidas para
                                                  src/config/constants.py;
                                                  process_task_data adotado como schema)
```

> **Nota — improve-not-rewrite:** As pastas `models/`, `routes/`, `services/`, `utils/` no root **foram movidas para `src/`**, não substituídas. Conteúdo funcional foi preservado linha a linha onde nenhum finding do catálogo o atacava; novas camadas (`config/`, `controllers/`, `middlewares/`, `errors/`, `schemas/`, `views/response.py`) foram adicionadas. O cascade `User.tasks = db.relationship('Task', back_populates='user', cascade='all, delete-orphan')` substitui o loop manual em `delete_user` (residual da S001 consertado estruturalmente). 18 `datetime.utcnow()` e 16 `Model.query.get(...)` migrados para `now_utc()` e `db.session.get(Model, id)`. `marshmallow==3.20.1` (no `requirements.txt` mas morto) foi adotado nos schemas.

Detalhes em [`plans/P001-S006-results.md`](plans/P001-S006-results.md), commit `79747f501fced6e29551a49def129dd17fc90009`.

### Validação por projeto

#### Projeto 1 — code-smells-project

Boot command:

```bash
cd code-smells-project
SECRET_KEY=test-key-do-not-commit DEBUG=false PORT=5050 python app.py
```

Boot outcome: OK — servidor Werkzeug em `http://0.0.0.0:5050`. A porta 5000 estava ocupada pelo macOS AirPlay; o `PORT` env var foi honrado via `src/config/settings.py` (prova que config é genuinamente env-loaded).

Smoke test (extraído de [`reports/audit-project-1.md`](reports/audit-project-1.md) §Validation):

| Endpoint | Método | HTTP | Pass? |
|---|---|---|---|
| `/` | GET | 200 | YES |
| `/health` | GET | 200 | YES (secret_key não aparece mais — leak fixed) |
| `/produtos` | GET | 200 | YES |
| `/produtos/1` | GET | 200 | YES |
| `/produtos/busca?q=Notebook` | GET | 200 | YES |
| `/produtos` | POST | 201 | YES |
| `/produtos/1` | PUT | 200 | YES |
| `/produtos/11` | DELETE | 200 | YES |
| `/usuarios` | GET | 200 | YES |
| `/usuarios` | POST | 201 | YES |
| `/login` (`joao@email.com`/`123456`) | POST | 200 | YES |
| `/login` (`x' OR 1=1 --`/`y`) | POST | **401** | YES (**SQL injection fix verificado**) |
| `/pedidos` (criar com 1 item) | POST | 201 | YES |
| `/pedidos` | GET | 200 | YES (N+1 corrigido por single JOIN) |
| `/pedidos/usuario/2` | GET | 200 | YES (N+1 corrigido) |
| `/pedidos/1/status` (`aprovado`) | PUT | 200 | YES (notification via service) |
| `/relatorios/vendas` | GET | 200 | YES (1 query agregada; tiers em controller) |
| `/admin/reset-db` | POST | **404** | YES (endpoint deletado em Fase 3) |
| `/admin/query` | POST | **404** | YES (endpoint deletado em Fase 3) |

**17 endpoints funcionais respondendo + 2 endpoints admin corretamente 404 = 19/19**, 0 regressões.

```markdown
## Checklist de Validação — Projeto 1

### Fase 1 — Análise
- [x] Linguagem detectada corretamente — see plans/P001-S004-results.md "Phase 1 evidence" (Language: python)
- [x] Framework detectado corretamente — see plans/P001-S004-results.md (Framework: python-flask Flask 3.1.1)
- [x] Domínio da aplicação descrito corretamente — see plans/P001-S004-results.md (Domain: E-commerce API)
- [x] Número de arquivos analisados condiz com a realidade — 4 files, see reports/audit-project-1.md header

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência — see reports/audit-project-1.md vs template-relatorio.md skeleton
- [x] Cada finding tem arquivo e linhas exatos — see reports/audit-project-1.md File: lines for all 9 findings
- [x] Findings ordenados por severidade (CRITICAL → LOW) — see reports/audit-project-1.md §Findings order
- [x] Mínimo de 5 findings identificados — 9 ≥ 5, see reports/audit-project-1.md §Summary
- [x] Detecção de APIs deprecated incluída (se aplicável) — não aplicável a P1 (catálogo varreu, 0 matches honestos)
- [x] Skill pausa e pede confirmação antes da Fase 3 — see reports/audit-project-1.md last line of §Findings + "Operator response: y"

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC — see reports/audit-project-1.md §New project structure
- [x] Configuração extraída para módulo de config (sem hardcoded) — src/config/settings.py + .env.example
- [x] Models criados para abstrair dados — src/models/{produto,usuario,pedido}_model.py
- [x] Views/Routes separadas para visualização ou roteamento — src/views/*_routes.py + response.py
- [x] Controllers concentram o fluxo da aplicação — src/controllers/{produto,usuario,pedido,relatorio,health}_controller.py
- [x] Error handling centralizado — src/middlewares/error_handler.py + src/errors/__init__.py
- [x] Entry point claro — app.py reduced to 22 LOC composition root
- [x] Aplicação inicia sem erros — see plans/P001-S004-results.md Boot outcome: OK
- [x] Endpoints originais respondem corretamente — 17 funcionais YES + 2 admin 404 esperado = 19/19, see reports/audit-project-1.md §Validation
```

#### Projeto 2 — ecommerce-api-legacy

Boot command:

```bash
cd ecommerce-api-legacy
npm install
DB_PASS=test PAYMENT_GATEWAY_KEY=test-key PORT=3131 node src/app.js
```

Boot outcome: OK — Express em `http://0.0.0.0:3131`. Portas 3000 (sistema) e 3030 (Docker) ocupadas; `PORT` env var foi honrado via `src/config/settings.js`. `DB_PASS` e `PAYMENT_GATEWAY_KEY` são marcados `required()` no settings — boot lança se forem ausentes (env-loading genuinamente fail-fast).

Smoke test (extraído de [`reports/audit-project-2.md`](reports/audit-project-2.md) §Validation):

| Endpoint | Payload | HTTP | Pass? |
|---|---|---|---|
| `POST /api/checkout` | Visa válido | 200 | YES (`enrollment_id` retornado; envelope `{status: "ok"}`) |
| `POST /api/checkout` | cartão não-Visa | 400 | YES (`payment_denied`; decisão por constante) |
| `POST /api/checkout` | campos faltando | 400 | YES (`validation_error`; ValidationError caught by middleware) |
| `GET /api/admin/financial-report` | — | 200 | YES (single JOIN; N+1 corrigido) |
| `DELETE /api/users/1` | — | 200 | YES (JSON envelope; texto plain-text-com-bug removido) |

**5/5 endpoints**, 0 regressões. A confissão de bug `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco"` foi removida; o defeito subjacente (cascade ausente) ficou como residual #2 documentado.

```markdown
## Checklist de Validação — Projeto 2

### Fase 1 — Análise
- [x] Linguagem detectada corretamente — see plans/P001-S005-results.md "Phase 1 evidence" (Language: javascript)
- [x] Framework detectado corretamente — see plans/P001-S005-results.md (Framework: nodejs-express Express ^4.18.2)
- [x] Domínio da aplicação descrito corretamente — see plans/P001-S005-results.md (Domain: LMS API)
- [x] Número de arquivos analisados condiz com a realidade — 3 files, see reports/audit-project-2.md header

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência — see reports/audit-project-2.md vs template-relatorio.md skeleton
- [x] Cada finding tem arquivo e linhas exatos — see reports/audit-project-2.md File: lines for all 8 findings
- [x] Findings ordenados por severidade (CRITICAL → LOW) — see reports/audit-project-2.md §Findings order
- [x] Mínimo de 5 findings identificados — 8 ≥ 5, see reports/audit-project-2.md §Summary
- [x] Detecção de APIs deprecated incluída (se aplicável) — see reports/audit-project-2.md MEDIUM finding sqlite3.verbose()
- [x] Skill pausa e pede confirmação antes da Fase 3 — see reports/audit-project-2.md last line of §Findings + "Operator response: y"

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC — see reports/audit-project-2.md §New project structure
- [x] Configuração extraída para módulo de config (sem hardcoded) — src/config/settings.js + .env.example; required() throws on missing
- [x] Models criados para abstrair dados — src/models/{db,user,course,enrollment,payment,audit,report}_model.js
- [x] Views/Routes separadas para visualização ou roteamento — src/views/*_routes.js + response.js
- [x] Controllers concentram o fluxo da aplicação — src/controllers/{checkout,admin,user}_controller.js
- [x] Error handling centralizado — src/middlewares/error_handler.js (4-arg signature) + src/errors/index.js
- [x] Entry point claro — src/app.js reduced to ~25 LOC composition root
- [x] Aplicação inicia sem erros — see plans/P001-S005-results.md Boot outcome: OK
- [x] Endpoints originais respondem corretamente — 5/5, see reports/audit-project-2.md §Validation
```

#### Projeto 3 — task-manager-api

Boot command (seed → boot):

```bash
cd task-manager-api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
SECRET_KEY=test-do-not-commit DEBUG=false PORT=5151 .venv/bin/python seed.py
SECRET_KEY=test-do-not-commit DEBUG=false PORT=5151 .venv/bin/python app.py
```

Boot outcome: OK — Flask em `http://127.0.0.1:5151` após `seed.py` semear 3 usuários / 4 categorias / 10 tasks. Porta 5151 escolhida para evitar 5000 (AirPlay), 5050 (cache do P1), 3030/3131 (P2).

Smoke test (extraído de [`reports/audit-project-3.md`](reports/audit-project-3.md) §Validation):

| Endpoint | Método | HTTP | Pass? |
|---|---|---|---|
| `/` | GET | 200 | YES |
| `/health` | GET | 200 | YES |
| `/tasks` | GET | 200 | YES (N+1 corrigido via joinedload) |
| `/tasks` | POST | 201 | YES |
| `/tasks/{id}` | GET | 200 | YES |
| `/tasks/{id}` | PUT | 200 | YES |
| `/tasks/{id}` | DELETE | 200 | YES |
| `/tasks/search?q=login` | GET | 200 | YES |
| `/tasks/stats` | GET | 200 | YES |
| `/users` | GET | 200 | YES |
| `/users` | POST | 201 | YES |
| `/users/{id}` | GET | 200 | YES |
| `/users/{id}` | PUT | 200 | YES |
| `/users/{id}` | DELETE | 200 | YES (cascade automático) |
| `/users/{id}/tasks` | GET | 200 | YES |
| `/login` | POST | 200 | YES |
| `/reports/summary` | GET | 200 | YES (aggregate query; N+1 do user_productivity corrigido) |
| `/reports/user/{id}` | GET | 200 | YES |
| `/categories` | GET | 200 | YES |
| `/categories` | POST | 201 | YES |
| `/categories/{id}` | PUT | 200 | YES |
| `/categories/{id}` | DELETE | 200 | YES |
| `/tasks/9999` (404 envelope check) | GET | 404 | YES (`{status:error, error:{code:not_found}}`) |
| `/tasks` (validation envelope check) | POST `{"title":"x"}` | 400 | YES (`{status:error, error:{code:validation_error}}`) |

**22 endpoints felizes + 2 negativos = 24/24**, 0 regressões.

```markdown
## Checklist de Validação — Projeto 3

### Fase 1 — Análise
- [x] Linguagem detectada corretamente — see plans/P001-S006-results.md "Phase 1 evidence" (Language: python)
- [x] Framework detectado corretamente — see plans/P001-S006-results.md (Framework: python-flask Flask 3.0.0 + Flask-SQLAlchemy 3.1.1)
- [x] Domínio da aplicação descrito corretamente — see plans/P001-S006-results.md (Domain: Task Manager API)
- [x] Número de arquivos analisados condiz com a realidade — 15 .py files, see reports/audit-project-3.md header

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência — see reports/audit-project-3.md vs template-relatorio.md skeleton
- [x] Cada finding tem arquivo e linhas exatos — see reports/audit-project-3.md File: lines for all 8 findings
- [x] Findings ordenados por severidade (CRITICAL → LOW) — see reports/audit-project-3.md §Findings order
- [x] Mínimo de 5 findings identificados — 8 ≥ 5, see reports/audit-project-3.md §Summary
- [x] Detecção de APIs deprecated incluída (se aplicável) — see reports/audit-project-3.md MEDIUM finding deprecated-api-call (18 datetime.utcnow + 16 Model.query.get)
- [x] Skill pausa e pede confirmação antes da Fase 3 — see reports/audit-project-3.md last line of §Findings + "Operator answered y on 2026-05-18"

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC — see reports/audit-project-3.md §New project structure
- [x] Configuração extraída para módulo de config (sem hardcoded) — src/config/{settings.py, constants.py} + .env.example; SECRET_KEY fail-fast
- [x] Models criados para abstrair dados — src/models/{__init__ (db), task.py, user.py, category.py}; back_populates + cascade declarado
- [x] Views/Routes separadas para visualização ou roteamento — src/views/{task,user,report,category}_routes.py + response.py
- [x] Controllers concentram o fluxo da aplicação — src/controllers/{task,user,report,category}_controller.py
- [x] Error handling centralizado — src/middlewares/error_handler.py + src/errors/__init__.py
- [x] Entry point claro — app.py é composition root (6 src.* imports, 0 business logic)
- [x] Aplicação inicia sem erros — see plans/P001-S006-results.md Boot outcome: OK on port 5151
- [x] Endpoints originais respondem corretamente — 22 funcionais YES + 2 envelope checks YES = 24/24, see reports/audit-project-3.md §Validation
```

### Critérios de aceite (`desafio.md` linhas 415-426)

| Critério | Projeto 1 | Projeto 2 | Projeto 3 | Status |
|---|---|---|---|---|
| Fase 1 detecta stack corretamente | ✓ (Python/Flask 3.1.1) | ✓ (Node/Express ^4.18.2) | ✓ (Python/Flask 3.0.0 + SQLAlchemy 3.1.1) | **OBRIGATÓRIO — 3/3** |
| Fase 2 encontra ≥ 5 findings | ✓ (9) | ✓ (8) | ✓ (8) | **OBRIGATÓRIO — 3/3** |
| Fase 2 inclui ≥ 1 CRITICAL ou HIGH | ✓ (3 CRIT + 2 HIGH = 5) | ✓ (2 CRIT + 2 HIGH = 4) | ✓ (1 CRIT + 2 HIGH = 3) | **OBRIGATÓRIO — 3/3** |
| Fase 3 aplicação funciona após refatoração | ✓ (19/19 endpoints) | ✓ (5/5 endpoints) | ✓ (24/24 endpoints) | **OBRIGATÓRIO — 3/3** |

Evidência de cada célula nos respectivos `plans/P001-S00{4,5,6}-results.md` e `reports/audit-project-{1,2,3}.md`. Hashes dos commits-bootstrap: P1 `4abae1f`, P2 `d33fa83`, P3 `79747f5`.

### Observações cross-stack

- **O bloco de Fase 1 tem a mesma forma em todos os projetos.** Mesmo campos (`Language: / Framework: / Dependencies: / Domain: / Architecture: / Source files: / DB tables:`), mesma ordem; só o conteúdo muda. É a evidência de que o template de detecção mora em `analise-projeto.md`, não em prompt-templates separados por stack.
- **Filtro `Stacks:` do catálogo funciona em ambas as direções.** Em P3 (Flask-SQLAlchemy), o slug `sql-injection-string-concat` rodou e reportou **zero matches honestamente** — SQLAlchemy ORM faz binding por construção. Em P1 (raw `sqlite3.cursor.execute` com concatenação) o mesmo slug fez 14 matches. A skill nunca inventa findings para bater a meta.
- **O caso "improve-not-rewrite" funcionou.** P3 começava com `models/`, `routes/`, `services/`, `utils/` já presentes. A skill reconheceu (Fase 1 reportou `Architecture: partially-organised`), preservou o conteúdo funcional, moveu para `src/`, e adicionou só as camadas que faltavam — em vez de reescrever os 299 LOC de `routes/task_routes.py` do zero.
- **Padrão `success() / error_handler` é idêntico em ambos os stacks.** A recipe `replace-bare-except-with-typed-handler-and-error-middleware` produz envelope `{status: ok, data: …}` ↔ `{status: error, error: {code, message}}` tanto em Flask (`@app.errorhandler`) quanto em Express (`app.use((err, req, res, next) => ...)` com assinatura de 4 args). Um único recipe, dois idiomas.

---

## D) Como Executar

### Pré-requisitos

- **Claude Code CLI** instalado e autenticado. Skills oficialmente suportadas em `.claude/skills/<nome>/SKILL.md`.
- **Python 3.11+** para os projetos 1 e 3. Projeto 3 usa SQLAlchemy 2.x (`db.session.get`, `case((...))` form); 3.11 ou 3.12 são as versões testadas.
- **Node.js 18+** para o projeto 2.
- **`git`** para clonar o fork.
- **macOS / Linux** terminal. Comandos abaixo usam zsh/bash; em ambos a sintaxe é idêntica.

> Portas 5000 (AirPlay no macOS), 3000 (geralmente em uso por dev local), 3030 (Docker). Os comandos abaixo já usam portas livres (5050, 3131, 5151) via `PORT=...`.

### Executar a skill em cada projeto

A skill já está copiada em todos os 3 projetos sob `.claude/skills/refactor-arch/` (bit-identical entre eles).

```bash
# Projeto 1 — code-smells-project (Python/Flask)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — ecommerce-api-legacy (Node.js/Express)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — task-manager-api (Python/Flask, parcialmente organizado)
cd ../task-manager-api
claude "/refactor-arch"
```

Quando a Fase 2 imprimir a linha:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

responda `y` (ou `yes`) para autorizar a Fase 3. Qualquer outra resposta encerra a execução sem tocar em arquivos (`Phase 3 skipped by operator.`).

### Validar a refatoração

Esta entrega já trouxe a Fase 3 executada e commitada nos três projetos (veja a §Resultados). Para reproduzir a validação de boot+endpoint localmente, use os comandos abaixo (idênticos aos registrados nos `*-results.md`):

#### Projeto 1 — code-smells-project

```bash
cd code-smells-project
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
SECRET_KEY=test-key-do-not-commit DEBUG=false PORT=5050 .venv/bin/python app.py
# em outro terminal:
curl http://127.0.0.1:5050/health
curl http://127.0.0.1:5050/produtos
curl -X POST -H 'Content-Type: application/json' http://127.0.0.1:5050/login \
     -d '{"email":"joao@email.com","senha":"123456"}'
# SQL-injection check (deve retornar 401, não 200):
curl -X POST -H 'Content-Type: application/json' http://127.0.0.1:5050/login \
     -d "{\"email\":\"x' OR 1=1 --\",\"senha\":\"y\"}"
```

#### Projeto 2 — ecommerce-api-legacy

```bash
cd ecommerce-api-legacy
npm install
DB_PASS=test PAYMENT_GATEWAY_KEY=test-key PORT=3131 node src/app.js
# em outro terminal:
curl -X POST -H 'Content-Type: application/json' http://127.0.0.1:3131/api/checkout \
     -d '{"usr":"Guilherme","eml":"guilherme@test.com","pwd":"123456","c_id":2,"card":"4111111111111111"}'
curl http://127.0.0.1:3131/api/admin/financial-report
curl -X DELETE http://127.0.0.1:3131/api/users/1
```

Mais payloads em [`ecommerce-api-legacy/api.http`](ecommerce-api-legacy/api.http).

#### Projeto 3 — task-manager-api

```bash
cd task-manager-api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
SECRET_KEY=test-do-not-commit DEBUG=false PORT=5151 .venv/bin/python seed.py
SECRET_KEY=test-do-not-commit DEBUG=false PORT=5151 .venv/bin/python app.py
# em outro terminal:
curl http://127.0.0.1:5151/health
curl http://127.0.0.1:5151/tasks
curl http://127.0.0.1:5151/reports/summary
curl -X POST -H 'Content-Type: application/json' http://127.0.0.1:5151/login \
     -d '{"email":"joao@email.com","password":"1234"}'
# envelope de erro (deve retornar {status:error, error:{code:not_found, ...}}):
curl http://127.0.0.1:5151/tasks/9999
```

### Onde ler os relatórios

- [`reports/audit-project-1.md`](reports/audit-project-1.md) — auditoria + bloco `Validation` do projeto 1
- [`reports/audit-project-2.md`](reports/audit-project-2.md) — auditoria + bloco `Validation` do projeto 2
- [`reports/audit-project-3.md`](reports/audit-project-3.md) — auditoria + bloco `Validation` do projeto 3

Para o ciclo de vida da entrega (sessões, verdicts, hashes de commit-bootstrap, residuais por sessão), veja [`plans/INDEX.md`](plans/INDEX.md) + [`plans/P001-S00{1..7}-results.md`](plans/).

### Como replicar a skill em um novo projeto

```bash
cp -R code-smells-project/.claude <new-project>/.claude
cd <new-project>
claude "/refactor-arch"
```

A skill faz **zero suposições** sobre linguagem ou framework. Toda detecção acontece em Fase 1 contra os arquivos reais do projeto. O catálogo filtra entradas pelo campo `Stacks:` antes de aplicar sinais — então rodar em uma stack desconhecida (ex.: Ruby/Rails, Go/Gin) ainda emite o bloco-resumo da Fase 1 corretamente; entradas do catálogo cuja seção `Stacks:` não cobre a stack apenas não disparam, sem erro. Para expandir a cobertura, basta adicionar entradas no catálogo com o novo tag de stack — o `SKILL.md` continua intacto.

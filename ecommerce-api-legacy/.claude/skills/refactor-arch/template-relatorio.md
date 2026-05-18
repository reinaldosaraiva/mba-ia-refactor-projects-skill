---
schema_version: 1
target_path: reports/audit-project-<N>.md
---

# Phase-2 report template

Every audit run produces one report file at `reports/audit-project-<N>.md` where `<N>` is the project ordinal (1 for `code-smells-project`, 2 for `ecommerce-api-legacy`, 3 for `task-manager-api`, or whatever ordinal the operator chooses for a new target). The report is also printed to stdout before the Phase-2 halt.

The format below is binding. Field names, section headings, and the ASCII separators are part of the contract — they let humans and tooling grep stable anchors.

## Skeleton

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project-name>
Stack:   <language> + <framework>
Files:   <N> analyzed | ~<LOC> lines of code
Generated: <ISO-8601 timestamp>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERITY>] <short title — match the catalog slug or a human-readable rendering>
File: <relative/path.ext:line-range>
Description: <1-2 sentences. State the anti-pattern present in the code.>
Impact: <1 sentence. Name the failure mode: security, maintainability, perf, testability.>
Recommendation: Apply playbook recipe `<playbook-slug>`.

<...repeat for every finding...>

================================
Total: <N> findings
================================
```

Phase 3 appends the validation block to the same file:

```markdown
## Validation

Boot command: `<the exact command used to start the refactored app>`
Boot outcome: <OK | failed — paste error excerpt>

| Endpoint | Method | HTTP status | Pass? |
|----------|--------|-------------|-------|
| /produtos | GET | 200 | YES |
| /produtos/1 | GET | 200 | YES |
| /pedidos | POST | 201 | YES |
| /login | POST | 200 | YES |
| ... | ... | ... | ... |

Regressions: <none | list endpoints that broke during refactor>
Residuals: <none | list catalog slugs intentionally left unfixed and why>
```

## Field rules

- **Project / Stack / Files** — required. Project name matches the working directory base name. Stack reads `<language> + <framework>` (e.g. `Python + Flask 3.1`).
- **Summary line** — required. Counts must equal the total findings; format is exactly `CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>`. Even zero counts must be listed (`CRITICAL: 0`) for grep stability.
- **Findings order** — strictly CRITICAL → HIGH → MEDIUM → LOW. Within a severity, group by file path; within a file, by line number ascending.
- **Finding heading** — `### [<SEVERITY>] <title>`. The severity tag in brackets must match one of the four levels exactly, in caps.
- **File field** — required, exact, `<path>:<line-range>` where line range is either a single number (`app.py:7`) or a range (`controllers.py:30-54`). Approximate ranges like `~30` are forbidden.
- **Description / Impact** — one to two sentences each, no bullet lists.
- **Recommendation** — must reference a playbook slug verbatim in backticks. Phase 3 routes the finding to that recipe; an unresolvable slug aborts the refactor for that finding.
- **Total** — required, equals the sum of severity counts.

## Validation block rules

- **Boot command** — one shell command. If multi-step (export envs + start), record them on separate lines inside the code fence.
- **Boot outcome** — `OK` only if the process is still up after a 3-second probe; otherwise paste the error excerpt (first 10 lines).
- **Endpoint table** — at least one entry per top-level resource exposed by the original app. The operator picks a representative call per route family (list, item, create, update, delete, plus auth and health when present).
- **Regressions** — any endpoint that returned a different status than the original or that returned 5xx. Phase 3 must not declare complete with regressions outstanding.
- **Residuals** — catalog slugs from Phase 2 that were intentionally not fixed in Phase 3. Each residual entry names the slug and one-sentence justification (e.g. "kept inline whitelist because moving it to constants would balloon scope; deferred to a follow-up").

## Example block (excerpt from the brief)

Anchored to `desafio.md` lines 40-78 for fidelity:

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Apply playbook recipe `split-god-class-into-controllers-by-domain`.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
Impact: Source-tree leak compromete sessões; segredo também é vazado em /health.
Recommendation: Apply playbook recipe `extract-config-to-env-or-settings-module`.
```

## Anti-patterns to avoid when writing reports

- **Vague file references.** `File: throughout` is never acceptable. If a finding spans multiple files, list each separately with its own line range.
- **Severity inflation.** A magic number is LOW, not MEDIUM. A bare `except` is MEDIUM, not HIGH. Use the catalog's `Severity` field as the source of truth.
- **English recommendations.** Recommendations must end with a backtick-quoted playbook slug; the slug is the routing key for Phase 3, not human prose.
- **Duplicate findings.** If the same anti-pattern occurs across 14 sites, the finding has one heading with a multi-line `File:` block listing all 14 paths; do not write 14 separate headings.

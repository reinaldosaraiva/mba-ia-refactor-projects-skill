# P001-S002 — Anti-pattern catalog + refactor playbook

## Zero-context bootstrap

If resuming with no prior conversation:

1. Read `plans/CURRENT.md` to confirm this is the active session.
2. Read `plans/P001-skill-refactor-arch.md` for workstream context.
3. Read `plans/P001-design-contract.md` — focus on **I-1** (agnostic skill), **I-8** (catalog ≥ 8, deprecated-API included), **I-9** (playbook ≥ 8 with before/after).
4. Read `plans/P001-S001-results.md` and `plans/P001-S001-findings.md` — the catalog and playbook seeds at the bottom of the findings file are the input for this session.
5. Then execute the tasks below.

## Goal

Produce the two largest reference files of the `/refactor-arch` skill:

- `code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md` — ≥ 8 anti-patterns, severity-balanced (CRITICAL/HIGH/MEDIUM/LOW), with at least one explicit deprecated-API detection entry. Stack-agnostic: every entry tags which stacks its signals fire on.
- `code-smells-project/.claude/skills/refactor-arch/playbook-refactor.md` — ≥ 8 transformation recipes, each with a fenced `Before` and `After` code block plus validation hint. Each recipe links back to one or more catalog slugs.

These two files are the **knowledge base** the skill consults during Phase 2 (audit) and Phase 3 (refactor). Other reference files (`SKILL.md`, `analise-projeto.md`, `template-relatorio.md`, `guidelines-arquitetura.md`) are S003 work — do not author them here.

Per the brief, the canonical skill home is inside `code-smells-project/.claude/skills/refactor-arch/`; S005 and S006 copy that tree into the other two projects. Author the files there.

## Prerequisite reads (only these)

| Path | Why |
|------|-----|
| `plans/P001-S001-findings.md` | Catalog seeds (#1-#22) and playbook seeds (#1-#16) at end of file are the input |
| `plans/P001-design-contract.md` | Invariants I-1, I-8, I-9 govern this session |
| `desafio.md` lines 132-146 | Mandatory areas of reference files; mandatory deprecated-API detection (line 144); mandatory ≥8 catalog + ≥8 playbook (lines 142, 144) |
| `code-smells-project/{models.py, controllers.py, app.py, database.py}` | Source of CRITICAL-severity example seeds (SQL injection, god-class, hardcoded creds) |
| `ecommerce-api-legacy/src/AppManager.js` | Source of god-class and deprecated `sqlite3.verbose()` example seeds |
| `task-manager-api/routes/{task,user,report}_routes.py` and `services/notification_service.py` | Source of N+1 and missing-auth-middleware example seeds |

Do **not** read or draft `SKILL.md`, `analise-projeto.md`, `template-relatorio.md`, `guidelines-arquitetura.md` — those belong to S003.

## Catalog entry schema

Every entry in `catalog-antipatterns.md` must use the structure below. Skill machinery in S003 will rely on these field names being stable.

```markdown
## <kebab-case-slug>

- **Severity:** CRITICAL | HIGH | MEDIUM | LOW
- **Stacks:** `any` | comma-separated list among {`python-flask`, `nodejs-express`, `python-generic`, `nodejs-generic`}
- **What it is:** 1-2 sentences describing the anti-pattern in plain language.
- **Why it matters:** 1-2 sentences on the failure mode (security, maintainability, perf, testability).
- **Detection signals:** bullet list of grep/regex/structural signals. Each signal labelled with the stack(s) it applies to. At least one signal must be a concrete regex or shell-grep pattern.
- **Example from analysis:** one `file:line` quote from `plans/P001-S001-findings.md` (or directly from a project file). Required.
- **Linked playbook:** comma-separated playbook recipe slug(s) that fix this anti-pattern. Required (forces catalog↔playbook coverage).
```

The file must open with a YAML-fenced header containing the severity tally to allow a downstream lint script to grep it:

```yaml
---
total: <n>
critical: <n>
high: <n>
medium: <n>
low: <n>
deprecated_api_entries: <n>  # must be >= 1
stacks_covered: [python-flask, nodejs-express]
---
```

## Playbook recipe schema

Every recipe in `playbook-refactor.md` must use this structure:

```markdown
## <kebab-case-slug>

- **Fixes catalog entries:** comma-separated catalog slug(s). Required.
- **Applies to:** `any` | `python-flask` | `nodejs-express` | `python-generic` | `nodejs-generic`.
- **When to apply:** one sentence on the trigger.
- **Steps:** numbered list (3-7 steps), specific enough to follow without context.

### Before

\`\`\`<lang>
<minimal but representative original snippet — 5-25 lines>
\`\`\`

### After

\`\`\`<lang>
<minimal refactored snippet showing the target shape — 5-25 lines>
\`\`\`

### Validation hint

How the operator confirms the transformation worked: a grep that should now return nothing, a curl that should now succeed, a test that should now pass, etc.
```

The file must open with a YAML header containing the recipe count and the catalog coverage check:

```yaml
---
total_recipes: <n>
catalog_slugs_covered: [<list-of-catalog-slugs>]
stacks_covered: [python-flask, nodejs-express]
---
```

## Required entries (minimum spread)

Catalog (≥ 8 entries; the suggested list below covers the seed list and the severity distribution requirement — replace at most 2 if you find tighter alternatives in the findings):

1. `god-class-or-god-module` — CRITICAL — stacks `any`
2. `hardcoded-credentials` — CRITICAL — stacks `any`
3. `sql-injection-string-concat` — CRITICAL — stacks `python-flask`, `nodejs-express`, `python-generic`, `nodejs-generic`
4. `business-logic-in-route-or-controller` — HIGH — stacks `any`
5. `n+1-query` — HIGH — stacks `any`
6. `bare-except-or-catch-all` — MEDIUM — stacks `python-flask`, `python-generic` (Node equivalent: empty `catch(e){}`)
7. `duplicate-validation-logic` — MEDIUM — stacks `any`
8. `deprecated-api-call` — MEDIUM — stacks `any` — **MANDATORY per brief line 144**
9. `magic-numbers-or-inline-whitelist` — LOW — stacks `any`
10. `inconsistent-response-envelope` — LOW — stacks `any`

That is 10 entries. Drop two only if absolutely necessary; the brief asks for *at least* 8 with severity distribution, and the distribution here (3 CRITICAL, 2 HIGH, 3 MEDIUM, 2 LOW) is exactly the shape the audit reports should match in S004-S006.

Playbook (≥ 8 recipes covering every catalog slug above):

1. `extract-config-to-env-or-settings-module` — fixes `hardcoded-credentials`
2. `split-god-class-into-controllers-by-domain` — fixes `god-class-or-god-module`
3. `replace-raw-sql-with-parameterised-queries` — fixes `sql-injection-string-concat`
4. `eager-load-relationships-to-fix-n+1` — fixes `n+1-query`
5. `move-business-logic-from-route-to-controller` — fixes `business-logic-in-route-or-controller`, `duplicate-validation-logic`
6. `replace-bare-except-with-typed-handler-and-error-middleware` — fixes `bare-except-or-catch-all`, `inconsistent-response-envelope`
7. `replace-deprecated-api-call-with-current-equivalent` — fixes `deprecated-api-call`
8. `lift-magic-numbers-and-whitelists-into-constants-module` — fixes `magic-numbers-or-inline-whitelist`

Eight recipes covers all ten catalog entries via shared coverage (recipe 5 doubles for duplicate-validation, recipe 6 doubles for envelope). If you go beyond eight, add `replace-fake-or-broken-crypto-with-bcrypt` and `standardise-response-envelope-helper` from the playbook seed list.

## Tasks

1. Create the directory `code-smells-project/.claude/skills/refactor-arch/`.

2. Author `code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md` using the schema above. Open with the YAML severity tally. Use seed list from `plans/P001-S001-findings.md` for example quotes.

3. Author `code-smells-project/.claude/skills/refactor-arch/playbook-refactor.md` using the schema above. Open with the YAML recipe-count header. Every recipe has both Before and After code blocks.

4. Verify counts with this one-liner (acts as the closeout lint; record its output in results):

   ```bash
   {
     echo "=== Catalog ===";
     awk '/^## /{c++} END{print "entries:", c}' code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md;
     grep -c '^- \*\*Severity:\*\* CRITICAL' code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md | awk '{print "critical:", $1}';
     grep -c '^- \*\*Severity:\*\* HIGH' code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md | awk '{print "high:", $1}';
     grep -c '^- \*\*Severity:\*\* MEDIUM' code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md | awk '{print "medium:", $1}';
     grep -c '^- \*\*Severity:\*\* LOW' code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md | awk '{print "low:", $1}';
     grep -c 'deprecated' code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md | awk '{print "deprecated_mentions:", $1}';
     echo "=== Playbook ===";
     awk '/^## /{c++} END{print "recipes:", c}' code-smells-project/.claude/skills/refactor-arch/playbook-refactor.md;
     awk '/^### Before/{b++} /^### After/{a++} END{print "before_blocks:", b, "after_blocks:", a}' code-smells-project/.claude/skills/refactor-arch/playbook-refactor.md;
   }
   ```

   Acceptance: `entries >= 8`, `critical >= 1`, `high >= 1`, `medium >= 1`, `low >= 1`, `deprecated_mentions >= 1`, `recipes >= 8`, `before_blocks == recipes`, `after_blocks == recipes`.

5. Write `plans/P001-S002-results.md` with **Verdict:** GO in the first 5 lines and the lint output pasted in an Evidence block.

6. Update `plans/INDEX.md`: S002 row to `done | GO`, S003 row to `authorable`.

7. Update `plans/CURRENT.md`: point at "S003 authorable, between sessions".

8. Clear `plans/LOCKS.json` if you acquired a lock at start.

9. Scoped git commit covering only the new skill files plus the plan artefacts touched in this session. Record the commit hash in the results file (use the bootstrap-then-follow-up pattern from S001 to avoid the self-reference paradox).

## Definition of done

- `code-smells-project/.claude/skills/refactor-arch/catalog-antipatterns.md` exists, YAML header has tallies matching schema, ≥ 8 entries, ≥ 1 deprecated-API entry, all 4 severities represented.
- `code-smells-project/.claude/skills/refactor-arch/playbook-refactor.md` exists, YAML header present, ≥ 8 recipes, every recipe has Before + After code blocks, every recipe links to ≥ 1 catalog slug, every catalog slug is referenced by ≥ 1 recipe.
- Lint one-liner output saved in `plans/P001-S002-results.md` Evidence section.
- No source files in the 3 projects modified during S002 (the catalog and playbook files live inside `code-smells-project/.claude/skills/refactor-arch/`, which is *skill territory*, not project source — this is allowed and is the canonical home per the brief).
- `INDEX.md`, `CURRENT.md`, `LOCKS.json` updated.
- Two-commit pattern: bootstrap commit + follow-up hash-recording commit, both on `main`, scoped to S002 artefacts only.

## Out of scope (defer)

- `SKILL.md`, `analise-projeto.md`, `template-relatorio.md`, `guidelines-arquitetura.md` — S003.
- Copying the skill into the other two projects — S005, S006.
- Executing the skill — S004+.

## Risks specific to this session

- **Stack-leak.** If a catalog entry's signals only fire for Python (or only for Node), the skill drifts from agnostic. Mitigation: every entry has a `Stacks:` field; if it lists only one stack, the entry must explain why (e.g. SQLAlchemy-specific cascade). Cross-stack signals preferred.
- **Cosmetic playbook.** A recipe whose "After" is just a hand-wave (e.g. `// TODO: use bcrypt`) is useless during Phase-3 execution. Mitigation: every After block must compile/parse in its declared language; reviewer reads each block as if pasting it into the target project.
- **Catalog↔playbook coverage gap.** A catalog slug nobody fixes wastes audit time; a recipe nobody triggers wastes skill memory. Mitigation: explicit cross-link fields, verified by the closeout lint.
- **Premature SKILL.md authoring.** Resist authoring the skill's main prompt here; S003 needs the catalog/playbook to already exist to write the right surface area. Stay disciplined.

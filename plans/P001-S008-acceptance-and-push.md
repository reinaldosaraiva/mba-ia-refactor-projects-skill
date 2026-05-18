# P001-S008 — Final acceptance sweep + public GitHub push + delivery wrap

## Zero-context bootstrap

If resuming with no prior conversation:

1. Read `plans/CURRENT.md`, `plans/INDEX.md`, `plans/P001-skill-refactor-arch.md`, `plans/P001-design-contract.md` — focus on **acceptance criterion 5** ("Repository pushed to a public GitHub fork; URL recorded in `S008-results.md`") and **invariant I-11** (Reentry artefacts override chat memory).
2. Read `desafio.md` lines 172-197 (the 19-item Checklist de Validação the brief mandates per project), lines 415-426 (the 4 OBRIGATÓRIO acceptance criteria across 3/3 projects), and lines 276-283 (the entregável description naming `reports/` and the README explicitly).
3. Read `plans/P001-S004-results.md`, `plans/P001-S005-results.md`, `plans/P001-S006-results.md`, `plans/P001-S007-results.md` — these hold the historical evidence S008 re-verifies. Bootstrap commit hashes: P1 `4abae1f`, P2 `d33fa83`, P3 `79747f5`, README `5911835`.
4. Skim each `reports/audit-project-N.md` Validation block once more.
5. Read `desafio.md` lines 276-283 again to confirm the deliverable contract: `(1) Skill completa em .claude/skills/refactor-arch/ (dentro dos 3 projetos), (2) Código refatorado dos 3 projetos commitado, (3) Relatórios de auditoria em reports/ (3 arquivos), (4) README.md atualizado`.
6. Execute the tasks below.

## Goal

Close the P001 workstream. This is the final session: a re-verification sweep against the three already-refactored projects, a single public-GitHub push of the `main` branch to the user's fork, and the master-plan-level closure record.

Three outcomes (verdict PASS):

1. All 4 acceptance criteria from `desafio.md` lines 415-426 verified ✓ × 3 with **live commands re-run today** (not just citing the older results files). If any single criterion regresses against any project, S008 does not close PASS — the regression is diagnosed and patched in a separate sub-session before resuming the push.
2. The repository is pushed to a public GitHub fork, the URL is recorded in `plans/P001-S008-results.md`, and `gh repo view --json url,visibility,defaultBranchRef` confirms `visibility: PUBLIC` and `defaultBranchRef.name: main`.
3. `plans/INDEX.md`, `plans/CURRENT.md`, and `plans/P001-skill-refactor-arch.md` updated to reflect workstream closure (P001 → `closed`).

## Operating mode

- **Delivery round.** Verdict closes PASS (consistent with S004/S005/S006). Documentation rounds (S001-S003, S007) close GO.
- **No new code in projects, skill, reports.** S008 only adds/edits `plans/P001-S008-*` files and possibly minor `.gitignore` / `README.md` patches if a re-verification surfaces a tiny drift. If the re-verification surfaces anything bigger (a project no longer boots, a test no longer passes), pause and ask the operator before patching — that scenario is a hidden regression that S006 should have caught.
- **Public push is gated.** The push to a public GitHub fork is a one-way, user-visible action. Before invoking `git push` to the public remote, surface to the operator the exact remote + branch + commit count being pushed, confirm `gh auth status` is logged in, and **explicitly ask the operator to confirm** with `y`/`yes` before executing the push. Phase-2 halt discipline carried forward.
- **Secret-leakage final sweep.** Before push, run a workspace-wide grep for the original literal secret strings observed in S001 (`super-secret-key-123`, `minha-chave-super-secreta-123`, `senha_super_secreta_prod_123`, `pk_live_1234567890abcdef`, `senha123`, plain `admin123` outside seed contexts). Expected: zero matches in the refactored project trees. Matches inside `desafio.md`, `plans/P001-S001-findings.md`, `reports/audit-project-*.md`, and the project READMEs are **acceptable** because those are evidence documents describing what was wrong; matches inside the live project source under `code-smells-project/src/`, `ecommerce-api-legacy/src/`, `task-manager-api/src/`, or root-level `app.py`/`app.js`/`seed.py` are NOT acceptable.

## Prerequisite reads (only these)

| Path | Why |
|------|-----|
| `desafio.md` (lines 172-197, 247-254, 276-283, 415-426) | Brief contract: 19-item checklist, deliverables, acceptance criteria |
| `plans/P001-skill-refactor-arch.md` | Workstream goal + session ledger |
| `plans/P001-design-contract.md` | Invariants I-1…I-11, acceptance criterion 5 |
| `plans/P001-S004-results.md` | P1 boot command + smoke table to re-run |
| `plans/P001-S005-results.md` | P2 boot command + smoke table to re-run |
| `plans/P001-S006-results.md` | P3 boot command + smoke table to re-run |
| `plans/P001-S007-results.md` | README grep verifications to re-run |
| `reports/audit-project-1.md`, `audit-project-2.md`, `audit-project-3.md` | Validation blocks per project |
| `README.md` (workspace root) | Source of the final deliverable description |

Do not re-read S001/S002/S003 — they fed earlier sessions and the README already cites them. Do not read the skill files unless a verification mismatches and needs investigation.

## Tasks — acceptance sweep (Phase A)

1. **Snapshot the workspace before any verification.**
   - `git status --short` — expect clean (no uncommitted changes inherited from S007 closeout).
   - `git log --oneline -10` — confirm the top of `main` matches the expected close-S007 commits.
   - Record both in the closeout results file.

2. **Re-verify the skill is bit-identical across the 3 projects.**
   - `diff -rq code-smells-project/.claude/skills/refactor-arch ecommerce-api-legacy/.claude/skills/refactor-arch` → expect empty.
   - `diff -rq code-smells-project/.claude/skills/refactor-arch task-manager-api/.claude/skills/refactor-arch` → expect empty.
   - `diff -rq ecommerce-api-legacy/.claude/skills/refactor-arch task-manager-api/.claude/skills/refactor-arch` → expect empty.
   - If any diff is non-empty, halt — that would mean the skill drifted between projects after S007 closed and the workstream's agnosticism claim is unprovable. Diagnose with `git log -- <path-that-differs>` and patch before continuing.

3. **Re-verify the README grep counts.**
   - `grep -c '^## A)' README.md` → 1, `B)` → 1, `C)` → 1, `D)` → 1.
   - `grep -c '^- \[x\]' README.md` → 57 (or any ≥ 54).
   - `grep -c 'reports/audit-project-' README.md` → ≥ 3 (S007 result was 37).
   - `grep -cE 'plans/P001-S00[456]-results' README.md` → ≥ 3 (S007 result was 15).

4. **Re-boot and re-smoke project 1.**
   - `cd code-smells-project`
   - `python3 -m venv .venv` (fresh — do not reuse S004's venv) and `.venv/bin/pip install -r requirements.txt`.
   - `SECRET_KEY=test-key-do-not-commit DEBUG=false PORT=5050 .venv/bin/python app.py` in background.
   - Smoke a **subset** of the 19 endpoints from `reports/audit-project-1.md` §Validation — pick a representative ≥ 8: `GET /`, `GET /health`, `GET /produtos`, `POST /produtos`, `POST /login` (happy), `POST /login` (SQL injection — must return 401), `GET /pedidos`, `GET /relatorios/vendas`. **At least the SQL-injection-401 check is mandatory** (it is the most security-critical regression to detect).
   - Tear down: `kill <pid>`; delete venv to keep the tree clean.
   - Record outcomes in `plans/P001-S008-results.md` smoke table.

5. **Re-boot and re-smoke project 2.**
   - `cd ../ecommerce-api-legacy`
   - `npm install` fresh (delete `node_modules` first if needed).
   - `DB_PASS=test PAYMENT_GATEWAY_KEY=test-key PORT=3131 node src/app.js` in background.
   - Smoke ≥ 4 of the 5 endpoints from `reports/audit-project-2.md` §Validation. **`POST /api/checkout` with Visa-prefix card → 200 AND `POST /api/checkout` with non-Visa → 400 are both mandatory** (proves the constant-driven payment-decision works).
   - Tear down.

6. **Re-boot and re-smoke project 3.**
   - `cd ../task-manager-api`
   - Fresh `.venv` + `pip install -r requirements.txt`.
   - `SECRET_KEY=test-do-not-commit DEBUG=false PORT=5151 .venv/bin/python seed.py` then `... app.py` in background.
   - Smoke ≥ 12 of the 22 endpoints from `reports/audit-project-3.md` §Validation. **The two envelope checks (`GET /tasks/9999` → 404 with `{status:error, error:{code:not_found,...}}` AND `POST /tasks` with `{"title":"x"}` → 400 with `validation_error` envelope) are mandatory** (proves the error-handler middleware survives a fresh boot).
   - Tear down.

7. **Final secret-leakage sweep.** From workspace root:

   ```bash
   git grep -nE "(super-secret-key-123|minha-chave-super-secreta-123|senha_super_secreta_prod_123|pk_live_1234567890abcdef|senha123|admin123)" \
     -- ':!desafio.md' ':!README.md' ':!plans/' ':!reports/'
   ```

   Expected: zero matches outside the documentation files. If any literal credential persists in live project source after the refactors, S008 does NOT close PASS — patch the leak first.

8. **Layering grep checks** (per `code-smells-project/.claude/skills/refactor-arch/guidelines-arquitetura.md`), one last pass across the 3 projects:

   ```bash
   for proj in code-smells-project ecommerce-api-legacy task-manager-api; do
     echo "== $proj =="
     # Python: src/views must not import models
     grep -rEn 'from src\.models'   "$proj/src/views/"   2>/dev/null && echo "VIOLATION $proj: views -> models" || true
     grep -rEn 'from src\.(controllers|views)' "$proj/src/models/" 2>/dev/null && echo "VIOLATION $proj: models -> upward" || true
     grep -rEn 'from src\.views' "$proj/src/controllers/"   2>/dev/null && echo "VIOLATION $proj: controllers -> views" || true
     grep -rEn 'from src\.(models|controllers)' "$proj/src/middlewares/" 2>/dev/null && echo "VIOLATION $proj: middleware reaches domain" || true
   done
   ```

   (Project 2's Node sources don't use `from src.X` syntax — for it, run the Node variants from `reports/audit-project-2.md` §Layering rule checks. Expected: 4 OK rows × 3 projects = 12 OK, 0 VIOLATIONs.)

9. **Final acceptance-criteria table** with live results — re-fill the `desafio.md` 415-426 table using today's smoke numbers, not the historical ones. Expected: 4 rows × 3 columns all ✓.

## Tasks — public push (Phase B)

10. **Pre-push environment check.**
    - `gh auth status` → must show "Logged in to github.com as <user>". If not logged in, halt and instruct the operator to run `gh auth login`.
    - `git remote -v` → expect either an existing `origin` pointing at a public GitHub fork OR no `origin`. If `origin` already points at a private remote, halt — do NOT overwrite the remote silently.
    - `git status --short` → must be clean.
    - `git log --oneline -1` → confirm the top commit matches what we plan to push.

11. **If no public remote exists, present options to the operator.**
    Surface a 3-way choice and let the operator pick:
    - (a) "Create a new public GitHub repo under my account named `mba-ia-refactor-projects-skill` and push to it" → run `gh repo create <owner>/mba-ia-refactor-projects-skill --public --source=. --remote=origin --push`.
    - (b) "I already have a fork at `<URL>`, push there" → operator pastes URL; agent runs `git remote add origin <URL>` and pushes.
    - (c) "Cancel, don't push" → close S008 with verdict `BLOCKED` and write `plans/P001-S008-results.md` recording the block reason; do not modify INDEX/CURRENT to "closed".

12. **Push preamble — explicit confirmation.**
    Before running any `git push`, surface to the operator:
    - The remote URL the push will land at.
    - The branch (`main`).
    - The commit count being pushed (`git rev-list --count main`).
    - The top 5 commit subjects (`git log --oneline -5`).
    - The fact that the repo will be public after push (anyone with the URL can read the source, the audit reports, and the README).
    Ask: "Confirm push to `<URL>` (public)? [y/n]". Wait for `y`/`yes`. Anything else exits with `Push skipped by operator.` and S008 stays open.

13. **Run the push.**
    - `git push -u origin main` (no `--force` — fast-forward only).
    - If the remote already has commits and refuses, halt — investigate before any history rewrite. Do **not** `--force` without re-asking the operator.
    - On success: capture `gh repo view --json url,visibility,defaultBranchRef`; expect `visibility: PUBLIC` and `defaultBranchRef.name: main`. Record both fields verbatim in the results file.

14. **Post-push verification.**
    - `gh api repos/{owner}/{repo} -q '.html_url, .visibility, .pushed_at'` — record the canonical HTML URL, visibility, and the server-confirmed timestamp.
    - `gh browse --no-browser` to obtain the URL for sharing.
    - Optionally: smoke-fetch `reports/audit-project-1.md` from `raw.githubusercontent.com/<owner>/<repo>/main/reports/audit-project-1.md` to prove the artefact is readable publicly. If the fetch returns 404, the push did not land — diagnose before closing.

## Tasks — closeout (Phase C)

15. **Write `plans/P001-S008-results.md`** with verdict `PASS`, including:
    - The Phase-A snapshot, diff results, grep results, boot+smoke results, secret-leakage sweep, and layering check outcomes.
    - The Phase-B remote URL, visibility, push timestamp, and the public-fetch smoke-test outcome.
    - The 4-row acceptance-criteria table with **live** numbers from today.
    - A "Workstream summary" closing block: 8 sessions, 4 sessions PASS (S004/S005/S006/S008), 4 sessions GO (S001/S002/S003/S007), bootstrap hashes for each project (P1 `4abae1f`, P2 `d33fa83`, P3 `79747f5`, README `5911835`, this session's commit).

16. **Update `plans/INDEX.md`** — S008 → `done | PASS`. Mark P001 master plan as `closed`. Add a footer to INDEX noting the public-fork URL.

17. **Update `plans/CURRENT.md`** — `Active master plan: none (P001 closed)`; `Active session: none`; Status: `workstream complete`. Replace "Last completed sessions" list with the full 8-session summary.

18. **Update `plans/P001-skill-refactor-arch.md`** — add a final section "## Workstream closed" with the close date (`2026-05-18`) and the public fork URL.

19. **Two-commit pattern:**
    - Commit 1: `docs(plans): final acceptance sweep results + workstream closure; close S008 PASS` — staging `plans/P001-S008-acceptance-and-push.md`, `plans/P001-S008-results.md`, `plans/INDEX.md`, `plans/CURRENT.md`, `plans/P001-skill-refactor-arch.md`.
    - Commit 2: `docs(plans): record S008 evidence commit hash in results file` — patches the placeholder in `P001-S008-results.md` with the commit-1 SHA.

20. **Push the closeout commits.** Once Phase B has succeeded and the operator's confirmation is on record for the original push, the two closeout commits ride on the same `origin/main` without a second confirmation gate (they are the workstream-closure documentation, not new code). If the operator wants a second gate for these too, they can interrupt — but the default is: `git push origin main` runs after the two-commit pattern lands.

## Definition of done

- All 4 acceptance-criteria rows from `desafio.md` 415-426 are ✓ × 3 projects with **today's** evidence (not cached from S004-S006).
- The 19-item Checklist de Validação from `desafio.md` 246-272 is **not** re-reproduced in this session's results file — the README §C already carries it × 3 (57 ticked boxes); S008 references the README block instead of re-duplicating it.
- Skill `.claude/skills/refactor-arch/` remains bit-identical across the 3 projects (`diff -rq` empty × 3).
- README grep counts unchanged from S007 (or higher).
- No secret literal survives in live project source (Phase A task 7 grep returns zero matches outside docs).
- Layering grep checks pass across all 3 projects (Phase A task 8).
- `gh repo view --json url,visibility,defaultBranchRef` confirms public + main; URL recorded in `plans/P001-S008-results.md`.
- `gh api repos/<owner>/<repo>` confirms `pushed_at` matches today; public-fetch smoke of one audit report from `raw.githubusercontent.com` returns 200.
- `plans/INDEX.md` shows P001 closed; `plans/CURRENT.md` shows workstream complete; `plans/P001-skill-refactor-arch.md` carries the closure footer.
- Two closeout commits landed; the hash file records commit-1's SHA; final push of those commits to `origin/main` succeeded.

## Out of scope

- Authoring `plans/P002-*` (any follow-up workstream). S008 closes P001; further work opens P002.
- v1.1 catalog/playbook expansion (e.g. adding `global-mutable-state`, `fake-or-broken-crypto`, `missing-orm-cascade`, `pii-or-card-in-logs` slugs). Those are documented in S004-S006 residuals and remain TODO for a future workstream.
- Real JWT in project 3, bcrypt in project 1/2, FK cascade in project 2. All documented residuals.
- Performance benchmarking, load tests, security pen-testing — the smoke contract from invariant I-5 is sufficient for the brief.
- Any private remote, GitHub Pages, releases, or tags. The brief asks for a public fork and a URL; that is the entire deliverable surface.

## Risks specific to this session

- **Re-boot finds a rotted dependency.** Between S004's boot date and today, a transitive dependency may have shipped a breaking version (e.g. SQLAlchemy 2.x or Flask 3.1.x). Mitigation: pin in `requirements.txt` exactly the versions used during S004-S006 if needed; the brief does not require fresh-pip-install reproducibility past commit time, but the smoke must boot from clean `python3 -m venv` for the acceptance to be defensible. If a fresh venv boot fails, surface the failure to the operator before patching.
- **Port collisions.** macOS AirPlay on 5000, Docker on 3030, leftover venv servers on 5050/5151/3131. Mitigation: kill any stray process matching the project name + port before each boot; the smoke tables above already use unique ports per project.
- **Public push reveals a secret missed by S004-S006.** Mitigation: Phase A task 7 sweeps for the 6 known literals before push; **always run that before** task 13. If the sweep finds anything, fix and re-commit before the push.
- **GitHub fork already has a `main` branch with different history.** Mitigation: do not `--force`. If the push is rejected, halt and ask the operator whether to (a) cancel and target a different branch, (b) reset the remote to a clean state explicitly (rare; requires explicit operator authorisation).
- **Operator declines the push.** That's a legitimate outcome — close S008 with `BLOCKED` verdict, leave INDEX at S008 `authorable`, document the block in results. The push can be re-attempted later without re-running Phase A.
- **`gh` CLI not logged in.** Mitigation: Phase B task 10 checks `gh auth status` first; if not logged in, the agent halts before attempting any state change. The operator runs `gh auth login` interactively.
- **Two-commit pattern collision with the operator's confirmation flow.** The closeout commits (task 19) can land *before* Phase B succeeds, but pushing them to public only happens *after* Phase B's confirmed push. If the operator declines the push (task 12 → "no"), the closeout commits stay local and the verdict is `BLOCKED` — re-pushing later just runs `git push` again, no re-commit needed.
- **Long-running boot processes leaking into the chat.** Mitigation: every `python app.py` / `node app.js` / `node src/app.js` invocation uses `run_in_background=true` (or `&` + `kill $!` teardown) so the agent's chat doesn't hang on the daemon.

## Closeout

After all definition-of-done items are checked:

1. `plans/P001-S008-results.md` (verdict `PASS`) — with all phase outcomes, the public URL, the workstream summary block.
2. `plans/INDEX.md` — S008 done | PASS; P001 closed; footer with public URL.
3. `plans/CURRENT.md` — workstream complete; no active session.
4. `plans/P001-skill-refactor-arch.md` — closure footer.
5. `plans/LOCKS.json` stays empty.
6. Two closeout commits landed; the hash file records the commit-1 SHA.
7. Final `git push origin main` for the closeout commits (after Phase B confirmation already on record).
8. The agent's final chat message to the operator is the public URL + a one-line summary: "P001 closed PASS — public fork at <URL>. Skill `/refactor-arch` runs on Python/Flask and Node/Express; 25 findings produced, 46 endpoints verified across 3 projects, 0 regressions."

There is no S009. Further work opens a new master plan (e.g. P002 for catalog v1.1).

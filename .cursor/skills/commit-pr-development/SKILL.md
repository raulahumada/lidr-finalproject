---
name: commit-pr-development
description: >-
  Prepares a Conventional Commits commit on a fresh branch cut from development,
  then opens a pull request targeting development. Use when the user asks to
  commit and PR, prepare a PR to development, ship changes to development, or
  run commit-pr-development.
---

# Commit + PR → development

End-to-end workflow: sync `development` → branch from it → Conventional Commit → push → PR into `development`.

Base and target branch are always **`development`** (not `main`/`master`), unless the user explicitly overrides.

## Preconditions

- Stop if there is nothing to commit (no staged/unstaged/untracked relevant changes).
- Never commit secrets (`.env`, credentials, keys). Warn and exclude them.
- Never update git config, never `--force` to shared branches, never `--no-verify` unless the user asks.
- Do not amend unless the user explicitly asks and amend safety rules in the user rules are met.
- Do not push or open a PR until the commit succeeds.

## Workflow checklist

```
Progress:
- [ ] 1. Inspect changes + recent commit style
- [ ] 2. Sync development and create branch
- [ ] 3. Stage relevant files
- [ ] 4. Commit (Conventional Commits)
- [ ] 5. Push branch
- [ ] 6. Open PR → development
- [ ] 7. Return PR URL
```

### 1. Inspect (run in parallel)

```bash
git status
git diff
git diff --staged
git log development -5 --oneline
git fetch origin development
```

If `development` does not exist locally:

```bash
git fetch origin development:development
```

Analyze the full diff (staged + unstaged + untracked you will include). Draft the commit type/scope/description from the **why**, not a file list.

### 2. Branch from development

Branch name: `<type>/<short-kebab-description>`

Allowed types (same as commit types below): `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

```bash
git checkout development
git pull --ff-only origin development
git checkout -b feat/short-description
```

If the user is already on a feature branch that was cut from `development` and asks only to commit+PR that branch, reuse it — do **not** recreate. Still ensure it is based on up-to-date `development` (rebase/merge only if the user asks; otherwise warn if it diverged badly).

If current work is on another base and moving would lose commits, stop and ask.

### 3. Stage

```bash
git add <relevant paths>
```

Do not `git add .` blindly when secrets or unrelated files are present. Prefer explicit paths.

### 4. Commit — Conventional Commits 1.0.0

Follow project guide **`docs/conventional-commits.md`** (authoritative for this repo) and [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).

**Read `docs/conventional-commits.md` before drafting the message** — especially scope rules for front vs back.

**Structure:**

```
<type>[optional scope][optional !]: <description>

[optional body]

[optional footer(s)]
```

**Scope (required when the diff is app code):**

| Diff under | Scope |
|------------|--------|
| `frontend/**` only | `frontend` |
| `backend/**` only | `backend` |
| both apps | prefer **two commits**; otherwise no app scope / `repo` + body |
| docs / `.cursor` / openspec / root | omit app scope (`docs`/`chore` type) |

**Examples:**

```
feat(backend): add health check endpoint

fix(frontend): correct API base URL for local backend

docs: add conventional commits guide for front and back
```

**Commit command (bash / macOS default):**

```bash
git commit -m "$(cat <<'EOF'
feat(scope): short description

Optional body explaining why.
EOF
)"
```

Windows (PowerShell), only if that shell is what you are using:

```powershell
git commit -m @"
feat(scope): short description

Optional body explaining why.
"@
```

After commit: `git status` to verify clean/success. If a hook fails, fix and create a **new** commit (do not amend unless amend rules allow).

### 5. Push

```bash
git push -u origin HEAD
```

### 6. Pull request → `development`

Use `gh`. Base branch **must** be `development`.

Run in parallel before creating the PR if useful:

```bash
git status
git diff development...HEAD
git log development..HEAD --oneline
```

Title: same as the primary Conventional Commit subject (or the main commit if several).

Body template:

```markdown
## Summary
- <1-3 bullets of what / why>

## Test plan
- [ ] <concrete verification steps>
```

Create:

```bash
gh pr create --base development --title "feat(scope): short description" --body "$(cat <<'EOF'
## Summary
- Bullet one

## Test plan
- [ ] Step one

EOF
)"
```

If `gh` fails auth, stop and report the error; do not open a web PR manually unless asked.

### 7. Finish

Return the PR URL. Do not merge unless the user asks.

## Edge cases

| Situation | Action |
|-----------|--------|
| No changes | Do not commit; say so |
| Only secrets changed | Refuse; warn |
| User asked commit but not PR | Stop after commit (this skill still applies for commit format; skip push/PR) |
| User asked PR but nothing committed | Commit first (with confirmation of message intent from the request), then PR |
| Multiple logical changes mixed | Prefer one focused commit; ask before splitting into multiple commits/PRs |
| `development` missing on remote | Stop and report |

## Anti-patterns

- PR base `main` / `master` by default
- Non-conventional subjects (`Updated stuff`, `WIP`, `fix bugs`)
- Force-push to `development`
- Bundling unrelated files “while at it”
- Skipping `git fetch` / outdated base without noting it

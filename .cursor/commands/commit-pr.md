---
name: /commit-pr
id: commit-pr
category: Workflow
description: Commit with Conventional Commits on a branch from development, then open a PR targeting development
---

Follow the project skill **commit-pr-development** at `.cursor/skills/commit-pr-development/SKILL.md`.

Read that skill and execute its full checklist:

1. Inspect changes
2. Sync `development` and create branch `<type>/<short-kebab>` from it
3. Stage relevant files (no secrets)
4. Commit using `docs/conventional-commits.md` (scopes `frontend` / `backend`) and [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
5. Push
6. `gh pr create --base development`
7. Return the PR URL

Optional argument after `/commit-pr`: short description or preferred branch suffix (e.g. `/commit-pr add health endpoint`).

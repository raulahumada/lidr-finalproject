#!/usr/bin/env bash
# Sync peer reference (cahumada/lidr-master — Knowledge CAG / process-map patterns)
# into .reference/lidr-master (gitignored).
#
# Usage (from repo root, macOS/Linux):
#   bash .cursor/skills/openspec-prespec/scripts/sync-peer-lidr-master.sh
#   bash .cursor/skills/openspec-prespec/scripts/sync-peer-lidr-master.sh main

set -euo pipefail

BRANCH="${1:-main}"
REPO_URL="${2:-https://github.com/cahumada/lidr-master.git}"
TARGET_DIR="${3:-.reference/lidr-master}"

REPO_ROOT="$(pwd)"
TARGET="${REPO_ROOT}/${TARGET_DIR}"

echo "Peer reference sync (lidr-master)"
echo "  repo:   ${REPO_URL}"
echo "  branch: ${BRANCH}"
echo "  target: ${TARGET}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required but was not found on PATH." >&2
  exit 1
fi

if [[ ! -d "${TARGET}/.git" ]]; then
  mkdir -p "$(dirname "${TARGET}")"
  rm -rf "${TARGET}"
  echo "Cloning (depth 1)..."
  git clone --depth 1 --branch "${BRANCH}" --single-branch "${REPO_URL}" "${TARGET}"
else
  echo "Updating existing cache..."
  git -C "${TARGET}" remote set-url origin "${REPO_URL}"
  git -C "${TARGET}" fetch --depth 1 origin "${BRANCH}"
  if ! git -C "${TARGET}" checkout "${BRANCH}" 2>/dev/null; then
    git -C "${TARGET}" checkout -B "${BRANCH}" "origin/${BRANCH}"
  fi
  git -C "${TARGET}" reset --hard "origin/${BRANCH}"
fi

HEAD="$(git -C "${TARGET}" rev-parse --short HEAD)"
echo "OK @ ${HEAD}"
echo "Key paths:"
for p in \
  ai-service/app/generation/rag/process_map/cag.py \
  ai-service/app/generation/rag/answer.py \
  openspec/specs/process-map/spec.md \
  openspec/specs/answer-generation/spec.md
do
  if [[ -f "${TARGET}/${p}" ]]; then
    echo "  - ${p}"
  fi
done

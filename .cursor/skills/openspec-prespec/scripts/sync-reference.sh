#!/usr/bin/env bash
# Sync course ai-engineering reference into .reference/ai-engineering
# Usage (from repo root, macOS/Linux):
#   bash .cursor/skills/openspec-prespec/scripts/sync-reference.sh
#   bash .cursor/skills/openspec-prespec/scripts/sync-reference.sh session_16 ai-service
#
# On Windows, the sibling sync-reference.ps1 is available.

set -euo pipefail

BRANCH="${1:-session_16}"
SPARSE_PATH="${2:-ai-service}"
REPO_URL="${3:-https://github.com/LIDR-academy/ai-engineering.git}"
TARGET_DIR="${4:-.reference/ai-engineering}"

REPO_ROOT="$(pwd)"
TARGET="${REPO_ROOT}/${TARGET_DIR}"

echo "Course reference sync"
echo "  repo:   ${REPO_URL}"
echo "  branch: ${BRANCH}"
echo "  sparse: ${SPARSE_PATH}"
echo "  target: ${TARGET}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required but was not found on PATH." >&2
  exit 1
fi

if [[ ! -d "${TARGET}/.git" ]]; then
  mkdir -p "$(dirname "${TARGET}")"
  rm -rf "${TARGET}"
  echo "Cloning (blobless, sparse)..."
  git clone --filter=blob:none --sparse --branch "${BRANCH}" --single-branch "${REPO_URL}" "${TARGET}"
  git -C "${TARGET}" sparse-checkout set "${SPARSE_PATH}"
else
  echo "Updating existing cache..."
  git -C "${TARGET}" remote set-url origin "${REPO_URL}"
  git -C "${TARGET}" fetch --depth 1 origin "${BRANCH}"
  if ! git -C "${TARGET}" checkout "${BRANCH}" 2>/dev/null; then
    git -C "${TARGET}" checkout -B "${BRANCH}" "origin/${BRANCH}"
  fi
  git -C "${TARGET}" reset --hard "origin/${BRANCH}"
  git -C "${TARGET}" sparse-checkout set "${SPARSE_PATH}"
fi

HEAD="$(git -C "${TARGET}" rev-parse --short HEAD)"
SPARSE_ROOT="${TARGET}/${SPARSE_PATH}"
echo "OK @ ${HEAD}"
if [[ -d "${SPARSE_ROOT}" ]]; then
  echo "Sparse tree ready: ${SPARSE_ROOT}"
  ls "${SPARSE_ROOT}" | head -20 | while IFS= read -r name; do
    echo "  - ${name}"
  done
else
  echo "Warning: Sparse path not found after sync: ${SPARSE_ROOT}" >&2
fi

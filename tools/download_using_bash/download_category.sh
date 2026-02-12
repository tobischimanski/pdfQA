#!/usr/bin/env bash
set -euo pipefail

# Download a single top-level category folder via git sparse-checkout + git-lfs.
#
# Categories:
#   - syn-pdfQA
#   - real-pdfQA
#
# Usage:
#   ./download_category.sh syn-pdfQA
#   ./download_category.sh real-pdfQA
#
# Optional env overrides:
#   REPO_ID=pdfqa/pdfQA-Benchmark BRANCH=main DEST_ROOT=downloads ./download_category.sh syn-pdfQA

REPO_ID="${REPO_ID:-pdfqa/pdfQA-Benchmark}"
BRANCH="${BRANCH:-main}"
DEST_ROOT="${DEST_ROOT:-.}"

CATEGORY="${1:-}"
if [[ -z "${CATEGORY}" ]]; then
  echo "Error: missing category argument."
  echo "Usage: $0 syn-pdfQA|real-pdfQA"
  exit 1
fi

if [[ "${CATEGORY}" != "syn-pdfQA" && "${CATEGORY}" != "real-pdfQA" ]]; then
  echo "Error: invalid category '${CATEGORY}'. Must be 'syn-pdfQA' or 'real-pdfQA'."
  exit 1
fi

REPO_URL="https://huggingface.co/datasets/${REPO_ID}"
DEST_DIR="${DEST_ROOT%/}/pdfQA_${CATEGORY}"

echo "==> Repo:     ${REPO_ID}"
echo "==> Branch:   ${BRANCH}"
echo "==> Category: ${CATEGORY}"
echo "==> Dest:     ${DEST_DIR}"
echo

# Resumable by default. Set CLEAN=1 to delete.
if [[ -d "${DEST_DIR}" ]]; then
  if [[ "${CLEAN:-0}" == "1" ]]; then
    echo "==> CLEAN=1 → removing existing '${DEST_DIR}'"
    rm -rf "${DEST_DIR}"
  else
    echo "==> '${DEST_DIR}' already exists; resuming inside it. (Set CLEAN=1 to delete.)"
  fi
fi

mkdir -p "${DEST_DIR}"
cd "${DEST_DIR}"

# Initialize repo if first time
if [[ ! -d ".git" ]]; then
  git init -q
  git remote add origin "${REPO_URL}"
else
  # Ensure remote exists (users sometimes copy dirs around)
  git remote set-url origin "${REPO_URL}" >/dev/null 2>&1 || true
fi

# Sparse checkout setup (cone mode is fine since CATEGORY is a single folder)
git sparse-checkout init --cone >/dev/null 2>&1 || true
git sparse-checkout set "${CATEGORY}"

# Fetch and checkout target branch
git fetch --depth=1 origin "${BRANCH}"
git checkout -q -B "${BRANCH}" "origin/${BRANCH}"

# LFS pull (only pulls LFS objects referenced by checked-out files)
git lfs install --local >/dev/null 2>&1 || true
git lfs pull

echo
echo "✅ Done. Downloaded to: ${DEST_DIR}/${CATEGORY}/"

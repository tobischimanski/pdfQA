#!/usr/bin/env bash
set -euo pipefail

# Download a single dataset folder across all 3 "type" trees:
#   01.1_Input_Files_Non_PDF/<dataset>/
#   01.2_Input_Files_PDF/<dataset>/
#   01.3_Input_Files_CSV/<dataset>/
#
# Usage:
#   ./download_dataset_all_types.sh syn-pdfQA "financial reports"
#   ./download_dataset_all_types.sh real-pdfQA ClimateFinanceBench
#
# Optional env overrides:
#   REPO_ID=pdfqa/pdfQA-Benchmark BRANCH=main DEST_ROOT=downloads CLEAN=1 ./download_dataset_all_types.sh syn-pdfQA books

REPO_ID="${REPO_ID:-pdfqa/pdfQA-Benchmark}"
BRANCH="${BRANCH:-main}"
DEST_ROOT="${DEST_ROOT:-.}"

CATEGORY="${1:-}"
DATASET="${2:-}"

if [[ -z "${CATEGORY}" || -z "${DATASET}" ]]; then
  echo "Usage: $0 syn-pdfQA|real-pdfQA <dataset_name>"
  exit 1
fi

if [[ "${CATEGORY}" != "syn-pdfQA" && "${CATEGORY}" != "real-pdfQA" ]]; then
  echo "Error: invalid category '${CATEGORY}'. Must be 'syn-pdfQA' or 'real-pdfQA'."
  exit 1
fi

REPO_URL="https://huggingface.co/datasets/${REPO_ID}"
DEST_DIR="${DEST_ROOT%/}/pdfQA_${CATEGORY}__${DATASET}"

echo "==> Repo:     ${REPO_ID}"
echo "==> Branch:   ${BRANCH}"
echo "==> Category: ${CATEGORY}"
echo "==> Dataset:  ${DATASET}"
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

# Initialize repo if needed
if [[ ! -d ".git" ]]; then
  git init -q
  git remote add origin "${REPO_URL}"
else
  git remote set-url origin "${REPO_URL}" >/dev/null 2>&1 || true
fi

# IMPORTANT:
# - --cone is great for simple top-level dirs
# - but here we list multiple deep paths → use NON-cone patterns.
git sparse-checkout init --no-cone >/dev/null 2>&1 || true

# Set sparse paths (quote everything; dataset name may contain spaces)
git sparse-checkout set \
  "${CATEGORY}/01.1_Input_Files_Non_PDF/${DATASET}" \
  "${CATEGORY}/01.2_Input_Files_PDF/${DATASET}" \
  "${CATEGORY}/01.3_Input_Files_CSV/${DATASET}"

# Fetch and checkout the remote branch
git fetch --depth=1 origin "${BRANCH}"
git checkout -q -B "${BRANCH}" "origin/${BRANCH}"

# Pull LFS objects referenced by the checked-out files
git lfs install --local >/dev/null 2>&1 || true
git lfs pull

echo
echo "✅ Done. Downloaded to: ${DEST_DIR}/"

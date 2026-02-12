#!/usr/bin/env bash
set -euo pipefail

# Download the entire dataset repo via git + git-lfs.
# Pros: resumable, preserves repo structure, efficient for large binary files.
# Cons: requires git + git-lfs installed.

REPO_ID="pdfqa/pdfQA-Benchmark"
BRANCH="main"
DEST_DIR="pdfQA_all"

# You can override defaults like:
#   REPO_ID=pdfqa/pdfQA-Benchmark DEST_DIR=mydir ./download_all.sh

REPO_URL="https://huggingface.co/datasets/${REPO_ID}"

echo "==> Repo:   ${REPO_ID}"
echo "==> Branch: ${BRANCH}"
echo "==> Dest:   ${DEST_DIR}"
echo

# If the directory exists, we DO NOT delete it by default.
# To force a clean download: set CLEAN=1
if [[ -d "${DEST_DIR}" ]]; then
  if [[ "${CLEAN:-0}" == "1" ]]; then
    echo "==> CLEAN=1 → removing existing '${DEST_DIR}'"
    rm -rf "${DEST_DIR}"
  else
    echo "==> '${DEST_DIR}' already exists."
    echo "    Resuming inside it. (Set CLEAN=1 to delete and re-clone.)"
  fi
fi

# Clone if needed; otherwise just fetch/pull updates.
if [[ ! -d "${DEST_DIR}/.git" ]]; then
  echo "==> Cloning (this may take time for large repos)..."
  git clone --depth=1 --branch "${BRANCH}" "${REPO_URL}" "${DEST_DIR}"
else
  echo "==> Existing git repo detected → fetching latest..."
  (cd "${DEST_DIR}" && git fetch --depth=1 origin "${BRANCH}" && git checkout "${BRANCH}" && git pull --ff-only)
fi

cd "${DEST_DIR}"

# Ensure git-lfs is initialized in this repo, then pull LFS objects.
# The install command is safe to run repeatedly.
echo "==> Initializing git-lfs (local)..."
git lfs install --local >/dev/null 2>&1 || true

echo "==> Pulling LFS objects..."
git lfs pull

echo
echo "✅ Done. Downloaded to: ${DEST_DIR}/"

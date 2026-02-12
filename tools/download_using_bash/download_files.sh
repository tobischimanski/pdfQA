#!/usr/bin/env bash
set -euo pipefail

# Download specific files from a HF dataset repo using git sparse-checkout + git-lfs.
#
# Examples:
#   ./download_files.sh "syn-pdfQA/01.2_Input_Files_PDF/books/file1.pdf"
#   ./download_files.sh \
#     "syn-pdfQA/01.2_Input_Files_PDF/financial reports/2020__CATC__2020-03-16_10-K_catc-10k_20191231.pdf" \
#     "syn-pdfQA/01.3_Input_Files_CSV/financial reports/2020__CATC__2020-03-16_10-K_catc-10k_20191231.csv"
#
# From a file (one path per line; blank lines and #comments allowed):
#   ./download_files.sh --file files.txt
#
# Optional env overrides:
#   REPO_ID=pdfqa/pdfQA-Benchmark BRANCH=main DEST_DIR=downloads_files CLEAN=1 ./download_files.sh ...

REPO_ID="${REPO_ID:-pdfqa/pdfQA-Benchmark}"
BRANCH="${BRANCH:-main}"
DEST_DIR="${DEST_DIR:-pdfQA_files_subset}"
REPO_URL="https://huggingface.co/datasets/${REPO_ID}"

print_help() {
  cat <<'EOF'
Usage:
  download_files.sh [--file files.txt] <file1> [file2 ...]
  download_files.sh -h|--help

Arguments:
  fileN   Repo-relative file paths to include
          (e.g., syn-pdfQA/01.2_Input_Files_PDF/books/file1.pdf)

Options:
  --file PATH   Read file paths from file (one per line; supports spaces; ignores blank lines and lines starting with #)
  CLEAN=1       Delete DEST_DIR before downloading (default is resumable)

Environment:
  REPO_ID   (default: pdfqa/pdfQA-Benchmark)
  BRANCH    (default: main)
  DEST_DIR  (default: pdfQA_files_subset)
EOF
}

FILES=()
FILE_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) print_help; exit 0 ;;
    --file)
      FILE_ARG="${2:-}"
      [[ -z "${FILE_ARG}" ]] && { echo "Error: --file requires a path" >&2; exit 1; }
      shift 2
      ;;
    *)
      FILES+=("$1")
      shift
      ;;
  esac
done

if [[ -n "${FILE_ARG}" ]]; then
  [[ ! -f "${FILE_ARG}" ]] && { echo "Error: file not found: ${FILE_ARG}" >&2; exit 1; }
  while IFS= read -r line; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "${line}" ]] && continue
    [[ "${line}" == \#* ]] && continue
    FILES+=("${line}")
  done < "${FILE_ARG}"
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
  echo "Error: no file paths provided. Use --help." >&2
  exit 1
fi

echo "==> Repo:   ${REPO_ID}"
echo "==> Branch: ${BRANCH}"
echo "==> Dest:   ${DEST_DIR}"
echo "==> Files:"
for f in "${FILES[@]}"; do
  echo "    - ${f}"
done
echo

# Resumable by default; CLEAN=1 to remove.
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

# Init repo if needed
if [[ ! -d ".git" ]]; then
  git init -q
  git remote add origin "${REPO_URL}"
else
  git remote set-url origin "${REPO_URL}" >/dev/null 2>&1 || true
fi

# Non-cone required for arbitrary deep paths (including files)
git sparse-checkout init --no-cone >/dev/null 2>&1 || true

# Apply sparse file paths
git sparse-checkout set "${FILES[@]}"

# Fetch + checkout
git fetch --depth=1 origin "${BRANCH}"
git checkout -q -B "${BRANCH}" "origin/${BRANCH}"

# Pull LFS objects referenced by selected files
git lfs install --local >/dev/null 2>&1 || true
git lfs pull

echo
echo "✅ Done. Downloaded to: ${DEST_DIR}/"

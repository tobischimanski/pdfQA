#!/usr/bin/env bash
set -euo pipefail

# Download an arbitrary folder or list of folders using git sparse-checkout + git-lfs.
#
# Examples:
#   ./download_folders.sh "syn-pdfQA/01.2_Input_Files_PDF/books"
#   ./download_folders.sh \
#     "syn-pdfQA/01.2_Input_Files_PDF/financial reports" \
#     "syn-pdfQA/01.3_Input_Files_CSV/financial reports"
#
# From a file (one path per line; blank lines and #comments allowed):
#   ./download_folders.sh --file paths.txt
#
# Optional env overrides:
#   REPO_ID=pdfqa/pdfQA-Benchmark BRANCH=main DEST_DIR=downloads_subset CLEAN=1 ./download_folders.sh ...

REPO_ID="${REPO_ID:-pdfqa/pdfQA-Benchmark}"
BRANCH="${BRANCH:-main}"
DEST_DIR="${DEST_DIR:-pdfQA_subset}"
REPO_URL="https://huggingface.co/datasets/${REPO_ID}"

print_help() {
  cat <<'EOF'
Usage:
  download_folders.sh [--file paths.txt] <path1> [path2 ...]
  download_folders.sh -h|--help

Arguments:
  pathN   Repo-relative folder paths to include (e.g., syn-pdfQA/01.2_Input_Files_PDF/books)

Options:
  --file PATH   Read folder paths from file (one per line; supports spaces; ignores blank lines and lines starting with #)
  CLEAN=1       Delete DEST_DIR before downloading (default is resumable)

Environment:
  REPO_ID   (default: pdfqa/pdfQA-Benchmark)
  BRANCH    (default: main)
  DEST_DIR  (default: pdfQA_subset)

Examples:
  ./download_folders.sh "syn-pdfQA/01.2_Input_Files_PDF/books"

  ./download_folders.sh \
    "syn-pdfQA/01.2_Input_Files_PDF/financial reports" \
    "syn-pdfQA/01.3_Input_Files_CSV/financial reports"

  ./download_folders.sh --file paths.txt
EOF
}

PATHS=()
FILE_ARG=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      print_help
      exit 0
      ;;
    --file)
      FILE_ARG="${2:-}"
      if [[ -z "${FILE_ARG}" ]]; then
        echo "Error: --file requires a path" >&2
        exit 1
      fi
      shift 2
      ;;
    --) shift; break ;;
    *)
      PATHS+=("$1")
      shift
      ;;
  esac
done

# Load from file if provided
if [[ -n "${FILE_ARG}" ]]; then
  if [[ ! -f "${FILE_ARG}" ]]; then
    echo "Error: file not found: ${FILE_ARG}" >&2
    exit 1
  fi
  while IFS= read -r line; do
    # trim leading/trailing whitespace
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    # skip blanks/comments
    [[ -z "${line}" ]] && continue
    [[ "${line}" == \#* ]] && continue
    PATHS+=("${line}")
  done < "${FILE_ARG}"
fi

if [[ ${#PATHS[@]} -eq 0 ]]; then
  echo "Error: no folder paths provided." >&2
  echo "Run with --help for usage." >&2
  exit 1
fi

echo "==> Repo:    ${REPO_ID}"
echo "==> Branch:  ${BRANCH}"
echo "==> Dest:    ${DEST_DIR}"
echo "==> Paths:"
for p in "${PATHS[@]}"; do
  echo "    - ${p}"
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

# Init git repo if needed
if [[ ! -d ".git" ]]; then
  git init -q
  git remote add origin "${REPO_URL}"
else
  git remote set-url origin "${REPO_URL}" >/dev/null 2>&1 || true
fi

# Non-cone required for arbitrary deep folder lists
git sparse-checkout init --no-cone >/dev/null 2>&1 || true

# Apply sparse paths (each array item preserved even if it contains spaces)
git sparse-checkout set "${PATHS[@]}"

# Fetch + checkout branch
git fetch --depth=1 origin "${BRANCH}"
git checkout -q -B "${BRANCH}" "origin/${BRANCH}"

# Pull LFS objects for selected files
git lfs install --local >/dev/null 2>&1 || true
git lfs pull

echo
echo "✅ Done. Downloaded to: ${DEST_DIR}/"

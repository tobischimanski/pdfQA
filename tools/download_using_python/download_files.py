from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List

from huggingface_hub import snapshot_download


def _read_list_file(path_file: str) -> List[str]:
    p = Path(path_file)
    if not p.exists():
        raise FileNotFoundError(f"list file not found: {path_file}")

    out: List[str] = []
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line.lstrip("/"))  # repo-relative
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Download specific files from a HF dataset repo.")
    ap.add_argument(
        "--repo-id",
        default=os.environ.get("REPO_ID", "pdfqa/pdfQA-Benchmark"),
        help="HF dataset repo id (default: pdfqa/pdfQA-Benchmark).",
    )
    ap.add_argument(
        "--local-dir",
        default=os.environ.get("LOCAL_DIR", "downloads_files"),
        help="Where to write files (default: downloads_files).",
    )
    ap.add_argument(
        "--files-list",
        help="Text file containing repo-relative file paths (one per line). Lines starting with # are ignored.",
    )
    ap.add_argument(
        "files",
        nargs="*",
        help="Repo-relative file paths (e.g., syn-pdfQA/01.2_Input_Files_PDF/books/file1.pdf).",
    )
    args = ap.parse_args()

    files: List[str] = []
    if args.files_list:
        files.extend(_read_list_file(args.files_list))
    files.extend([f.lstrip("/") for f in args.files])

    if not files:
        raise SystemExit("Error: no files provided. Use --files-list or pass file paths as arguments.")

    # Deduplicate while preserving order
    seen = set()
    allow_patterns: List[str] = []
    for f in files:
        if f not in seen:
            seen.add(f)
            allow_patterns.append(f)

    print(f"==> Repo:      {args.repo_id}")
    print(f"==> Local dir: {args.local_dir}")
    print("==> Files:")
    for f in allow_patterns:
        print(f"    - {f}")
    print("==> Downloading...")

    snapshot_download(
        repo_id=args.repo_id,
        repo_type="dataset",
        local_dir=args.local_dir,
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=allow_patterns,
    )

    print(f"\n✅ Done: {args.local_dir}/")


if __name__ == "__main__":
    main()

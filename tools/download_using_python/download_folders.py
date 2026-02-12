from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import List

from huggingface_hub import snapshot_download


def _read_paths_file(path_file: str) -> List[str]:
    p = Path(path_file)
    if not p.exists():
        raise FileNotFoundError(f"paths file not found: {path_file}")

    out: List[str] = []
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def _normalize_to_allow_patterns(repo_paths: List[str]) -> List[str]:
    """
    Convert repo-relative folder/file paths into allow_patterns for snapshot_download.

    Behavior:
      - If user gives a folder path (most common), we append '/**'
      - If user gives a file path, allow as-is (but users can still pass folder/** explicitly)
    """
    allow: List[str] = []
    for rp in repo_paths:
        rp = rp.strip().lstrip("/")  # ensure repo-relative
        if not rp:
            continue

        # If user already gave a glob, keep it.
        if any(ch in rp for ch in ["*", "?", "["]):
            allow.append(rp)
            continue

        # If it "looks like a directory" (no extension) -> treat as folder
        # (Users can still pass "path/to/file.pdf" explicitly.)
        if Path(rp).suffix == "":
            allow.append(f"{rp}/**")
        else:
            allow.append(rp)

    # Deduplicate while preserving order
    seen = set()
    uniq: List[str] = []
    for a in allow:
        if a not in seen:
            seen.add(a)
            uniq.append(a)
    return uniq


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Download arbitrary folders (or lists of folders) from a Hugging Face dataset repo."
    )
    ap.add_argument(
        "--repo-id",
        default=os.environ.get("REPO_ID", "pdfqa/pdfQA-Benchmark"),
        help="HF dataset repo id (default: pdfqa/pdfQA-Benchmark). You can also set REPO_ID env var.",
    )
    ap.add_argument(
        "--local-dir",
        default=os.environ.get("LOCAL_DIR", "downloads_subset"),
        help="Where to write files (default: downloads_subset). You can also set LOCAL_DIR env var.",
    )
    ap.add_argument(
        "--paths-file",
        help="Text file with repo-relative paths, one per line. Lines starting with # are ignored.",
    )
    ap.add_argument(
        "paths",
        nargs="*",
        help='Repo-relative folder/file paths. Example: syn-pdfQA/01.2_Input_Files_PDF/books',
    )
    args = ap.parse_args()

    repo_paths: List[str] = []

    if args.paths_file:
        repo_paths.extend(_read_paths_file(args.paths_file))

    repo_paths.extend(args.paths)

    if not repo_paths:
        raise SystemExit("Error: no paths provided. Use --paths-file or pass paths as positional arguments.")

    allow_patterns = _normalize_to_allow_patterns(repo_paths)

    print(f"==> Repo:      {args.repo_id}")
    print(f"==> Local dir: {args.local_dir}")
    print("==> Allow patterns:")
    for p in allow_patterns:
        print(f"    - {p}")
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

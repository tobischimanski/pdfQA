from __future__ import annotations

import argparse
import os
from huggingface_hub import snapshot_download


def main() -> None:
    """
    Download one top-level category folder using snapshot_download + allow_patterns.

    Usage:
      python download_category.py --category syn-pdfQA
      python download_category.py --category real-pdfQA

    Optional env overrides:
      REPO_ID=pdfqa/pdfQA-Benchmark LOCAL_ROOT=downloads python download_category.py --category syn-pdfQA
    """
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--category",
        required=True,
        choices=["syn-pdfQA", "real-pdfQA"],
        help="Top-level category folder to download.",
    )
    args = ap.parse_args()

    repo_id = os.environ.get("REPO_ID", "pdfqa/pdfQA-Benchmark")
    local_root = os.environ.get("LOCAL_ROOT", ".")
    local_dir = os.path.join(local_root, f"pdfQA_{args.category}")

    print(f"==> Repo:      {repo_id}")
    print(f"==> Category:  {args.category}")
    print(f"==> Local dir: {local_dir}")
    print("==> Downloading snapshot subset...")

    snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        local_dir=local_dir,
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=[
            f"{args.category}/**",  # everything under that category
        ],
    )

    print(f"\n✅ Done: {local_dir}/")


if __name__ == "__main__":
    main()

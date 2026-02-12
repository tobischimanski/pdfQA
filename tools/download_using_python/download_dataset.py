from __future__ import annotations

import argparse
import os
from huggingface_hub import snapshot_download


def main() -> None:
    """
    Download one dataset (across all input types) using allow_patterns.

    Examples:
      python download_dataset_all_types.py --category syn-pdfQA --dataset "financial reports"
      python download_dataset_all_types.py --category real-pdfQA --dataset ClimateFinanceBench

    Optional env overrides:
      REPO_ID=pdfqa/pdfQA-Benchmark LOCAL_ROOT=downloads python download_dataset_all_types.py --category syn-pdfQA --dataset books
    """
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, choices=["syn-pdfQA", "real-pdfQA"])
    ap.add_argument("--dataset", required=True, help="Dataset folder name (can include spaces).")
    args = ap.parse_args()

    repo_id = os.environ.get("REPO_ID", "pdfqa/pdfQA-Benchmark")
    local_root = os.environ.get("LOCAL_ROOT", ".")
    local_dir = os.path.join(local_root, f"downloads_{args.category}__{args.dataset}")

    allow = [
        f"{args.category}/01.1_Input_Files_Non_PDF/{args.dataset}/**",
        f"{args.category}/01.2_Input_Files_PDF/{args.dataset}/**",
        f"{args.category}/01.3_Input_Files_CSV/{args.dataset}/**",
    ]

    print(f"==> Repo:      {repo_id}")
    print(f"==> Category:  {args.category}")
    print(f"==> Dataset:   {args.dataset}")
    print(f"==> Local dir: {local_dir}")
    print("==> Downloading subset...")

    snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        local_dir=local_dir,
        local_dir_use_symlinks=False,
        resume_download=True,
        allow_patterns=allow,
    )

    print(f"\n✅ Done: {local_dir}/")


if __name__ == "__main__":
    main()

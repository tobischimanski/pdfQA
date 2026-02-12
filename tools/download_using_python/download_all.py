from __future__ import annotations

import os
from huggingface_hub import snapshot_download


def main() -> None:
    """
    Download the entire dataset repository via huggingface_hub.snapshot_download.

    Pros:
      - No git needed
      - Resumable
      - Can ignore patterns, cache-aware

    Cons:
      - Still downloads large binaries (as stored on the Hub)
      - Needs `huggingface_hub` installed and (optionally) HF token for private/limited scenarios

    Install:
      pip install -U huggingface_hub
    """

    repo_id = os.environ.get("REPO_ID", "pdfqa/pdfQA-Benchmark")
    local_dir = os.environ.get("LOCAL_DIR", "downloads_all")

    print(f"==> Repo:      {repo_id}")
    print(f"==> Local dir: {local_dir}")
    print("==> Downloading snapshot...")

    snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        local_dir=local_dir,
        # Keep downloads resumable/efficient:
        local_dir_use_symlinks=False,  # safer across filesystems; uses real files
        resume_download=True,
    )

    print(f"\n✅ Done: {local_dir}/")


if __name__ == "__main__":
    main()

"""
AgriLens Production Helper: Qwen 2.5 3B GGUF Model Downloader & Health Check.
Downloads qwen2.5-3b-instruct-q4_k_m.gguf from HuggingFace directly to data/models/.
"""
import os
import sys
import time
import argparse
from pathlib import Path
import urllib.request

MODEL_FILENAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
DEFAULT_HF_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
)
EXPECTED_MIN_BYTES = 1_900_000_000  # ~1.9 GB minimum


def find_existing_model(target_dir: Path) -> Path | None:
    """Checks common locations for the Qwen model file."""
    candidates = [
        target_dir / MODEL_FILENAME,
        Path("/app/data/models") / MODEL_FILENAME,
        Path("/app/models") / MODEL_FILENAME,
        Path(r"C:\Users\ndoli\Documents\WEBAPP\IHKIP\models") / MODEL_FILENAME,
    ]
    for c in candidates:
        if c.is_file() and c.stat().st_size >= EXPECTED_MIN_BYTES:
            return c
    return None


def download_model(url: str, dest_path: Path, force: bool = False) -> bool:
    """Downloads model with streaming progress updates."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.is_file() and not force:
        size = dest_path.stat().st_size
        if size >= EXPECTED_MIN_BYTES:
            print(f"[OK] Model already present: {dest_path} ({size / (1024*1024):.1f} MB)")
            return True
        else:
            print(f"[WARN] Incomplete model file detected ({size} bytes). Re-downloading...")

    part_path = dest_path.with_suffix(".part")
    print(f"==> Initiating download of Qwen 2.5 3B GGUF model...")
    print(f"    Source URL:  {url}")
    print(f"    Destination: {dest_path}")

    start_time = time.time()
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "AgriLens-Production-Deployment/1.0"}
        )
        with urllib.request.urlopen(req) as resp, open(part_path, "wb") as f_out:
            total_size = resp.headers.get("Content-Length")
            total_bytes = int(total_size) if total_size else 0
            downloaded = 0
            block_size = 1024 * 1024  # 1MB chunks
            last_print = 0

            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                f_out.write(chunk)
                downloaded += len(chunk)
                now = time.time()
                if now - last_print > 3:  # Print every 3s
                    pct = (downloaded / total_bytes * 100) if total_bytes else 0
                    mb = downloaded / (1024 * 1024)
                    total_mb = total_bytes / (1024 * 1024)
                    speed = mb / max(1, now - start_time)
                    print(f"    Progress: {pct:5.1f}% [{mb:,.0f}MB / {total_mb:,.0f}MB] @ {speed:.2f} MB/s")
                    last_print = now

        # Atomic rename once completed
        if part_path.exists():
            if dest_path.exists():
                dest_path.unlink()
            part_path.rename(dest_path)

        elapsed = time.time() - start_time
        final_size_mb = dest_path.stat().st_size / (1024 * 1024)
        print(f"[SUCCESS] Download completed in {elapsed:.1f}s: {dest_path} ({final_size_mb:,.1f} MB)")
        return True

    except Exception as exc:
        print(f"[ERROR] Failed to download Qwen model: {exc}", file=sys.stderr)
        if part_path.exists():
            part_path.unlink()
        return False


def main():
    parser = argparse.ArgumentParser(description="AgriLens Qwen Model Downloader")
    parser.add_argument("--dest-dir", type=str, default="data/models", help="Target models directory")
    parser.add_argument("--url", type=str, default=DEFAULT_HF_URL, help="HuggingFace model download URL")
    parser.add_argument("--check-only", action="store_true", help="Only check if model exists")
    parser.add_argument("--force", action="store_true", help="Force re-download even if file exists")
    args = parser.parse_args()

    target_dir = Path(args.dest_dir).resolve()
    existing = find_existing_model(target_dir)

    if existing and not args.force:
        print(f"[OK] Qwen 2.5 3B model is verified and ready at: {existing}")
        sys.exit(0)

    if args.check_only:
        print(f"[MISSING] Qwen 2.5 3B model not found in standard directories.")
        sys.exit(1)

    dest_file = target_dir / MODEL_FILENAME
    ok = download_model(args.url, dest_file, force=args.force)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

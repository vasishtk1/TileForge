"""Download the color image of every texture in the manifest.

Run with:
    uv run python -m tileforge.data.download            # everything
    uv run python -m tileforge.data.download --limit 5  # quick trial
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import time
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image
from remotezip import RemoteZip

USER_AGENT = "TileForge (https://github.com/vasishtk1/TileForge)"
SHRINK_FACTOR = 2  # 1024x1024 source -> 512x512 on disk
JPEG_QUALITY = 95

Fetch = Callable[[str], Image.Image]


def pick_color_file(names: list[str]) -> str | None:
    """Find the color image among the files in a texture zip."""
    for name in names:
        if name.endswith(("_Color.jpg", "_Color.png")):
            return name
    return None


def fetch_color_image(url: str) -> Image.Image:
    """Download only the color image from a remote zip, without downloading the whole zip."""
    with RemoteZip(url, headers={"User-Agent": USER_AGENT}, timeout=60) as archive:
        name = pick_color_file(archive.namelist())
        if name is None:
            raise FileNotFoundError(f"no color image in {url}")
        data = archive.read(name)
    return Image.open(io.BytesIO(data)).convert("RGB")


def shrink(image: Image.Image, factor: int = SHRINK_FACTOR) -> Image.Image:
    """Shrink by averaging each factor x factor block of pixels into one.

    Block averaging never mixes pixels across the image border, so a seamless texture stays
    seamless. Smoother resizing filters blur across the border and would not guarantee that.
    """
    return image.reduce(factor)


def save_atomic(image: Image.Image, path: Path) -> None:
    """Write to a temporary name, then rename. The final name only ever holds a complete file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    image.save(partial, format="JPEG", quality=JPEG_QUALITY)
    os.replace(partial, path)


def texture_path(row: dict[str, str], out_dir: Path) -> Path:
    return out_dir / row["label"] / f"{row['asset_id']}.jpg"


def download_one(
    row: dict[str, str],
    out_dir: Path,
    fetch: Fetch = fetch_color_image,
    attempts: int = 3,
    backoff_seconds: float = 2.0,
) -> str:
    """Download one texture. Returns "skipped", "downloaded" or "failed"."""
    path = texture_path(row, out_dir)
    if path.exists():
        return "skipped"
    for attempt in range(attempts):
        try:
            save_atomic(shrink(fetch(row["url"])), path)
            return "downloaded"
        except Exception as error:  # noqa: BLE001 - any failure should be retried, then reported
            if attempt == attempts - 1:
                print(f"FAILED {row['asset_id']}: {error}")
            else:
                time.sleep(backoff_seconds * (attempt + 1))
    return "failed"


def download_all(
    rows: list[dict[str, str]],
    out_dir: Path,
    workers: int = 4,
    fetch: Fetch = fetch_color_image,
) -> Counter[str]:
    """Download every row, a few at a time. Safe to re-run: finished textures are skipped."""
    results: Counter[str] = Counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        statuses = pool.map(lambda row: download_one(row, out_dir, fetch), rows)
        for done, status in enumerate(statuses, start=1):
            results[status] += 1
            if done % 50 == 0 or done == len(rows):
                print(f"{done}/{len(rows)} {dict(results)}", flush=True)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("manifests/ambientcg.csv"))
    parser.add_argument("--out", type=Path, default=Path("data/textures"))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--limit", type=int, default=None, help="only the first N textures")
    args = parser.parse_args()

    with args.manifest.open(newline="") as f:
        rows = list(csv.DictReader(f))[: args.limit]
    results = download_all(rows, args.out, workers=args.workers)
    if results["failed"]:
        raise SystemExit(f"{results['failed']} textures failed; re-run to retry them.")


if __name__ == "__main__":
    main()

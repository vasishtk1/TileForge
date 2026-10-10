"""Build the manifest: the list of ambientCG textures TileForge uses and their class labels.

Run with:
    uv run python -m tileforge.data.catalog
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

import requests
import yaml

API_URL = "https://ambientcg.com/api/v2/full_json"
PAGE_SIZE = 500
MANIFEST_FIELDS = ["asset_id", "label", "category", "url", "zip_bytes"]


def fetch_catalog() -> list[dict[str, Any]]:
    """Download the description of every ambientCG material (metadata only, no images)."""
    assets: list[dict[str, Any]] = []
    while True:
        response = requests.get(
            API_URL,
            params={
                "type": "Material",
                "include": "tagData,downloadData,displayData",
                "limit": PAGE_SIZE,
                "offset": len(assets),
            },
            timeout=60,
        )
        response.raise_for_status()
        page = response.json()["foundAssets"]
        assets.extend(page)
        if len(page) < PAGE_SIZE:
            return assets


def assign_label(asset: dict[str, Any], classes: dict[str, dict[str, Any]]) -> str | None:
    """Return the class label for one asset, or None if no class wants it. First match wins."""
    category = asset.get("displayCategory")
    tags = {tag.lower() for tag in asset.get("tags", [])}
    for label, rule in classes.items():
        if category in rule.get("categories", []):
            return label
        extra = rule.get("also_tagged")
        if extra and category == extra["in_category"] and extra["tag"].lower() in tags:
            return label
    return None


def find_download(asset: dict[str, Any], attribute: str) -> dict[str, Any] | None:
    """Return the download entry (link + size) for the requested resolution, if it exists."""
    try:
        downloads = asset["downloadFolders"]["default"]["downloadFiletypeCategories"]["zip"][
            "downloads"
        ]
    except (KeyError, TypeError):
        return None
    for download in downloads:
        if download.get("attribute") == attribute:
            return download
    return None


def build_manifest(assets: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep the assets that belong to a class and have a download; one manifest row each."""
    rows = []
    for asset in assets:
        label = assign_label(asset, config["classes"])
        download = find_download(asset, config["download_attribute"])
        if label is None or download is None:
            continue
        rows.append(
            {
                "asset_id": asset["assetId"],
                "label": label,
                "category": asset["displayCategory"],
                "url": download["downloadLink"],
                "zip_bytes": download["size"],
            }
        )
    # Sort so the manifest is identical no matter what order the API returns assets in.
    return sorted(rows, key=lambda row: row["asset_id"])


def write_manifest(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/classes.yaml"))
    parser.add_argument("--out", type=Path, default=Path("manifests/ambientcg.csv"))
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text())
    assets = fetch_catalog()
    rows = build_manifest(assets, config)
    write_manifest(rows, args.out)

    counts = Counter(row["label"] for row in rows)
    print(f"{len(assets)} materials in catalogue, {len(rows)} kept -> {args.out}")
    for label in config["classes"]:
        print(f"  {label:15s} {counts[label]:4d}")


if __name__ == "__main__":
    main()

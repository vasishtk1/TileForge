from tileforge.data.catalog import assign_label, build_manifest, find_download

CLASSES = {
    "grass": {"categories": ["Grass"], "also_tagged": {"tag": "grass", "in_category": "Ground"}},
    "ground": {"categories": ["Ground"]},
    "rock": {"categories": ["Rock", "Rocks"]},
}
CONFIG = {"download_attribute": "1K-JPG", "classes": CLASSES}


def make_asset(asset_id, category, tags=(), attributes=("1K-JPG",)):
    downloads = [
        {"attribute": a, "downloadLink": f"https://example.com/{asset_id}_{a}.zip", "size": 10}
        for a in attributes
    ]
    return {
        "assetId": asset_id,
        "displayCategory": category,
        "tags": list(tags),
        "downloadFolders": {
            "default": {"downloadFiletypeCategories": {"zip": {"downloads": downloads}}}
        },
    }


def test_label_from_category():
    assert assign_label(make_asset("Rocks001", "Rocks"), CLASSES) == "rock"


def test_grass_tag_claims_ground_texture():
    assert assign_label(make_asset("Ground037", "Ground", tags=["Grass"]), CLASSES) == "grass"
    assert assign_label(make_asset("Ground001", "Ground", tags=["dirt"]), CLASSES) == "ground"


def test_grass_tag_outside_ground_is_ignored():
    assert assign_label(make_asset("Snow015", "Snow", tags=["grass"]), CLASSES) is None


def test_find_download_picks_requested_resolution():
    asset = make_asset("Rock001", "Rock", attributes=("2K-JPG", "1K-JPG"))
    assert find_download(asset, "1K-JPG")["downloadLink"].endswith("Rock001_1K-JPG.zip")
    assert find_download(asset, "8K-JPG") is None


def test_find_download_handles_missing_downloads():
    assert find_download({"assetId": "X", "downloadFolders": {"default": []}}, "1K-JPG") is None


def test_manifest_skips_unwanted_and_is_sorted():
    assets = [
        make_asset("Rock002", "Rock"),
        make_asset("Sign001", "Sign"),
        make_asset("Ground001", "Ground", attributes=("2K-JPG",)),
        make_asset("Grass001", "Grass"),
    ]
    rows = build_manifest(assets, CONFIG)
    assert [row["asset_id"] for row in rows] == ["Grass001", "Rock002"]
    assert rows[0]["label"] == "grass"

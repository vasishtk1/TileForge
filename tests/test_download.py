from PIL import Image

from tileforge.data.download import download_all, download_one, pick_color_file, shrink

ROW = {"asset_id": "Rock001", "label": "rock", "url": "https://example.com/Rock001.zip"}


def fake_fetch(url):
    return Image.new("RGB", (64, 64), color=(10, 200, 30))


def failing_fetch(url):
    raise ConnectionError("network down")


def test_pick_color_file():
    names = ["Rock001_1K-JPG_NormalGL.jpg", "Rock001_1K-JPG_Color.jpg", "Rock001.png"]
    assert pick_color_file(names) == "Rock001_1K-JPG_Color.jpg"
    assert pick_color_file(["Rock001_1K-JPG_Roughness.jpg"]) is None


def test_shrink_halves_size_by_block_averaging():
    image = Image.new("RGB", (4, 2))
    image.putdata([(0, 0, 0), (100, 100, 100)] * 4)
    small = shrink(image, factor=2)
    assert small.size == (2, 1)
    assert small.getpixel((0, 0)) == (50, 50, 50)


def test_download_saves_shrunk_image(tmp_path):
    assert download_one(ROW, tmp_path, fetch=fake_fetch) == "downloaded"
    saved = Image.open(tmp_path / "rock" / "Rock001.jpg")
    assert saved.size == (32, 32)


def test_existing_file_is_skipped(tmp_path):
    download_one(ROW, tmp_path, fetch=fake_fetch)
    assert download_one(ROW, tmp_path, fetch=failing_fetch) == "skipped"


def test_failure_leaves_no_file_behind(tmp_path):
    status = download_one(ROW, tmp_path, fetch=failing_fetch, backoff_seconds=0)
    assert status == "failed"
    assert list(tmp_path.rglob("*.*")) == []


def test_download_all_counts_results(tmp_path):
    rows = [ROW, {**ROW, "asset_id": "Rock002"}]
    assert download_all(rows, tmp_path, fetch=fake_fetch)["downloaded"] == 2
    assert download_all(rows, tmp_path, fetch=fake_fetch)["skipped"] == 2

from unittest.mock import patch, MagicMock
from pathlib import Path

from grimmealie.bulk import list_screenshots, parse_selection, bulk_upload


def test_list_screenshots_empty_dir(tmp_path):
    result = list_screenshots(tmp_path)
    assert result == []


def test_list_screenshots_with_png_files(tmp_path):
    (tmp_path / "shot1.png").write_bytes(b"fake png 1")
    (tmp_path / "shot2.png").write_bytes(b"fake png 2")
    (tmp_path / "notes.txt").write_text("not an image")

    result = list_screenshots(tmp_path)
    assert len(result) == 2
    assert all(p.suffix == ".png" for p in result)
    assert result[0].name == "shot1.png"
    assert result[1].name == "shot2.png"


def test_list_screenshots_sorted(tmp_path):
    (tmp_path / "c.png").write_bytes(b"c")
    (tmp_path / "a.png").write_bytes(b"a")
    (tmp_path / "b.png").write_bytes(b"b")

    result = list_screenshots(tmp_path)
    assert [p.name for p in result] == ["a.png", "b.png", "c.png"]


def test_list_screenshots_nonexistent_dir():
    result = list_screenshots(Path("/nonexistent/path/12345"))
    assert result == []


def test_parse_selection_all():
    screenshots = [Path("a.png"), Path("b.png"), Path("c.png")]
    result = parse_selection("all", screenshots)
    assert result == screenshots


def test_parse_selection_all_case_insensitive():
    screenshots = [Path("a.png"), Path("b.png")]
    assert parse_selection("ALL", screenshots) == screenshots
    assert parse_selection("All", screenshots) == screenshots


def test_parse_selection_single_index():
    screenshots = [Path("a.png"), Path("b.png"), Path("c.png")]
    result = parse_selection("2", screenshots)
    assert result == [Path("b.png")]


def test_parse_selection_multiple_indices():
    screenshots = [Path("a.png"), Path("b.png"), Path("c.png"), Path("d.png")]
    result = parse_selection("1,3", screenshots)
    assert result == [Path("a.png"), Path("c.png")]


def test_parse_selection_range():
    screenshots = [Path("a.png"), Path("b.png"), Path("c.png"), Path("d.png")]
    result = parse_selection("2-4", screenshots)
    assert result == [Path("b.png"), Path("c.png"), Path("d.png")]


def test_parse_selection_mixed():
    screenshots = [
        Path("a.png"),
        Path("b.png"),
        Path("c.png"),
        Path("d.png"),
        Path("e.png"),
    ]
    result = parse_selection("1,3-4", screenshots)
    assert result == [Path("a.png"), Path("c.png"), Path("d.png")]


def test_parse_selection_out_of_bounds():
    screenshots = [Path("a.png"), Path("b.png")]
    result = parse_selection("5", screenshots)
    assert result == []


def test_parse_selection_empty_result():
    screenshots = [Path("a.png"), Path("b.png")]
    result = parse_selection("", screenshots)
    assert result == []


def test_parse_selection_preserves_order():
    screenshots = [Path("a.png"), Path("b.png"), Path("c.png")]
    result = parse_selection("3,1", screenshots)
    assert result == [Path("a.png"), Path("c.png")]


@patch("grimmealie.bulk.MealieClient")
def test_bulk_upload_success(mock_client_class, tmp_path):
    img1 = tmp_path / "test1.png"
    img2 = tmp_path / "test2.png"
    img1.write_bytes(b"fake png 1")
    img2.write_bytes(b"fake png 2")

    mock_client = MagicMock()
    mock_client.create_recipe_from_images.return_value = "test-recipe"
    mock_client_class.return_value = mock_client

    cfg = MagicMock()
    cfg.mealie_url = "https://mealie.example.com"
    cfg.mealie_key = "test-key"

    selected = [img1, img2]
    result = bulk_upload(cfg, selected, delete_after=False)

    assert result is True
    mock_client.create_recipe_from_images.assert_called_once()
    assert img1.exists()
    assert img2.exists()


@patch("grimmealie.bulk.MealieClient")
def test_bulk_upload_deletes_after_success(mock_client_class, tmp_path):
    img = tmp_path / "test.png"
    img.write_bytes(b"fake png")

    mock_client = MagicMock()
    mock_client.create_recipe_from_images.return_value = "test-recipe"
    mock_client_class.return_value = mock_client

    cfg = MagicMock()
    cfg.mealie_url = "https://mealie.example.com"
    cfg.mealie_key = "test-key"

    selected = [img]
    result = bulk_upload(cfg, selected, delete_after=True)

    assert result is True
    assert not img.exists()


@patch("grimmealie.bulk.MealieClient")
def test_bulk_upload_failure(mock_client_class, tmp_path):
    img = tmp_path / "test.png"
    img.write_bytes(b"fake png")

    mock_client = MagicMock()
    mock_client.create_recipe_from_images.side_effect = Exception("API error")
    mock_client_class.return_value = mock_client

    cfg = MagicMock()
    cfg.mealie_url = "https://mealie.example.com"
    cfg.mealie_key = "test-key"

    selected = [img]
    result = bulk_upload(cfg, selected, delete_after=True)

    assert result is False
    assert img.exists()


def test_bulk_upload_empty_selection():
    cfg = MagicMock()
    result = bulk_upload(cfg, [], delete_after=True)
    assert result is False

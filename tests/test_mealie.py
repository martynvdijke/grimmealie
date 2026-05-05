from unittest.mock import patch, MagicMock
from pathlib import Path
from grimmealie.mealie import MealieClient


def test_client_init():
    c = MealieClient("https://m.example.com/", "key-123")
    assert c.base_url == "https://m.example.com"
    assert c.api_key == "key-123"


def test_client_headers():
    c = MealieClient("https://m.example.com", "key-123")
    assert c._headers == {"Authorization": "Bearer key-123"}


@patch("grimmealie.mealie.httpx.Client")
def test_create_recipe_from_images(mock_client_class):
    mock_resp = MagicMock()
    mock_resp.json.return_value = "my-recipe-slug"
    mock_resp.raise_for_status.return_value = None

    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_ctx
    mock_ctx.post.return_value = mock_resp
    mock_client_class.return_value = mock_ctx

    c = MealieClient("https://m.example.com", "key-123")
    paths = [Path("/tmp/test.png")]
    Path("/tmp/test.png").write_bytes(b"fake png data")

    slug = c.create_recipe_from_images(paths)  # type: ignore

    assert slug == "my-recipe-slug"
    mock_ctx.post.assert_called_once()
    args, kwargs = mock_ctx.post.call_args
    assert args[0] == "https://m.example.com/api/recipes/create/image"
    assert kwargs["headers"] == {"Authorization": "Bearer key-123"}
    assert "images" in str(kwargs["files"])

    Path("/tmp/test.png").unlink(missing_ok=True)


@patch("grimmealie.mealie.httpx.Client")
def test_create_recipe_from_images_with_translate(mock_client_class):
    mock_resp = MagicMock()
    mock_resp.text = "slug"
    mock_resp.raise_for_status.return_value = None
    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_ctx
    mock_ctx.post.return_value = mock_resp
    mock_client_class.return_value = mock_ctx

    c = MealieClient("https://m.example.com", "key-123")
    p = Path("/tmp/test_trans.png")
    p.write_bytes(b"data")
    c.create_recipe_from_images([p], translate_language="nl")
    assert mock_ctx.post.call_args[1]["params"] == {"translateLanguage": "nl"}
    p.unlink(missing_ok=True)


@patch("grimmealie.mealie.httpx.Client")
def test_create_recipe_from_images_async(mock_client_class):
    mock_resp = MagicMock()
    mock_resp.json.return_value = "slug"
    mock_resp.raise_for_status.return_value = None
    mock_ctx = MagicMock()
    mock_ctx.__enter__.return_value = mock_ctx
    mock_ctx.post.return_value = mock_resp
    mock_client_class.return_value = mock_ctx

    c = MealieClient("https://m.example.com", "key-123")
    p = Path("/tmp/test_async.png")
    p.write_bytes(b"data")
    slug = c.create_recipe_from_images_async([p])
    assert slug == "slug"
    p.unlink(missing_ok=True)

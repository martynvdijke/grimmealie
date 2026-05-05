from pathlib import Path
import httpx


class MealieClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def create_recipe_from_images(
        self,
        image_paths: list[str | Path],
        translate_language: str | None = None,
    ) -> str:
        params = {}
        if translate_language:
            params["translateLanguage"] = translate_language

        files = []
        for path in image_paths:
            p = Path(path)
            files.append(("images", (p.name, p.read_bytes(), "image/png")))

        with httpx.Client() as client:
            resp = client.post(
                f"{self.base_url}/api/recipes/create/image",
                headers=self._headers,
                files=files,
                params=params,
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json()

    def create_recipe_from_images_async(
        self,
        image_paths: list[str | Path],
        translate_language: str | None = None,
    ) -> str:
        return self.create_recipe_from_images(image_paths, translate_language)

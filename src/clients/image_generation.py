import logging
from typing import Protocol

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

_IMAGE_MODEL = "imagen-4.0-fast-generate-001"


class ImageGenerationClient(Protocol):
    def generate(self, prompt: str) -> bytes | None: ...


class ImagenGenerationClient:
    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> bytes | None:
        try:
            response = self._client.models.generate_images(
                model=_IMAGE_MODEL,
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="16:9"),
            )
            return response.generated_images[0].image.image_bytes
        except Exception:
            logger.exception("Error generating image via Imagen API")
            return None

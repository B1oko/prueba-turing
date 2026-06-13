import logging
from typing import Protocol

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class ImageGenerationClient(Protocol):
    def generate(self, prompt: str) -> bytes | None: ...


class ImagenGenerationClient:
    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> bytes | None:
        logger.info("Sending image generation request to Imagen for prompt: '%s'", prompt)
        try:
            response = self._client.models.generate_images(
                model="imagen-3.0-fast-generate-001",
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1, aspect_ratio="4:3"),
            )
            image_bytes = response.generated_images[0].image.image_bytes
            logger.info("Successfully generated image. Got %d bytes.", len(image_bytes))
            return image_bytes
        except Exception as e:
            logger.exception("Error generating image via Imagen API for prompt '%s'", prompt)
            return None

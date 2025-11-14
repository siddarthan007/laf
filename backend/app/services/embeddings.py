from __future__ import annotations

import asyncio
import io
from dataclasses import dataclass
from typing import Optional

from PIL import Image
from sentence_transformers import SentenceTransformer

from app.config.settings import get_settings


@dataclass(slots=True)
class EmbeddingBundle:
    description_vector: list[float]
    description_clip_vector: list[float]
    image_vector: Optional[list[float]]


class EmbeddingService:
    """Wrapper around transformer models for generating text and image embeddings."""

    def __init__(self) -> None:
        settings = get_settings()
        self._text_model_name = settings.text_embedding_model_name
        self._clip_model_name = settings.clip_model_name
        self._device = settings.embeddings_device
        self._batch_size = settings.embeddings_batch_size
        self._text_model: Optional[SentenceTransformer] = None
        self._clip_model: Optional[SentenceTransformer] = None

    async def load(self) -> None:
        """Load transformer models into memory."""

        await asyncio.to_thread(self._load_models)

    def _load_models(self) -> None:
        self._text_model = SentenceTransformer(self._text_model_name, device=self._device)
        self._clip_model = SentenceTransformer(self._clip_model_name, device=self._device)

    async def encode_query(self, query: str) -> list[float]:
        """
        Generate MiniLM text embedding for a search query.
        
        This is optimized for search queries and matches the description_vector
        stored in items, enabling semantic similarity search.
        
        Args:
            query: Search query string
            
        Returns:
            List of floats representing the query embedding vector
        """
        if not self._text_model:
            raise RuntimeError("Text embedding model is not loaded")
        
        embedding = await asyncio.to_thread(
            self._text_model.encode,
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embedding.tolist()

    async def encode_description(self, description: str) -> tuple[list[float], list[float]]:
        """Generate both MiniLM and CLIP text embeddings for a description."""

        if not self._text_model or not self._clip_model:
            raise RuntimeError("Embedding models are not loaded")

        text_embedding, clip_embedding = await asyncio.gather(
            asyncio.to_thread(
                self._text_model.encode,
                description,
                normalize_embeddings=True,
                convert_to_numpy=True,
            ),
            asyncio.to_thread(
                self._clip_model.encode,
                description,
                normalize_embeddings=True,
                convert_to_numpy=True,
            ),
        )
        return text_embedding.tolist(), clip_embedding.tolist()

    async def encode_image(self, image_bytes: bytes | None) -> Optional[list[float]]:
        """Generate a CLIP image embedding if bytes are provided."""

        if not image_bytes:
            return None
        if not self._clip_model:
            raise RuntimeError("CLIP model is not loaded")

        pil_image = await asyncio.to_thread(self._bytes_to_image, image_bytes)
        embedding = await asyncio.to_thread(
            self._clip_model.encode,
            pil_image,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embedding.tolist()

    @staticmethod
    def _bytes_to_image(image_bytes: bytes) -> Image.Image:
        with Image.open(io.BytesIO(image_bytes)) as image:
            return image.convert("RGB")

    async def generate_bundle(self, *, description: str, image_bytes: bytes | None) -> EmbeddingBundle:
        """Produce a complete embedding bundle for a reported item."""

        description_vector, clip_text_vector = await self.encode_description(description)
        image_vector = await self.encode_image(image_bytes)
        return EmbeddingBundle(
            description_vector=description_vector,
            description_clip_vector=clip_text_vector,
            image_vector=image_vector,
        )


embedding_service = EmbeddingService()


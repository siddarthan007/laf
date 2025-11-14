"""
Lightweight fuzzy search and vector similarity search service.

This module provides fast, efficient search capabilities combining:
- Fuzzy string matching (using rapidfuzz for performance)
- Vector space similarity (using pre-computed embeddings)
- Hybrid scoring for optimal results

Optimized for:
- Database-level performance via selective filtering
- Efficient fuzzy matching with WRatio and preprocessing
- Vectorized numpy operations for batch processing
- Early termination and result limiting
"""

from __future__ import annotations

import logging
from statistics import mean
from typing import Any

import numpy as np
from rapidfuzz import fuzz, utils
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Item, Match, MatchStatus

logger = logging.getLogger(__name__)


def _cosine_similarity_fast(
    vector_a: list[float] | np.ndarray | None,
    vector_b: list[float] | np.ndarray | None,
) -> float:
    """
    Fast cosine similarity calculation using numpy (optimized for performance).

    Uses float32 for memory efficiency and vectorized operations.
    Returns -1.0 if vectors are invalid or empty.
    """
    if vector_a is None or vector_b is None:
        return -1.0

    def _to_array(vector: list[float] | np.ndarray) -> np.ndarray | None:
        if isinstance(vector, np.ndarray):
            if vector.size == 0:
                return None
            return vector.astype(np.float32) if vector.dtype != np.float32 else vector
        if len(vector) == 0:
            return None
        return np.array(vector, dtype=np.float32)

    np_a = _to_array(vector_a)
    np_b = _to_array(vector_b)

    if np_a is None or np_b is None:
        return -1.0

    norm_a = np.linalg.norm(np_a)
    norm_b = np.linalg.norm(np_b)

    if norm_a == 0.0 or norm_b == 0.0:
        return -1.0

    return float(np.dot(np_a, np_b) / (norm_a * norm_b))


def _fuzzy_score(query: str, text: str) -> float:
    """
    Calculate fuzzy matching score using rapidfuzz WRatio.

    Uses WRatio which automatically selects the best matching strategy,
    and preprocessing for better accuracy. Returns normalized score between 0.0 and 1.0.
    """
    if not query or not text:
        return 0.0

    score = fuzz.WRatio(
        query,
        text,
        score_cutoff=0,
        processor=utils.default_process,  # Normalizes strings for better matching
    )
    return score / 100.0


def _build_item_filters(
    *,
    status_filter: str | None,
    include_archived: bool,
) -> list[Any]:
    filters: list[Any] = []
    if not include_archived:
        filters.append(Item.is_active.is_(True))
    if status_filter:
        filters.append(Item.status == status_filter)
    return filters


async def search_items_fuzzy(
    session: AsyncSession,
    query: str,
    *,
    status_filter: str | None = None,
    include_archived: bool = False,
    limit: int = 50,
    min_score: float = 0.3,
) -> list[tuple[Item, float]]:
    """
    Fast fuzzy search for items using rapidfuzz WRatio.

    Searches in description and location fields with optimized fuzzy matching.
    Uses preprocessing and early termination for better performance.
    Returns items sorted by relevance score (descending).
    """
    if not query or len(query.strip()) < 2:
        return []

    query = query.strip()
    logger.info("Fuzzy search for query: '%s'", query)

    query_lower = query.lower()

    filters = _build_item_filters(status_filter=status_filter, include_archived=include_archived)
    statement = select(Item).order_by(Item.reported_at.desc())
    if filters:
        statement = statement.where(and_(*filters))

    candidates = list((await session.execute(statement)).scalars().all())
    if not candidates:
        return []

    scored_items: list[tuple[Item, float]] = []

    for item in candidates:
        desc_score = _fuzzy_score(query, item.description)
        loc_score = _fuzzy_score(query, item.location)
        fuzzy_score = max(desc_score, loc_score)

        desc_lower = item.description.lower()
        loc_lower = item.location.lower()
        if query_lower in desc_lower or query_lower in loc_lower:
            fuzzy_score = max(fuzzy_score, 0.90)

        if fuzzy_score >= min_score:
            scored_items.append((item, fuzzy_score))

    scored_items.sort(key=lambda x: x[1], reverse=True)
    return scored_items[:limit]


async def search_items_vector(
    session: AsyncSession,
    query_vector: list[float],
    *,
    status_filter: str | None = None,
    include_archived: bool = False,
    limit: int = 50,
    min_score: float = 0.3,
) -> list[tuple[Item, float]]:
    """
    Optimized vector similarity search using vectorized numpy operations.

    Uses batch processing with numpy for efficient cosine similarity calculation.
    """
    if not query_vector or len(query_vector) == 0:
        return []

    logger.info("Vector search with vector dimension: %s", len(query_vector))

    query_vec = np.array(query_vector, dtype=np.float32)
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0.0:
        return []
    query_vec_normalized = query_vec / query_norm

    filters = _build_item_filters(status_filter=status_filter, include_archived=include_archived)
    filters.append(Item.description_vector.isnot(None))

    statement = select(Item).order_by(Item.reported_at.desc())
    if filters:
        statement = statement.where(and_(*filters))

    candidates = list((await session.execute(statement)).scalars().all())
    if not candidates:
        return []

    scored_items: list[tuple[Item, float]] = []
    batch_size = 100

    for i in range(0, len(candidates), batch_size):
        batch = candidates[i : i + batch_size]
        batch_vectors: list[list[float]] = []
        batch_items: list[Item] = []

        for item in batch:
            if item.description_vector is not None and len(item.description_vector) > 0:
                batch_vectors.append(item.description_vector)
                batch_items.append(item)

        if not batch_vectors:
            continue

        vectors_array = np.array(batch_vectors, dtype=np.float32)
        norms = np.linalg.norm(vectors_array, axis=1)
        valid_mask = norms > 0.0
        if not np.any(valid_mask):
            continue

        vectors_normalized = vectors_array[valid_mask] / norms[valid_mask][:, np.newaxis]
        similarities = np.dot(vectors_normalized, query_vec_normalized)

        valid_indices = np.nonzero(valid_mask)[0]
        for local_idx, similarity in enumerate(similarities):
            if similarity >= min_score:
                original_idx = valid_indices[local_idx]
                scored_items.append((batch_items[original_idx], float(similarity)))

    scored_items.sort(key=lambda x: x[1], reverse=True)
    return scored_items[:limit]


async def search_items_hybrid(
    session: AsyncSession,
    query: str,
    query_vector: list[float] | None = None,
    *,
    status_filter: str | None = None,
    include_archived: bool = False,
    limit: int = 50,
    fuzzy_weight: float = 0.4,
    vector_weight: float = 0.6,
    min_score: float = 0.3,
) -> list[tuple[Item, float]]:
    """
    Hybrid search combining fuzzy matching and vector similarity.

    Combines fuzzy string matching with semantic vector search for optimal results.
    """
    if not query or len(query.strip()) < 2:
        return []

    query = query.strip()
    logger.info("Hybrid search for query: '%s'", query)

    fuzzy_results = await search_items_fuzzy(
        session,
        query,
        status_filter=status_filter,
        include_archived=include_archived,
        limit=limit * 3,
        min_score=0.15,
    )

    vector_results: list[tuple[Item, float]] = []
    if query_vector:
        vector_results = await search_items_vector(
            session,
            query_vector,
            status_filter=status_filter,
            include_archived=include_archived,
            limit=limit * 3,
            min_score=0.15,
        )

    if not query_vector:
        return fuzzy_results[:limit]

    item_scores: dict[str, tuple[Item, float, float]] = {}

    for item, score in fuzzy_results:
        item_scores[str(item.id)] = (item, score, 0.0)

    for item, score in vector_results:
        item_id = str(item.id)
        if item_id in item_scores:
            existing_item, fuzzy_score, _ = item_scores[item_id]
            item_scores[item_id] = (existing_item, fuzzy_score, score)
        else:
            item_scores[item_id] = (item, 0.0, score)

    combined_results: list[tuple[Item, float]] = []
    for item, fuzzy_score, vector_score in item_scores.values():
        combined_score = (fuzzy_score * fuzzy_weight) + (vector_score * vector_weight)
        if combined_score >= min_score:
            combined_results.append((item, combined_score))

    combined_results.sort(key=lambda x: x[1], reverse=True)
    return combined_results[:limit]


async def search_items_admin(
    session: AsyncSession,
    query: str,
    query_vector: list[float] | None = None,
    *,
    status_filter: str | None = None,
    include_archived: bool = True,
    include_matches: bool = True,
    limit: int = 50,
    fuzzy_weight: float = 0.4,
    vector_weight: float = 0.6,
    min_score: float = 0.3,
) -> list[tuple[Item, float]]:
    """
    Admin-focused search that includes archived items and matched pairs.
    """
    base_results = await search_items_hybrid(
        session,
        query=query,
        query_vector=query_vector,
        status_filter=status_filter,
        include_archived=include_archived,
        limit=limit * 2,  # fetch extra for post-processing
        fuzzy_weight=fuzzy_weight,
        vector_weight=vector_weight,
        min_score=min_score,
    )

    if not include_matches or not base_results:
        return base_results[:limit]

    item_ids = [item.id for item, _ in base_results]
    if not item_ids:
        return base_results[:limit]

    statement = select(Match).where(
        Match.match_status == MatchStatus.APPROVED,
        or_(Match.lost_item_id.in_(item_ids), Match.found_item_id.in_(item_ids)),
    )
    matches = list((await session.execute(statement)).scalars().all())
    if not matches:
        return base_results[:limit]

    average_score = mean(score for _, score in base_results) if base_results else min_score
    paired_score = max(min_score, average_score * 0.85)

    combined: dict[str, tuple[Item, float]] = {
        str(item.id): (item, score) for item, score in base_results
    }

    for match in matches:
        await session.refresh(match, attribute_names=["lost_item", "found_item"])

        for related_item in (match.lost_item, match.found_item):
            if related_item is None:
                continue
            key = str(related_item.id)
            if key not in combined:
                combined[key] = (related_item, paired_score)

    combined_results = sorted(combined.values(), key=lambda x: x[1], reverse=True)
    return combined_results[:limit]


from __future__ import annotations

import logging
import re
from datetime import timedelta
from math import isclose

import numpy as np
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.models import Item, ItemStatus, Match, MatchStatus, User, UserRole
from app.utils.location_proximity import apply_location_boost

settings = get_settings()
logger = logging.getLogger(__name__)


def _extract_keywords(text: str) -> set[str]:
    """Extract common object keywords from text."""
    if not text:
        return set()
    
    # Common lost items
    keywords = {
        "phone", "mobile", "smartphone", "iphone", "android",
        "laptop", "macbook", "computer",
        "wallet", "purse", "bag", "backpack", "handbag",
        "keys", "keychain",
        "id", "card", "license", "passport",
        "bottle", "water bottle", "thermos",
        "umbrella",
        "glasses", "sunglasses", "spectacles",
        "watch", "smartwatch",
        "headphones", "earphones", "airpods", "buds",
        "charger", "cable", "power bank",
        "notebook", "book", "textbook",
        "calculator",
    }
    
    found = set()
    text_lower = text.lower()
    for word in keywords:
        if word in text_lower:
            found.add(word)
    return found


def _extract_colors(text: str) -> set[str]:
    """Extract common colors from text."""
    if not text:
        return set()
        
    colors = {
        "red", "blue", "green", "black", "white", 
        "yellow", "orange", "purple", "pink", "brown",
        "gray", "grey", "silver", "gold", "beige", "maroon", "navy"
    }
    
    found = set()
    text_lower = text.lower()
    # Simple word boundary check to avoid partial matches like "red" in "tired"
    for color in colors:
        if re.search(r'\b' + re.escape(color) + r'\b', text_lower):
            found.add(color)
    return found


def _cosine_similarity_fast(vector_a: list[float] | None, vector_b: list[float] | None) -> float:
    """
    Fast cosine similarity calculation using numpy.
    Returns -1.0 if either vector is None or empty.
    """
    if vector_a is None or vector_b is None:
        return -1.0
        
    np_a = np.array(vector_a, dtype=np.float32)
    np_b = np.array(vector_b, dtype=np.float32)

    norm_a = np.linalg.norm(np_a)
    norm_b = np.linalg.norm(np_b)

    if norm_a == 0 or norm_b == 0:
        return -1.0

    return float(np.dot(np_a, np_b) / (norm_a * norm_b))


async def run_matching_algorithm(session: AsyncSession, new_item: Item) -> list[Match]:
    """
    Create match candidates for a newly reported item using optimized vector similarity.
    
    Optimization:
    - Uses database-side HNSW indices to fetch only relevant candidates.
    - Performs multi-vector search (image-image, text-image, text-text) to maximize recall.
    - Re-ranks candidates in memory with full weighted scoring.
    """
    logger.info(f"Starting matching algorithm for item {new_item.id} (status: {new_item.status})")

    target_status = ItemStatus.FOUND if new_item.status == ItemStatus.LOST else ItemStatus.LOST
    
    if new_item.status not in (ItemStatus.LOST, ItemStatus.FOUND):
        logger.warning(f"Invalid item status: {new_item.status}")
        return []

    # 1. Candidate Retrieval Strategy
    # We run multiple queries to get the top K candidates for each similarity aspect.
    # This ensures we don't miss items that are strong in one modality but weak in another.
    
    candidates: dict[str, Item] = {}  # Use dict to deduplicate by ID
    limit_per_query = 20  # Fetch top 20 for each aspect
    
    base_filters = [
        Item.status == target_status,
        Item.is_active.is_(True),
        Item.id != new_item.id
    ]

    # Time Window Filter
    if settings.matching_time_window_days > 0:
        window = timedelta(days=settings.matching_time_window_days)
        start_date = new_item.reported_at - window
        end_date = new_item.reported_at + window
        base_filters.append(Item.reported_at >= start_date)
        base_filters.append(Item.reported_at <= end_date)

    queries = []

    # A. Image-to-Image (Highest Priority)
    if new_item.image_vector is not None:
        queries.append(
            select(Item)
            .where(and_(*base_filters, Item.image_vector.is_not(None)))
            .order_by(Item.image_vector.cosine_distance(new_item.image_vector))
            .limit(limit_per_query)
        )

    # B. Text-to-Image (CLIP text vs Item Image)
    if new_item.description_clip_vector is not None:
        queries.append(
            select(Item)
            .where(and_(*base_filters, Item.image_vector.is_not(None)))
            .order_by(Item.image_vector.cosine_distance(new_item.description_clip_vector))
            .limit(limit_per_query)
        )

    # C. Image-to-Text (Item Image vs CLIP text)
    if new_item.image_vector is not None:
        queries.append(
            select(Item)
            .where(and_(*base_filters, Item.description_clip_vector.is_not(None)))
            .order_by(Item.description_clip_vector.cosine_distance(new_item.image_vector))
            .limit(limit_per_query)
        )

    # D. Text-to-Text (MiniLM) - Baseline
    if new_item.description_vector is not None:
        queries.append(
            select(Item)
            .where(and_(*base_filters, Item.description_vector.is_not(None)))
            .order_by(Item.description_vector.cosine_distance(new_item.description_vector))
            .limit(limit_per_query)
        )

    # Execute all queries
    for q in queries:
        result = await session.execute(q)
        items = result.scalars().all()
        for item in items:
            candidates[str(item.id)] = item

    target_items = list(candidates.values())
    logger.info(f"Retrieved {len(target_items)} unique candidates from DB indices")

    if not target_items:
        return []

    # 2. Re-ranking (In-Memory)
    # Now we have a small set of high-potential candidates. We calculate the full weighted score.
    
    matches_to_create: list[Match] = []
    threshold = settings.match_confidence_threshold
    candidate_scores: list[tuple[Item, float]] = []

    WEIGHT_IMAGE_IMAGE = 1.2  # Increased from 1.0
    WEIGHT_TEXT_IMAGE = 0.85
    WEIGHT_IMAGE_TEXT = 0.75
    WEIGHT_TEXT_TEXT = 0.5   # Decreased from 0.65
    
    # Pre-extract keywords/colors for new item
    new_keywords = _extract_keywords(new_item.description)
    new_colors = _extract_colors(new_item.description)
    
    for candidate in target_items:
        score_ii = _cosine_similarity_fast(new_item.image_vector, candidate.image_vector) if new_item.image_vector is not None and candidate.image_vector is not None else None
        score_ti = _cosine_similarity_fast(new_item.description_clip_vector, candidate.image_vector) if new_item.description_clip_vector is not None and candidate.image_vector is not None else None
        score_it = _cosine_similarity_fast(new_item.image_vector, candidate.description_clip_vector) if new_item.image_vector is not None and candidate.description_clip_vector is not None else None
        score_tt = _cosine_similarity_fast(new_item.description_vector, candidate.description_vector) if new_item.description_vector is not None and candidate.description_vector is not None else None

        weighted_scores: list[tuple[float, float]] = []
        if score_ii is not None and score_ii > 0: weighted_scores.append((score_ii, WEIGHT_IMAGE_IMAGE))
        if score_ti is not None and score_ti > 0: weighted_scores.append((score_ti, WEIGHT_TEXT_IMAGE))
        if score_it is not None and score_it > 0: weighted_scores.append((score_it, WEIGHT_IMAGE_TEXT))
        if score_tt is not None and score_tt > 0: weighted_scores.append((score_tt, WEIGHT_TEXT_TEXT))
        
        if not weighted_scores:
            continue
        
        # Weighted average
        total_weight = sum(weight for _, weight in weighted_scores)
        weighted_sum = sum(score * weight for score, weight in weighted_scores)
        base_score = weighted_sum / total_weight
        
        # Boost for image-image match
        if score_ii is not None and score_ii > 0:
            base_score = max(base_score, score_ii * 1.05)

        # Keyword Boost
        cand_keywords = _extract_keywords(candidate.description)
        common_keywords = new_keywords.intersection(cand_keywords)
        if common_keywords:
            # Boost if they share at least one significant noun
            base_score += 0.1
            
        # Color Boost/Penalty
        cand_colors = _extract_colors(candidate.description)
        if new_colors and cand_colors:
            common_colors = new_colors.intersection(cand_colors)
            if common_colors:
                base_score += 0.05
            elif not common_colors:
                # If both have colors but NO overlap, slight penalty
                # (Only if they have single colors to avoid complex multi-color issues)
                if len(new_colors) == 1 and len(cand_colors) == 1:
                    base_score -= 0.1

        # Location boost
        if base_score >= threshold * 0.8:
            final_score = apply_location_boost(base_score, new_item.location, candidate.location, boost_factor=0.05)
        else:
            final_score = base_score

        if final_score >= threshold or isclose(final_score, threshold, abs_tol=0.01):
            candidate_scores.append((candidate, final_score))

    # Sort and Limit
    candidate_scores.sort(key=lambda x: x[1], reverse=True)
    candidate_scores = candidate_scores[: settings.max_matches_returned]

    # 3. Create Matches
    for candidate, final_score in candidate_scores:
        # Determine lost/found roles
        if new_item.status == ItemStatus.LOST:
            lost_item, found_item = new_item, candidate
            loser_id, finder_id = new_item.reported_by_user_id, candidate.reported_by_user_id
        else:
            lost_item, found_item = candidate, new_item
            loser_id, finder_id = candidate.reported_by_user_id, new_item.reported_by_user_id

        # Check existence
        existing = await session.execute(
            select(Match).where(Match.lost_item_id == lost_item.id, Match.found_item_id == found_item.id)
        )
        if existing.scalar_one_or_none():
            continue

        match = Match(
            lost_item_id=lost_item.id,
            found_item_id=found_item.id,
            loser_id=loser_id,
            finder_id=finder_id,
            confidence_score=final_score,
        )
        session.add(match)
        matches_to_create.append(match)

    if matches_to_create:
        await session.flush()
        logger.info(f"Created {len(matches_to_create)} matches")

    return matches_to_create


def _admin_contact_payload() -> dict[str, str]:
    return {
        "name": settings.admin_office_name,
        "email": settings.admin_office_email,
        "contact_number": settings.admin_office_contact_number,
    }


def _user_contact_payload(user: User) -> dict[str, str]:
    return {
        "name": user.name,
        "email": user.email,
        "contact_number": user.contact_number,
    }


async def approve_match(session: AsyncSession, *, match: Match, acting_user: User) -> tuple[Match, dict[str, str], dict[str, str]]:
    """Approve a match, archive involved items, and prepare contact payloads."""

    if match.loser_id != acting_user.id:
        raise PermissionError("Only the owner of the lost item can approve the match")

    await session.refresh(match, attribute_names=["lost_item", "found_item"])
    await session.refresh(match.lost_item, attribute_names=["reported_by"])
    await session.refresh(match.found_item, attribute_names=["reported_by"])

    match.match_status = MatchStatus.APPROVED
    match.lost_item.is_active = False
    match.lost_item.has_match_found = True
    match.found_item.is_active = False
    match.found_item.has_match_found = True

    if match.lost_item.is_admin_report and match.lost_item.reported_by.role == UserRole.ADMIN:
        loser_contact = _admin_contact_payload()
    else:
        loser_contact = _user_contact_payload(match.lost_item.reported_by)
    
    if match.found_item.is_admin_report and match.found_item.reported_by.role == UserRole.ADMIN:
        finder_contact = _admin_contact_payload()
    else:
        finder_contact = _user_contact_payload(match.found_item.reported_by)

    session.add(match)
    await session.commit()
    await session.refresh(match)

    return match, loser_contact, finder_contact


async def reject_match(session: AsyncSession, *, match: Match, acting_user: User) -> Match:
    """Reject a pending match."""

    if match.loser_id != acting_user.id:
        raise PermissionError("Only the owner of the lost item can reject the match")

    match.match_status = MatchStatus.REJECTED
    session.add(match)
    await session.commit()
    await session.refresh(match)
    return match

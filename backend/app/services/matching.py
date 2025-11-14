from __future__ import annotations

import logging
from math import isclose

import numpy as np
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.models import Item, ItemStatus, Match, MatchStatus, User, UserRole
from app.utils.location_proximity import apply_location_boost

settings = get_settings()
logger = logging.getLogger(__name__)


def _cosine_similarity_fast(vector_a: list[float], vector_b: list[float]) -> float:
    """
    Fast cosine similarity calculation using numpy (optimized for performance).

    This is faster than individual SQL queries for batch processing.
    Uses float32 for memory efficiency and faster computation.
    """
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

    This function:
    - Calculates multiple similarity scores (text-text, text-image, image-text, image-image)
    - Takes the maximum similarity score for each candidate
    - Applies location proximity boost as a last resort tie-breaker (only when score is close to threshold)
    - Limits results to max_matches_returned for performance
    - Uses efficient numpy-based cosine similarity calculations
    
    IMPORTANT: Found items are ONLY compared with Lost items, and vice versa.
    """
    logger.info(f"Starting matching algorithm for item {new_item.id} (status: {new_item.status})")

    # Ensure we only match opposite statuses: LOST items match with FOUND items only
    target_status = ItemStatus.FOUND if new_item.status == ItemStatus.LOST else ItemStatus.LOST
    logger.info(f"Target status: {target_status}")
    
    # Defensive check: ensure new_item has a valid status
    if new_item.status not in (ItemStatus.LOST, ItemStatus.FOUND):
        logger.warning(f"Invalid item status: {new_item.status}")
        return []

    # Fetch target items with basic filters
    # CRITICAL: Only fetch items with the OPPOSITE status
    statement = (
        select(Item)
        .where(
            and_(
                Item.status == target_status,  # Only opposite status items
                Item.is_active.is_(True),
                Item.id != new_item.id,
            )
        )
        .order_by(Item.reported_at.desc())
        .limit(settings.max_matches_returned * 2)  # Fetch more candidates, filter later
    )
    target_items = list((await session.execute(statement)).scalars().all())
    logger.info(f"Found {len(target_items)} candidate items with status {target_status}")
    
    # Additional defensive check: verify all candidates have the correct status
    target_items = [item for item in target_items if item.status == target_status]

    if not target_items:
        logger.info(f"No target items found for matching")
        return []

    matches_to_create: list[Match] = []
    threshold = settings.match_confidence_threshold
    logger.info(f"Match confidence threshold: {threshold}")

    # Pre-calculate all similarity scores efficiently
    candidate_scores: list[tuple[Item, float]] = []

    # Weight configuration for different similarity types
    # Priority: image-image > text-image > image-text > text-text
    WEIGHT_IMAGE_IMAGE = 1.0      # Highest priority
    WEIGHT_TEXT_IMAGE = 0.85      # High priority
    WEIGHT_IMAGE_TEXT = 0.75      # Medium-high priority
    WEIGHT_TEXT_TEXT = 0.65       # Lower priority (baseline)
    
    for candidate in target_items:
        # Calculate all possible similarity combinations efficiently
        # Store scores with their types for weighted calculation
        score_tt = None
        score_ti = None
        score_it = None
        score_ii = None

        # Text-to-text similarity (MiniLM)
        # Check if vectors exist and are not empty (avoid array truthiness ambiguity)
        if (new_item.description_vector is not None and len(new_item.description_vector) > 0 and
            candidate.description_vector is not None and len(candidate.description_vector) > 0):
            score_tt = _cosine_similarity_fast(new_item.description_vector, candidate.description_vector)
            if score_tt < 0:
                score_tt = None

        # CLIP text-to-image similarity
        if (new_item.description_clip_vector is not None and len(new_item.description_clip_vector) > 0 and
            candidate.image_vector is not None and len(candidate.image_vector) > 0):
            score_ti = _cosine_similarity_fast(new_item.description_clip_vector, candidate.image_vector)
            if score_ti < 0:
                score_ti = None

        # Image-to-CLIP text similarity
        if (new_item.image_vector is not None and len(new_item.image_vector) > 0 and
            candidate.description_clip_vector is not None and len(candidate.description_clip_vector) > 0):
            score_it = _cosine_similarity_fast(new_item.image_vector, candidate.description_clip_vector)
            if score_it < 0:
                score_it = None

        # Image-to-image similarity (highest priority)
        if (new_item.image_vector is not None and len(new_item.image_vector) > 0 and
            candidate.image_vector is not None and len(candidate.image_vector) > 0):
            score_ii = _cosine_similarity_fast(new_item.image_vector, candidate.image_vector)
            if score_ii < 0:
                score_ii = None

        # Calculate weighted score based on priority
        # Use weighted average when multiple scores are available, prioritizing higher-weight scores
        weighted_scores: list[tuple[float, float]] = []  # (score, weight)
        
        if score_ii is not None:
            weighted_scores.append((score_ii, WEIGHT_IMAGE_IMAGE))
        if score_ti is not None:
            weighted_scores.append((score_ti, WEIGHT_TEXT_IMAGE))
        if score_it is not None:
            weighted_scores.append((score_it, WEIGHT_IMAGE_TEXT))
        if score_tt is not None:
            weighted_scores.append((score_tt, WEIGHT_TEXT_TEXT))
        
        if not weighted_scores:
            continue
        
        # Calculate weighted average, but prioritize higher-weight scores more
        # Use weighted harmonic mean for better emphasis on high-priority matches
        if len(weighted_scores) == 1:
            base_score = weighted_scores[0][0]
        else:
            # Weighted average with emphasis on higher weights
            total_weight = sum(weight for _, weight in weighted_scores)
            weighted_sum = sum(score * weight for score, weight in weighted_scores)
            base_score = weighted_sum / total_weight
            
            # Boost if highest-priority score (image-image) exists
            if score_ii is not None:
                # Give extra boost to image-image matches
                base_score = max(base_score, score_ii * 1.05)  # 5% boost for image-image
        
        # Format scores for logging (handle None values)
        ii_str = f"{score_ii:.4f}" if score_ii is not None else "N/A"
        ti_str = f"{score_ti:.4f}" if score_ti is not None else "N/A"
        it_str = f"{score_it:.4f}" if score_it is not None else "N/A"
        tt_str = f"{score_tt:.4f}" if score_tt is not None else "N/A"
        
        logger.debug(
            f"Candidate {candidate.id}: base_score={base_score:.4f}, "
            f"ii={ii_str}, ti={ti_str}, it={it_str}, tt={tt_str}"
        )

        # Apply location proximity boost as last resort (only if score is close to threshold)
        # This ensures location is truly a last resort tie-breaker
        if base_score >= threshold * 0.9:  # Only boost if already close to threshold
            final_score = apply_location_boost(
                base_score,
                new_item.location,
                candidate.location,
                boost_factor=0.05,  # Small boost (5% max)
            )
            logger.debug(f"Candidate {candidate.id}: location boost applied, final_score={final_score:.4f}")
        else:
            final_score = base_score

        # Only consider candidates above threshold
        if final_score >= threshold or isclose(final_score, threshold, abs_tol=0.01):
            candidate_scores.append((candidate, final_score))
            logger.info(f"Candidate {candidate.id} passed threshold: {final_score:.4f} >= {threshold}")
        else:
            logger.debug(f"Candidate {candidate.id} below threshold: {final_score:.4f} < {threshold}")

    # Sort by score descending and limit to max matches
    candidate_scores.sort(key=lambda x: x[1], reverse=True)
    candidate_scores = candidate_scores[: settings.max_matches_returned]
    logger.info(f"Found {len(candidate_scores)} candidates above threshold")

    # Check for existing matches and create new ones
    for candidate, final_score in candidate_scores:
        # Defensive check: ensure candidate has opposite status
        if candidate.status == new_item.status:
            continue  # Skip if somehow same status (should never happen, but safety check)
        
        # Determine which item is lost and which is found
        if new_item.status == ItemStatus.LOST:
            # new_item is LOST, candidate must be FOUND
            assert candidate.status == ItemStatus.FOUND, "Candidate must be FOUND when new_item is LOST"
            lost_item_id = new_item.id
            found_item_id = candidate.id
            loser_id = new_item.reported_by_user_id
            finder_id = candidate.reported_by_user_id
        else:
            # new_item is FOUND, candidate must be LOST
            assert candidate.status == ItemStatus.LOST, "Candidate must be LOST when new_item is FOUND"
            lost_item_id = candidate.id
            found_item_id = new_item.id
            loser_id = candidate.reported_by_user_id
            finder_id = new_item.reported_by_user_id
        
        # Check for existing matches
        existing_statement = select(Match).where(
            Match.lost_item_id == lost_item_id,
            Match.found_item_id == found_item_id,
        )
        if (await session.execute(existing_statement)).scalar_one_or_none():
            continue

        match = Match(
            lost_item_id=lost_item_id,
            found_item_id=found_item_id,
            loser_id=loser_id,
            finder_id=finder_id,
            confidence_score=final_score,
        )
        session.add(match)
        matches_to_create.append(match)
        logger.info(f"Created match {match.id}: lost_item={lost_item_id}, found_item={found_item_id}, score={final_score:.4f}")

    if matches_to_create:
        await session.flush()
        logger.info(f"Successfully created {len(matches_to_create)} matches")
    else:
        logger.info("No matches created")

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

    # Determine contact for lost item:
    # - If admin report AND reported_by is admin: office report → use admin contact
    # - If admin report AND reported_by is user: on behalf report → use user contact
    # - If not admin report: regular report → use user contact
    if match.lost_item.is_admin_report and match.lost_item.reported_by.role == UserRole.ADMIN:
        loser_contact = _admin_contact_payload()
    else:
        loser_contact = _user_contact_payload(match.lost_item.reported_by)
    
    # Determine contact for found item:
    # - If admin report AND reported_by is admin: office report → use admin contact
    # - If admin report AND reported_by is user: on behalf report → use user contact
    # - If not admin report: regular report → use user contact
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


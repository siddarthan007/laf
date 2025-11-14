"""Location proximity mapping utility for TSP-like distance calculations."""

from __future__ import annotations

from functools import lru_cache


# Standardized location names (case-insensitive matching)
STANDARD_LOCATIONS = {
    "cafeteria",
    "library",
    "hostel a",
    "hostel b",
    "hostel c",
    "tan block",
    "cos block",
    "g block",
    "b block",
}

# Proximity matrix: represents "distance" between locations (lower = closer)
# This is a symmetric matrix where values represent proximity scores (0-1 scale)
# Higher values mean locations are closer together
LOCATION_PROXIMITY_MATRIX: dict[str, dict[str, float]] = {
    "cafeteria": {
        "cafeteria": 1.0,
        "library": 0.3,
        "hostel a": 0.5,
        "hostel b": 0.6,
        "hostel c": 0.4,
        "tan block": 0.7,
        "cos block": 0.6,
        "g block": 0.8,
        "b block": 0.7,
    },
    "library": {
        "cafeteria": 0.3,
        "library": 1.0,
        "hostel a": 0.2,
        "hostel b": 0.3,
        "hostel c": 0.2,
        "tan block": 0.4,
        "cos block": 0.5,
        "g block": 0.3,
        "b block": 0.4,
    },
    "hostel a": {
        "cafeteria": 0.5,
        "library": 0.2,
        "hostel a": 1.0,
        "hostel b": 0.9,
        "hostel c": 0.8,
        "tan block": 0.3,
        "cos block": 0.4,
        "g block": 0.2,
        "b block": 0.3,
    },
    "hostel b": {
        "cafeteria": 0.6,
        "library": 0.3,
        "hostel a": 0.9,
        "hostel b": 1.0,
        "hostel c": 0.9,
        "tan block": 0.4,
        "cos block": 0.5,
        "g block": 0.3,
        "b block": 0.4,
    },
    "hostel c": {
        "cafeteria": 0.4,
        "library": 0.2,
        "hostel a": 0.8,
        "hostel b": 0.9,
        "hostel c": 1.0,
        "tan block": 0.2,
        "cos block": 0.3,
        "g block": 0.2,
        "b block": 0.3,
    },
    "tan block": {
        "cafeteria": 0.7,
        "library": 0.4,
        "hostel a": 0.3,
        "hostel b": 0.4,
        "hostel c": 0.2,
        "tan block": 1.0,
        "cos block": 0.8,
        "g block": 0.5,
        "b block": 0.6,
    },
    "cos block": {
        "cafeteria": 0.6,
        "library": 0.5,
        "hostel a": 0.4,
        "hostel b": 0.5,
        "hostel c": 0.3,
        "tan block": 0.8,
        "cos block": 1.0,
        "g block": 0.6,
        "b block": 0.7,
    },
    "g block": {
        "cafeteria": 0.8,
        "library": 0.3,
        "hostel a": 0.2,
        "hostel b": 0.3,
        "hostel c": 0.2,
        "tan block": 0.5,
        "cos block": 0.6,
        "g block": 1.0,
        "b block": 0.9,
    },
    "b block": {
        "cafeteria": 0.7,
        "library": 0.4,
        "hostel a": 0.3,
        "hostel b": 0.4,
        "hostel c": 0.3,
        "tan block": 0.6,
        "cos block": 0.7,
        "g block": 0.9,
        "b block": 1.0,
    },
}


def normalize_location_name(location: str) -> str | None:
    """Normalize a location string to match standard location names."""
    if not location:
        return None

    normalized = location.strip().lower()

    # Direct match
    if normalized in STANDARD_LOCATIONS:
        return normalized

    # Fuzzy matching for common variations
    location_mappings = {
        "cafe": "cafeteria",
        "mess": "cafeteria",
        "lib": "library",
        "hostel-a": "hostel a",
        "hostel-a": "hostel a",
        "hostel a": "hostel a",
        "hostel-b": "hostel b",
        "hostel-b": "hostel b",
        "hostel b": "hostel b",
        "hostel-c": "hostel c",
        "hostel-c": "hostel c",
        "hostel c": "hostel c",
        "tan": "tan block",
        "cos": "cos block",
        "g": "g block",
        "b": "b block",
    }

    for key, value in location_mappings.items():
        if key in normalized:
            return value

    # Check if any standard location is contained in the input
    for std_loc in STANDARD_LOCATIONS:
        if std_loc in normalized or normalized in std_loc:
            return std_loc

    return None


@lru_cache(maxsize=256)
def get_location_proximity(location_a: str, location_b: str) -> float:
    """
    Get proximity score between two locations (0-1 scale, higher = closer).

    Returns:
        Proximity score between 0.0 and 1.0. Returns 0.0 if locations
        cannot be matched or are not in the proximity matrix.
    """
    norm_a = normalize_location_name(location_a)
    norm_b = normalize_location_name(location_b)

    if not norm_a or not norm_b:
        return 0.0

    return LOCATION_PROXIMITY_MATRIX.get(norm_a, {}).get(norm_b, 0.0)


def apply_location_boost(base_score: float, location_a: str, location_b: str, boost_factor: float = 0.1) -> float:
    """
    Apply location proximity as a small boost to the base similarity score.

    Location proximity is used as a last resort tie-breaker, so the boost
    is minimal and only applied when locations are reasonably close.

    Args:
        base_score: The base similarity score from vector matching (0-1)
        location_a: First location string
        location_b: Second location string
        boost_factor: Maximum boost to apply (default 0.1 = 10%)

    Returns:
        Adjusted score with location boost applied
    """
    proximity = get_location_proximity(location_a, location_b)

    # Only apply boost if locations are reasonably close (proximity > 0.5)
    # and base score is already above threshold
    if proximity > 0.5 and base_score >= 0.5:
        # Apply a small boost proportional to proximity
        boost = proximity * boost_factor
        return min(1.0, base_score + boost)

    return base_score


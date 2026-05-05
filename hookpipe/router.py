"""Route incoming requests to matching pipeline configurations."""

from typing import Any

from hookpipe.filters import apply_filters, FilterError


class RouterError(Exception):
    """Raised when routing fails."""


def _matches_route(payload: dict[str, Any], route: dict[str, Any]) -> bool:
    """Return True if payload satisfies all filters defined in the route."""
    filters = route.get("filters", [])
    if not filters:
        return True
    try:
        return apply_filters(payload, filters)
    except FilterError:
        return False


def find_matching_routes(
    payload: dict[str, Any],
    routes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return all routes whose filters match the given payload.

    Args:
        payload: Parsed webhook payload.
        routes:  List of route config dicts, each optionally containing
                 a ``filters`` list and a ``targets`` list.

    Returns:
        Subset of *routes* that match.

    Raises:
        RouterError: If *routes* is not a list.
    """
    if not isinstance(routes, list):
        raise RouterError("routes must be a list")

    return [route for route in routes if _matches_route(payload, route)]


def collect_targets(
    matched_routes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Flatten targets from all matched routes, preserving order.

    Args:
        matched_routes: Routes returned by :func:`find_matching_routes`.

    Returns:
        Deduplicated list of target dicts (by ``url`` key).
    """
    seen: set[str] = set()
    targets: list[dict[str, Any]] = []
    for route in matched_routes:
        for target in route.get("targets", []):
            url = target.get("url", "")
            if url and url not in seen:
                seen.add(url)
                targets.append(target)
    return targets

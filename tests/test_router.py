"""Tests for hookpipe.router."""

import pytest

from hookpipe.router import RouterError, find_matching_routes, collect_targets


ROUTES = [
    {
        "name": "github-push",
        "filters": [{"field": "event", "op": "eq", "value": "push"}],
        "targets": [{"url": "https://example.com/push"}],
    },
    {
        "name": "github-pr",
        "filters": [{"field": "event", "op": "eq", "value": "pull_request"}],
        "targets": [{"url": "https://example.com/pr"}],
    },
    {
        "name": "catch-all",
        "filters": [],
        "targets": [
            {"url": "https://example.com/all"},
            {"url": "https://example.com/push"},  # duplicate url
        ],
    },
]


def test_find_matching_routes_single_match():
    payload = {"event": "push", "repo": "hookpipe"}
    matched = find_matching_routes(payload, ROUTES)
    names = [r["name"] for r in matched]
    assert "github-push" in names
    assert "github-pr" not in names


def test_find_matching_routes_catch_all_always_matches():
    payload = {"event": "delete"}
    matched = find_matching_routes(payload, ROUTES)
    names = [r["name"] for r in matched]
    assert "catch-all" in names


def test_find_matching_routes_no_match():
    routes = [
        {"filters": [{"field": "event", "op": "eq", "value": "push"}], "targets": []}
    ]
    matched = find_matching_routes({"event": "delete"}, routes)
    assert matched == []


def test_find_matching_routes_empty_routes():
    assert find_matching_routes({"event": "push"}, []) == []


def test_find_matching_routes_invalid_routes_type():
    with pytest.raises(RouterError):
        find_matching_routes({}, "not-a-list")  # type: ignore[arg-type]


def test_find_matching_routes_bad_filter_skipped():
    routes = [
        {"filters": [{"field": "x", "op": "unknown_op", "value": 1}], "targets": []}
    ]
    # Bad filter should not raise; route simply does not match
    matched = find_matching_routes({"x": 1}, routes)
    assert matched == []


def test_collect_targets_deduplicates_by_url():
    payload = {"event": "push"}
    matched = find_matching_routes(payload, ROUTES)  # push + catch-all
    targets = collect_targets(matched)
    urls = [t["url"] for t in targets]
    assert urls.count("https://example.com/push") == 1


def test_collect_targets_preserves_order():
    matched = [
        {"targets": [{"url": "https://a.com"}, {"url": "https://b.com"}]},
        {"targets": [{"url": "https://c.com"}]},
    ]
    targets = collect_targets(matched)
    assert [t["url"] for t in targets] == [
        "https://a.com",
        "https://b.com",
        "https://c.com",
    ]


def test_collect_targets_empty_matched():
    assert collect_targets([]) == []


def test_collect_targets_skips_targets_without_url():
    matched = [{"targets": [{"method": "POST"}, {"url": "https://valid.com"}]}]
    targets = collect_targets(matched)
    assert len(targets) == 1
    assert targets[0]["url"] == "https://valid.com"

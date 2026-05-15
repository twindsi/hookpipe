"""filter_chain_middleware.py — Wrap a handler with a pre-built filter chain.

The returned callable applies the chain before invoking the inner handler.
If the chain raises FilterChainError the exception propagates unchanged,
allowing callers to translate it into an HTTP 400 / skip response.
"""

from typing import Any, Callable, Dict, List

from hookpipe.event_filter_chain import (
    FilterChainError,
    build_chain,
    run_filter_chain,
)


def with_filter_chain(
    handler: Callable[[Dict], Any],
    steps: List[Dict],
    *,
    raise_on_mismatch: bool = True,
) -> Callable[[Dict], Any]:
    """Return a new callable that runs *steps* before calling *handler*.

    Parameters
    ----------
    handler:
        The downstream function to call when all required steps match.
        It receives the original payload and must return a result.
    steps:
        Raw list of step dicts as loaded from config.  ``build_chain`` is
        called once at wrap-time so configuration errors surface early.
    raise_on_mismatch:
        Forwarded to :func:`run_filter_chain`.  When *False* the handler is
        still called even if required steps did not match.
    """
    chain = build_chain(steps)

    def _wrapped(payload: Dict) -> Any:
        run_filter_chain(payload, chain, raise_on_mismatch=raise_on_mismatch)
        return handler(payload)

    _wrapped.__wrapped__ = handler  # type: ignore[attr-defined]
    return _wrapped


def get_matched_steps(
    payload: Dict,
    steps: List[Dict],
    *,
    raise_on_mismatch: bool = False,
) -> List[str]:
    """Convenience helper: build *steps* and return matched step names.

    Useful for introspection / logging without going through the full
    middleware wrapper.
    """
    chain = build_chain(steps)
    return run_filter_chain(payload, chain, raise_on_mismatch=raise_on_mismatch)

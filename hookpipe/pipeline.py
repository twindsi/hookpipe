"""Pipeline orchestration: filter → transform → deliver with retry."""

from typing import Any, Dict, List, Optional
import time

from hookpipe.filters import FilterError, apply_filters
from hookpipe.transforms import TransformError, apply_transforms
from hookpipe.delivery import DeliveryError, deliver
from hookpipe.retry import RetryError, with_retry
from hookpipe.logging_utils import log_event, log_delivery_attempt


class PipelineError(Exception):
    """Raised when the pipeline cannot be constructed or executed."""


class Pipeline:
    """Orchestrates filter → transform → deliver for a single webhook route."""

    def __init__(
        self,
        destination: str,
        filters: Optional[List[Dict[str, Any]]] = None,
        transforms: Optional[List[Dict[str, Any]]] = None,
        retry: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        method: str = "POST",
    ) -> None:
        self.destination = destination
        self.filters = filters or []
        self.transforms = transforms or []
        self.retry_config = retry or {}
        self.headers = headers or {}
        self.method = method

    def process(self, payload: Dict[str, Any]) -> bool:
        """Run the pipeline for *payload*.

        Returns True if the payload was delivered, False if filtered out.
        Raises PipelineError on unrecoverable failure.
        """
        log_event("pipeline_start", payload=payload, destination=self.destination)

        # --- Filter stage ---
        try:
            if not apply_filters(payload, self.filters):
                log_event(
                    "pipeline_filtered",
                    payload=payload,
                    destination=self.destination,
                    status="filtered",
                )
                return False
        except FilterError as exc:
            raise PipelineError(f"Filter stage failed: {exc}") from exc

        # --- Transform stage ---
        try:
            transformed = apply_transforms(payload, self.transforms)
        except TransformError as exc:
            raise PipelineError(f"Transform stage failed: {exc}") from exc

        # --- Delivery stage (with optional retry) ---
        attempt_counter = [0]

        def _deliver():
            attempt_counter[0] += 1
            t0 = time.monotonic()
            try:
                response = deliver(
                    transformed,
                    self.destination,
                    headers=self.headers,
                    method=self.method,
                )
                duration_ms = (time.monotonic() - t0) * 1000
                log_delivery_attempt(
                    destination=self.destination,
                    attempt=attempt_counter[0],
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )
                return response
            except DeliveryError as exc:
                duration_ms = (time.monotonic() - t0) * 1000
                log_delivery_attempt(
                    destination=self.destination,
                    attempt=attempt_counter[0],
                    error=str(exc),
                    duration_ms=duration_ms,
                )
                raise

        try:
            with_retry(_deliver, **self.retry_config)
        except (DeliveryError, RetryError) as exc:
            raise PipelineError(f"Delivery failed: {exc}") from exc

        log_event("pipeline_complete", destination=self.destination, status="delivered")
        return True


def pipeline_from_config(cfg: Dict[str, Any]) -> Pipeline:
    """Construct a Pipeline from a validated config dict."""
    try:
        destination = cfg["destination"]
    except KeyError as exc:
        raise PipelineError("Config missing required key: destination") from exc
    return Pipeline(
        destination=destination,
        filters=cfg.get("filters"),
        transforms=cfg.get("transforms"),
        retry=cfg.get("retry"),
        headers=cfg.get("headers"),
        method=cfg.get("method", "POST"),
    )

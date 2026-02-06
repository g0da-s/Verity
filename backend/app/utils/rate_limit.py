"""Per-IP rate limiter for FastAPI endpoints.

Uses an in-memory sliding window.  Suitable for single-process deployments
(the default for this project).  No external dependencies required.

Default: 5 requests per 60-second window per IP.
"""

import time
import logging
from collections import defaultdict, deque
from threading import Lock

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# Global state — lives for the lifetime of the process.
# key: client IP  →  value: deque of request timestamps within the current window
_request_log: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()  # Thread safety for cleanup operations

# Tunables
WINDOW_SECONDS: int = 60
MAX_REQUESTS: int = 5

# Cleanup settings - remove stale IPs to prevent memory leak
_CLEANUP_INTERVAL: int = 300  # Run cleanup every 5 minutes
_STALE_THRESHOLD: int = WINDOW_SECONDS * 2  # Remove IPs with no activity for 2x window
_last_cleanup: float = 0.0


def _cleanup_stale_entries() -> None:
    """Remove IP entries that haven't had activity recently.

    This prevents unbounded memory growth from many unique IPs.
    Called periodically during rate limit checks.
    """
    global _last_cleanup
    now = time.time()

    # Only run cleanup periodically
    if now - _last_cleanup < _CLEANUP_INTERVAL:
        return

    with _lock:
        # Double-check after acquiring lock
        if now - _last_cleanup < _CLEANUP_INTERVAL:
            return

        stale_threshold = now - _STALE_THRESHOLD
        stale_ips = []

        for ip, timestamps in _request_log.items():
            # If the most recent request is older than threshold, mark for removal
            if not timestamps or timestamps[-1] < stale_threshold:
                stale_ips.append(ip)

        for ip in stale_ips:
            del _request_log[ip]

        if stale_ips:
            logger.debug(f"Rate limiter cleanup: removed {len(stale_ips)} stale IPs")

        _last_cleanup = now


async def rate_limit(request: Request) -> None:
    """FastAPI dependency that enforces per-IP rate limiting.

    Raises a 429 response with a Retry-After header when the limit is hit.

    Usage:
        @router.post("/verify", dependencies=[Depends(rate_limit)])
        async def verify_claim(...): ...
    """
    # Periodically clean up stale entries to prevent memory leak
    _cleanup_stale_entries()

    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - WINDOW_SECONDS

    log = _request_log[ip]

    # Drop timestamps that have fallen outside the window
    while log and log[0] <= window_start:
        log.popleft()

    if len(log) >= MAX_REQUESTS:
        # Oldest request in the window determines when the next slot opens
        retry_after = int(log[0] - window_start) + 1
        logger.info(f"Rate limit exceeded for IP (retry_after={retry_after}s)")
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Too many requests. Please wait before trying again.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    log.append(now)

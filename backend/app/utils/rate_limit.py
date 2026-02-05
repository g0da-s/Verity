"""Per-IP rate limiter for FastAPI endpoints.

Uses an in-memory sliding window.  Suitable for single-process deployments
(the default for this project).  No external dependencies required.

Default: 5 requests per 60-second window per IP.
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


# Global state — lives for the lifetime of the process.
# key: client IP  →  value: deque of request timestamps within the current window
_request_log: dict[str, deque[float]] = defaultdict(deque)

# Tunables
WINDOW_SECONDS: int = 60
MAX_REQUESTS: int = 5


async def rate_limit(request: Request) -> None:
    """FastAPI dependency that enforces per-IP rate limiting.

    Raises a 429 response with a Retry-After header when the limit is hit.

    Usage:
        @router.post("/verify", dependencies=[Depends(rate_limit)])
        async def verify_claim(...): ...
    """
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
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Too many requests. Please wait before trying again.",
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )

    log.append(now)

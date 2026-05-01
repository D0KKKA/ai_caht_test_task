"""Rate limiting utilities for FastAPI routes."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings


def rate_limit_key(request: Request) -> str:
    """Prefer anonymous client ID, fall back to remote IP."""
    client_id = request.headers.get("X-Client-Id")
    if client_id:
        return f"client:{client_id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=rate_limit_key, headers_enabled=True)
WRITE_RATE_LIMIT = get_settings().rate_limit

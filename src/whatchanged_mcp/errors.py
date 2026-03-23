"""Error types for whatchanged-mcp.

This module defines the exception hierarchy used throughout the server
for consistent error handling and reporting.
"""


class WhatChangedError(Exception):
    """Base error for whatchanged-mcp."""

    pass


class AuthenticationError(WhatChangedError):
    """PAT missing, invalid, or expired."""

    pass


class AuthorizationError(WhatChangedError):
    """Repository not in allowlist."""

    pass


class NotFoundError(WhatChangedError):
    """Requested resource not found."""

    pass


class RateLimitError(WhatChangedError):
    """Rate limit exceeded after retries."""

    pass


class InsufficientPermissionsError(WhatChangedError):
    """PAT lacks required permissions."""

    pass


class ValidationError(WhatChangedError):
    """Input validation failed."""

    pass

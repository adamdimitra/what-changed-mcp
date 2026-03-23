"""Configuration module for whatchanged-mcp.

This module handles loading server configuration from environment variables
and provides the ServerConfig dataclass for type-safe configuration access.
"""

import os
from dataclasses import dataclass, field

from .errors import AuthenticationError


@dataclass
class ServerConfig:
    """Configuration for the whatchanged-mcp server.

    Attributes:
        github_token: GitHub Personal Access Token for API authentication.
        repo_allowlist: Optional list of allowed repositories (e.g., ["owner/repo", "org/*"]).
        max_retries: Maximum number of retries for rate-limited requests.
        max_bytes_per_file: Maximum bytes to fetch per file diff.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """

    github_token: str
    repo_allowlist: list[str] | None = None
    max_retries: int = 3
    max_bytes_per_file: int = 50_000
    log_level: str = "INFO"


def load_config() -> ServerConfig:
    """Load configuration from environment variables.

    Environment variables:
        GITHUB_TOKEN: Required. GitHub Personal Access Token.
        REPO_ALLOWLIST: Optional. Comma-separated list of allowed repos.
        MAX_RETRIES: Optional. Maximum retry attempts (default: 3).
        MAX_BYTES_PER_FILE: Optional. Max bytes per file diff (default: 50000).
        LOG_LEVEL: Optional. Logging level (default: INFO).

    Returns:
        ServerConfig: Populated configuration object.

    Raises:
        AuthenticationError: If GITHUB_TOKEN is not set.
    """
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise AuthenticationError(
            "GITHUB_TOKEN environment variable is required but not set"
        )

    # Parse optional allowlist from comma-separated string
    allowlist_str = os.environ.get("REPO_ALLOWLIST")
    repo_allowlist: list[str] | None = None
    if allowlist_str:
        repo_allowlist = [r.strip() for r in allowlist_str.split(",") if r.strip()]

    # Parse optional numeric settings
    max_retries = int(os.environ.get("MAX_RETRIES", "3"))
    max_bytes_per_file = int(os.environ.get("MAX_BYTES_PER_FILE", "50000"))

    # Parse log level
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    return ServerConfig(
        github_token=github_token,
        repo_allowlist=repo_allowlist,
        max_retries=max_retries,
        max_bytes_per_file=max_bytes_per_file,
        log_level=log_level,
    )

"""whatchanged-mcp: A read-only Python MCP server for GitHub Actions CI failure analysis.

This MCP server provides tools for analyzing CI failures by comparing failed runs
against successful baselines, identifying likely culprits through deterministic
risk scoring.
"""

__version__ = "0.1.0"
__all__ = ["__version__"]

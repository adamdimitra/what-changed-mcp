# Implementation Plan: whatchanged-mcp

## Overview

This plan implements a Python MCP server for GitHub Actions CI failure analysis. The server exposes five core tools via stdio transport that enable systematic investigation of CI failures by comparing failed runs against successful baselines.

## Tasks

- [x] 1. Project setup and configuration
  - [x] 1.1 Create project structure and pyproject.toml
    - Create `src/whatchanged_mcp/` package directory
    - Set up pyproject.toml with dependencies: mcp, requests, hypothesis (dev)
    - Create `__init__.py` with version info
    - _Requirements: 1.1, 1.5_

  - [x] 1.2 Implement configuration module
    - Create `src/whatchanged_mcp/config.py`
    - Implement `ServerConfig` dataclass with github_token, repo_allowlist, max_retries, max_bytes_per_file, log_level
    - Implement `load_config()` to load from environment variables
    - Raise `AuthenticationError` when GITHUB_TOKEN is missing
    - _Requirements: 1.1, 1.2_

  - [ ]* 1.3 Write unit tests for configuration
    - Test valid PAT loading from environment
    - Test missing PAT raises AuthenticationError
    - Test allowlist parsing from comma-separated env var
    - _Requirements: 1.1, 1.2_

- [ ] 2. Core error types and allowlist validation
  - [ ] 2.1 Implement error types module
    - Create `src/whatchanged_mcp/errors.py`
    - Implement WhatChangedError base class
    - Implement AuthenticationError, AuthorizationError, NotFoundError, RateLimitError, InsufficientPermissionsError, ValidationError
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ] 2.2 Implement allowlist validator
    - Create `src/whatchanged_mcp/allowlist.py`
    - Implement `is_repo_allowed(owner, repo, allowlist)` supporting exact match and org wildcard
    - Implement `validate_repo_access()` that raises AuthorizationError
    - _Requirements: 1.3, 1.4_

  - [ ]* 2.3 Write property test for allowlist enforcement
    - **Property 1: Allowlist Enforcement**
    - **Validates: Requirements 1.3, 1.4**

  - [ ]* 2.4 Write unit tests for allowlist
    - Test exact match "owner/repo"
    - Test wildcard match "org/*"
    - Test no match rejection
    - Test None allowlist allows all
    - _Requirements: 1.3, 1.4_

- [ ] 3. Interest pattern matching
  - [ ] 3.1 Implement pattern matcher module
    - Create `src/whatchanged_mcp/patterns.py`
    - Define DEFAULT_INTEREST_PATTERNS constant with all 20 patterns from requirements
    - Implement `matches_interest_pattern(filename, patterns)` using fnmatch
    - Implement `filter_interest_files(files, patterns)`
    - _Requirements: 5.1, 5.2_

  - [ ]* 3.2 Write property test for interest pattern filtering
    - **Property 8: Interest Pattern Filtering**
    - **Validates: Requirements 5.1**

  - [ ]* 3.3 Write unit tests for pattern matching
    - Test each default pattern category matches expected files
    - Test custom patterns override defaults
    - Test non-matching files are excluded
    - _Requirements: 5.1, 5.2_

- [ ] 4. Checkpoint - Core components complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. GitHub API client implementation
  - [ ] 5.1 Implement GitHub client core
    - Create `src/whatchanged_mcp/github_client.py`
    - Implement dataclasses: RunContext, BaselineRun, Commit, ChangedFile, CompareResult, FileDiff
    - Implement GitHubClient class with token and session initialization
    - _Requirements: 2.1, 3.1, 4.1_

  - [ ] 5.2 Implement retry logic with exponential backoff
    - Implement `_request_with_retry()` method
    - Use exponential backoff: base 1s, multiplier 2x, jitter ±0.5s, max 30s
    - Retry up to max_retries (default 3) on 429 status
    - Raise RateLimitError after exhausting retries
    - _Requirements: 2.4, 8.5_

  - [ ]* 5.3 Write property test for exponential backoff retry
    - **Property 3: Exponential Backoff Retry**
    - **Validates: Requirements 2.4, 8.5**

  - [ ] 5.4 Implement get_run method
    - Fetch workflow run metadata from `/repos/{owner}/{repo}/actions/runs/{run_id}`
    - Return RunContext with all required fields
    - Handle 404 with NotFoundError, 401/403 with appropriate errors
    - _Requirements: 2.1, 2.2, 2.3, 2.5_

  - [ ]* 5.5 Write property test for run context response completeness
    - **Property 2: Run Context Response Completeness**
    - **Validates: Requirements 2.1, 2.5**

  - [ ] 5.6 Implement find_last_successful_run method
    - Query `/repos/{owner}/{repo}/actions/workflows/{workflow}/runs` with branch and status=success
    - Resolve workflow name to ID if needed via `/repos/{owner}/{repo}/actions/workflows`
    - Return most recent successful run or None
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 5.7 Write property tests for baseline run
    - **Property 4: Baseline Run Recency**
    - **Property 5: Baseline Response Completeness**
    - **Property 6: Workflow Name Resolution**
    - **Validates: Requirements 3.1, 3.2, 3.4, 3.5**

  - [ ] 5.8 Implement compare_refs method
    - Fetch comparison from `/repos/{owner}/{repo}/compare/{base}...{head}`
    - Return CompareResult with commits, files, and compare_url
    - Handle base==head case returning empty comparison
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 5.9 Write property test for compare response structure
    - **Property 7: Compare Response Structure**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

  - [ ] 5.10 Implement get_file_diff method
    - Fetch file content diff between refs
    - Truncate at max_bytes and set truncated flag
    - Generate change_summary and evidence_url
    - _Requirements: 5.3, 5.4, 5.5_

  - [ ]* 5.11 Write property tests for diff retrieval
    - **Property 9: Interest File Diff Retrieval**
    - **Property 10: Diff Truncation Indication**
    - **Validates: Requirements 5.3, 5.4, 5.5**

  - [ ]* 5.12 Write unit tests for GitHub client
    - Test successful API responses (mocked)
    - Test 404 handling for missing runs
    - Test 401/403 authentication errors
    - Test rate limit retry behavior
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 9.1_

- [ ] 6. Checkpoint - GitHub client complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Risk scorer implementation
  - [ ] 7.1 Implement risk scorer module
    - Create `src/whatchanged_mcp/risk_scorer.py`
    - Define RiskCategory enum with all categories
    - Define RISK_WEIGHTS dict with baseline weights from requirements
    - Implement Suspect dataclass
    - _Requirements: 6.1, 6.2_

  - [ ] 7.2 Implement file categorization
    - Implement `categorize_file(filename, diff_content)` to determine RiskCategory
    - Match workflow YAML, lockfiles, toolchain files, build scripts, Dockerfiles, etc.
    - _Requirements: 6.2_

  - [ ] 7.3 Implement change scoring
    - Implement `score_changes(files, diffs)` to produce ranked Suspects
    - Apply weights based on category
    - Ensure every Suspect has at least one evidence_url
    - Prefer fewer high-confidence suspects over many low-confidence
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6_

  - [ ] 7.4 Implement evidence sufficiency check
    - Implement `has_sufficient_evidence(suspects)` returning False if all scores ≤ 2
    - _Requirements: 6.4_

  - [ ]* 7.5 Write property tests for risk scoring
    - **Property 11: Risk Scoring Weight Application**
    - **Property 12: Evidence Requirement Invariant**
    - **Property 13: Insufficient Evidence Indication**
    - **Property 14: Suspect Structure Completeness**
    - **Validates: Requirements 6.2, 6.3, 6.4, 6.6**

  - [ ]* 7.6 Write unit tests for risk scorer
    - Test each category gets correct weight
    - Test ranking order is by score descending
    - Test evidence_urls always populated
    - Test insufficient evidence detection
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 8. Checkpoint - Risk scorer complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Security and input validation
  - [ ] 9.1 Implement input validation
    - Add input validation to all tool handlers
    - Check for path traversal patterns (../, etc.)
    - Check for shell metacharacters
    - Raise ValidationError for invalid inputs
    - _Requirements: 8.4, 9.3_

  - [ ] 9.2 Implement log redaction
    - Create utility to redact secrets from log messages
    - Detect PAT patterns, API key patterns
    - Replace with [REDACTED]
    - _Requirements: 8.3_

  - [ ]* 9.3 Write property tests for security
    - **Property 16: Log Secret Redaction**
    - **Property 17: Input Injection Validation**
    - **Validates: Requirements 8.3, 8.4**

  - [ ]* 9.4 Write unit tests for security
    - Test path traversal rejection
    - Test shell metacharacter rejection
    - Test PAT redaction in logs
    - _Requirements: 8.3, 8.4_

- [ ] 10. MCP tool handlers
  - [ ] 10.1 Implement tool definitions
    - Create `src/whatchanged_mcp/tools.py`
    - Define all 5 Tool objects with inputSchema
    - _Requirements: 1.5_

  - [ ] 10.2 Implement get_run_context handler
    - Implement `handle_get_run_context()` async function
    - Validate inputs, check allowlist, call GitHub client
    - Return TextContent with JSON response
    - _Requirements: 2.1, 2.5_

  - [ ] 10.3 Implement find_last_successful_run handler
    - Implement `handle_find_last_successful_run()` async function
    - Handle no baseline found case
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ] 10.4 Implement compare_refs handler
    - Implement `handle_compare_refs()` async function
    - Handle base==head case
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ] 10.5 Implement diff_interest_files handler
    - Implement `handle_diff_interest_files()` async function
    - Filter files through pattern matcher
    - Fetch diffs for matching files
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 10.6 Implement rank_changes_by_risk handler
    - Implement `handle_rank_changes_by_risk()` function
    - Include what_did_not_change and unknowns sections
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.1, 7.2, 7.3_

  - [ ]* 10.7 Write property test for final response structure
    - **Property 15: Final Response Structure**
    - **Validates: Requirements 7.1, 7.2, 7.3**

  - [ ]* 10.8 Write unit tests for tool handlers
    - Test valid inputs return expected structure
    - Test missing params return ValidationError
    - Test allowlist rejection
    - _Requirements: 1.3, 1.4, 9.3_

- [ ] 11. Error handling property tests
  - [ ]* 11.1 Write property tests for error handling
    - **Property 18: API Error Response Structure**
    - **Property 19: Validation Error Listing**
    - **Property 20: Error Evidence Inclusion**
    - **Validates: Requirements 9.1, 9.3, 9.5**

- [ ] 12. Checkpoint - Tool handlers complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. MCP server entry point
  - [ ] 13.1 Implement server module
    - Create `src/whatchanged_mcp/server.py`
    - Implement `create_server(config)` to create MCP Server with all tools registered
    - Implement `main()` async function for stdio transport
    - _Requirements: 1.1, 1.5_

  - [ ] 13.2 Implement tool routing
    - Register all 5 tools with the MCP server
    - Route tool calls to appropriate handlers
    - Pass GitHub client and config to handlers
    - _Requirements: 1.5_

  - [ ] 13.3 Create CLI entry point
    - Add `__main__.py` for `python -m whatchanged_mcp`
    - Load config and start server
    - _Requirements: 1.1_

  - [ ]* 13.4 Write unit tests for server
    - Test server initialization with valid config
    - Test server rejects missing PAT
    - Test all tools are registered
    - _Requirements: 1.1, 1.2, 1.5_

- [ ] 14. Integration tests
  - [ ]* 14.1 Write integration tests for MCP protocol
    - Test tool discovery via MCP protocol
    - Test tool invocation with valid parameters
    - Test error responses for invalid inputs
    - Test stdio transport communication
    - _Requirements: 1.5, 7.1, 7.4, 7.5_

- [ ] 15. Final checkpoint - All tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All GitHub API interactions are read-only per security requirements

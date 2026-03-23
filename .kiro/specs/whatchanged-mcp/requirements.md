# Requirements Document

## Introduction

whatchanged-mcp is a read-only Python MCP (Model Context Protocol) server for GitHub Actions CI failure analysis. The server accepts a failed GitHub Actions run, finds the last successful run on the same workflow and branch, compares them across multiple dimensions, and produces an evidence-backed, explainable ranking of likely culprits.

Design principle: "Diff-first, narrative-last." The LLM narrates facts, not guesses.

### Non-Goals
- No reruns, cancels, or workflow dispatch
- No auto-fixing or auto-PRs
- No opaque "AI guessed this" explanations
- No write access to GitHub

## Glossary

- **MCP_Server**: The Model Context Protocol server that exposes tools for CI failure analysis via stdio transport
- **GitHub_API_Client**: The component responsible for authenticated read-only communication with GitHub's REST API
- **Run_Context**: Metadata about a GitHub Actions workflow run including workflow_id, branch, head_sha, conclusion, and timestamps
- **Baseline_Run**: The most recent successful workflow run on the same workflow and branch, used as comparison reference
- **Risk_Scorer**: The component that applies deterministic heuristics to rank changed files by their likelihood of causing CI failure
- **Evidence_Link**: A URL pointing to GitHub resources (commits, diffs, runs) that substantiate a ranking decision
- **Interest_Pattern**: A glob pattern identifying high-signal files for diff extraction (workflows, lockfiles, build configs)
- **Suspect**: A ranked change item with category, score, rationale, and evidence URLs
- **PAT**: GitHub Personal Access Token used for authentication with repo read and actions read permissions

## Requirements

### Requirement 1: MCP Server Initialization

**User Story:** As a developer, I want to start the MCP server with my GitHub credentials, so that I can analyze CI failures in my repositories.

#### Acceptance Criteria

1. WHEN the MCP_Server is started with a valid PAT environment variable, THE MCP_Server SHALL initialize successfully and listen on stdio transport
2. WHEN the MCP_Server is started without a PAT, THE MCP_Server SHALL return an error message indicating missing authentication
3. WHEN a repo allowlist is configured, THE MCP_Server SHALL only accept requests for repositories in the allowlist
4. IF a request targets a repository not in the allowlist, THEN THE MCP_Server SHALL reject the request with an authorization error
5. THE MCP_Server SHALL expose all core tools via the MCP protocol

### Requirement 2: Run Context Retrieval

**User Story:** As a developer, I want to get context about a failed GitHub Actions run, so that I can understand what workflow and branch failed.

#### Acceptance Criteria

1. WHEN get_run_context is called with valid owner, repo, and run_id, THE GitHub_API_Client SHALL return workflow_id, workflow_name, branch, head_sha, conclusion, run_url, and created_at
2. IF the run_id does not exist, THEN THE GitHub_API_Client SHALL return an error indicating the run was not found
3. IF the PAT lacks sufficient permissions, THEN THE GitHub_API_Client SHALL return an error indicating insufficient permissions
4. WHEN a rate limit is encountered, THE GitHub_API_Client SHALL retry with exponential backoff up to 3 attempts
5. THE Run_Context response SHALL include the run_url as an Evidence_Link

### Requirement 3: Baseline Run Discovery

**User Story:** As a developer, I want to find the last successful run on the same workflow and branch, so that I have a comparison baseline.

#### Acceptance Criteria

1. WHEN find_last_successful_run is called with valid owner, repo, workflow, and branch, THE GitHub_API_Client SHALL return the most recent run with conclusion "success"
2. THE Baseline_Run response SHALL include last_successful_run_id, base_sha, timestamp, and run_url
3. IF no successful run exists for the workflow and branch, THEN THE GitHub_API_Client SHALL return a response indicating no baseline found
4. THE Baseline_Run response SHALL include the run_url as an Evidence_Link
5. WHEN the workflow parameter is a name, THE GitHub_API_Client SHALL resolve it to the workflow_id before querying

### Requirement 4: Reference Comparison

**User Story:** As a developer, I want to see what changed between the last successful run and the failed run, so that I can identify potential culprits.

#### Acceptance Criteria

1. WHEN compare_refs is called with valid owner, repo, base_sha, and head_sha, THE GitHub_API_Client SHALL return a list of commits and changed files
2. THE compare_refs response SHALL include for each commit: sha, message, and url
3. THE compare_refs response SHALL include for each changed file: filename and status (added, modified, removed, renamed)
4. THE compare_refs response SHALL include the compare_url as an Evidence_Link
5. IF base_sha equals head_sha, THEN THE GitHub_API_Client SHALL return an empty comparison indicating no changes

### Requirement 5: Interest File Diff Extraction

**User Story:** As a developer, I want to see detailed diffs for high-signal files only, so that I can focus on likely culprits without noise.

#### Acceptance Criteria

1. WHEN diff_interest_files is called, THE GitHub_API_Client SHALL filter changed files against the provided Interest_Pattern list
2. THE default Interest_Pattern list SHALL include: .github/workflows/**, **/package-lock.json, **/yarn.lock, **/pnpm-lock.yaml, **/poetry.lock, **/requirements*.txt, **/go.sum, **/Cargo.lock, **/pom.xml, **/build.gradle*, **/Dockerfile*, **/Makefile, **/.tool-versions, **/.nvmrc, **/.python-version, **/.ruby-version, **/terraform.lock.hcl, **/Pulumi.yaml, **/cdk.json, **/.spacelift/**
3. WHEN a file matches an Interest_Pattern, THE GitHub_API_Client SHALL retrieve the diff content up to max_bytes_per_file
4. THE diff_interest_files response SHALL include for each file: filename, change_summary (human-readable), and evidence_url
5. IF a file diff exceeds max_bytes_per_file, THEN THE GitHub_API_Client SHALL truncate the diff and indicate truncation in the change_summary

### Requirement 6: Deterministic Risk Ranking

**User Story:** As a developer, I want changes ranked by their likelihood of causing the CI failure, so that I can investigate the most probable culprits first.

#### Acceptance Criteria

1. WHEN rank_changes_by_risk is called with run_context, changed_files, and diff_summaries, THE Risk_Scorer SHALL produce a ranked list of Suspects
2. THE Risk_Scorer SHALL apply the following baseline weights: workflow YAML changed (+6), lockfile changed (+5), runner or toolchain drift (+5), build scripts changed (+4), Dockerfile/base image change (+3), caching config changed (+3), permissions/secrets scope changed (+2), tests-only changes (+1)
3. THE Risk_Scorer SHALL never rank a Suspect without at least one Evidence_Link
4. IF only low-risk changes exist (all scores ≤ 2), THEN THE Risk_Scorer SHALL explicitly state "insufficient evidence to identify likely culprits"
5. THE Risk_Scorer SHALL prefer fewer, high-confidence Suspects over many low-confidence ones
6. THE ranked_suspects response SHALL include for each Suspect: category, score, rationale, and evidence_urls array

### Requirement 7: Structured Output Contract

**User Story:** As a developer, I want consistent, structured output from the analysis, so that I can reliably parse and act on the results.

#### Acceptance Criteria

1. THE MCP_Server final analysis response SHALL include: failed_run_url, last_successful_run_url, base_sha, head_sha, top_suspects (1-3 ranked), evidence_links per suspect, what_did_not_change, and unknowns_or_missing_signals
2. WHEN generating the response, THE MCP_Server SHALL include the "what did not change" section listing unchanged high-signal areas
3. WHEN generating the response, THE MCP_Server SHALL include an "unknowns" section for missing signals or incomplete data
4. THE MCP_Server SHALL never include a suspect without at least one Evidence_Link
5. IF the analysis cannot determine any suspects, THEN THE MCP_Server SHALL return a response stating "insufficient evidence" with available Evidence_Links

### Requirement 8: Security and Safety

**User Story:** As a developer, I want the server to enforce read-only access and protect sensitive data, so that my repositories remain secure.

#### Acceptance Criteria

1. THE GitHub_API_Client SHALL only use GitHub API endpoints that require read permissions (repo read, actions read)
2. THE MCP_Server SHALL never call GitHub API endpoints that modify repository state
3. WHEN log output is enabled, THE MCP_Server SHALL redact any detected secrets or tokens from log messages
4. THE MCP_Server SHALL validate all inputs against injection attacks before constructing API requests
5. WHEN rate limits are encountered, THE GitHub_API_Client SHALL implement exponential backoff with jitter, maximum 3 retries

### Requirement 9: Error Handling

**User Story:** As a developer, I want clear error messages when something goes wrong, so that I can understand and resolve issues.

#### Acceptance Criteria

1. IF a GitHub API request fails, THEN THE GitHub_API_Client SHALL return an error with the HTTP status code and error message
2. IF authentication fails, THEN THE MCP_Server SHALL return an error indicating invalid or expired PAT
3. IF a required input parameter is missing, THEN THE MCP_Server SHALL return an error listing the missing parameters
4. IF the comparison between refs fails, THEN THE MCP_Server SHALL return an error with the specific failure reason and any partial data retrieved
5. WHEN an error occurs, THE MCP_Server SHALL include any available Evidence_Links that may help diagnose the issue

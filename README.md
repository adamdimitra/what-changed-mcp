# whatchanged-mcp

A read-only Python MCP server for GitHub Actions CI failure analysis.

## Installation

```bash
poetry install
```

## Usage

Set your GitHub token:

```bash
export GITHUB_TOKEN=your_pat_here
```

Run the server:

```bash
poetry run whatchanged-mcp
```

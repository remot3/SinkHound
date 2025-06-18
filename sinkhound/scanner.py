"""Core scanning functionality."""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional

from git import Repo


def _log(message: str, enabled: bool) -> None:
    """Print a log message when logging is enabled."""
    if enabled:
        print(message)


from .sinks import SinkConfig, SinkRule


def clone_repo(url: str, branch: str, log_steps: bool) -> Repo:
    """Clone the repository and return the Repo object."""
    _log(f"Cloning repository {url} (branch {branch})", log_steps)
    temp_dir = tempfile.mkdtemp(prefix="sinkhound-")
    repo = Repo.clone_from(url, temp_dir, branch=branch)
    return repo


from itertools import islice


def iter_commits(repo: Repo, branch: str, max_count: Optional[int] = None) -> Iterable:
    commits = repo.iter_commits(branch, reverse=True)
    if max_count is not None and max_count > 0:
        commits = islice(commits, max_count)
    return commits


from dataclasses import dataclass


@dataclass
class ScanMatch:
    """Details about a single sink match."""

    path: str
    line: str
    description: str
    risk: int


def scan_commit(
    commit, rules: List[SinkRule], include_ext: Optional[List[str]] = None
) -> List[ScanMatch]:
    """Scan a commit and return matching lines."""
    matches: List[ScanMatch] = []
    parents = commit.parents
    if not parents:
        return matches
    diff = parents[0].diff(commit, create_patch=True)
    for diff_item in diff:

        if include_ext:
            b_path = diff_item.b_path
            if b_path is None or not any(b_path.endswith(ext) for ext in include_ext):
                continue
        for line in diff_item.diff.decode("utf-8", errors="ignore").splitlines():
            if not line.startswith("+"):
                continue
            for rule in rules:
                if re.search(rule.pattern, line):
                    matches.append(
                        ScanMatch(
                            path=diff_item.b_path,
                            line=line[1:].strip(),
                            description=rule.description,
                            risk=rule.risk,
                        )
                    )
    return matches


def scan_repository(
    repo_url: str,
    branch: str,
    sink_file: Path,
    include_ext: Optional[List[str]] = None,
    silent: bool = False,
    commit_limit: Optional[int] = None,
) -> None:
    log_steps = not silent
    repo = clone_repo(repo_url, branch, log_steps)
    _log(f"Loading sinks from {sink_file}", log_steps)
    cfg = SinkConfig(sink_file)
    COLOR_RESET = "\033[0m"
    COLOR_COMMIT = "\033[36m"
    COLOR_LINE = "\033[33m"

    printed_output = False
    for commit in iter_commits(repo, branch, commit_limit):
        if log_steps and not printed_output:
            _log(f"Scanning commit {commit.hexsha}", log_steps)

        matches = scan_commit(commit, cfg.rules, include_ext=include_ext)

        if matches:
            if log_steps and not printed_output:
                # separate progress logs from results
                printed_output = True
                print("")
            print(
                f"{COLOR_COMMIT}Commit {commit.hexsha}: {commit.summary}{COLOR_RESET}"
            )
            for m in matches:
                print(f"  {m.path} -> {m.description}")
                print(f"    {COLOR_LINE}{m.line}{COLOR_RESET}")

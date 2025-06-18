"""Core scanning functionality."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, List

from git import Repo

from .sinks import SinkConfig, SinkRule


def clone_repo(url: str, branch: str) -> Repo:
    temp_dir = tempfile.mkdtemp(prefix="sinkhound-")
    repo = Repo.clone_from(url, temp_dir, branch=branch)
    return repo


def iter_commits(repo: Repo, branch: str) -> Iterable:
    return repo.iter_commits(branch, reverse=True)


def scan_commit(commit, rules: List[SinkRule]) -> List[str]:
    """Scan a commit and return matching lines."""
    matches = []
    parents = commit.parents
    if not parents:
        return matches
    diff = parents[0].diff(commit, create_patch=True)
    for diff_item in diff:
        for line in diff_item.diff.decode("utf-8", errors="ignore").splitlines():
            if not line.startswith("+"):
                continue
            for rule in rules:
                if re.search(rule.pattern, line):
                    matches.append(
                        f"{commit.hexsha[:7]} {diff_item.b_path}: {line[1:].strip()}"
                    )
    return matches


def scan_repository(repo_url: str, branch: str, sink_file: Path) -> None:
    repo = clone_repo(repo_url, branch)
    cfg = SinkConfig(sink_file)
    for commit in iter_commits(repo, branch):
        matches = scan_commit(commit, cfg.rules)
        if matches:
            print(f"Commit {commit.hexsha}: {commit.summary}")
            for m in matches:
                print(f"  {m}")


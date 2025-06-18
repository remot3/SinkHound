"""Core scanning functionality."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional

from git import Repo

from .sinks import SinkConfig, SinkRule


def clone_repo(url: str, branch: str) -> Repo:
    temp_dir = tempfile.mkdtemp(prefix="sinkhound-")
    repo = Repo.clone_from(url, temp_dir, branch=branch)
    return repo


def iter_commits(repo: Repo, branch: str) -> Iterable:
    return repo.iter_commits(branch, reverse=True)


from dataclasses import dataclass


@dataclass
class ScanMatch:
    """Details about a single sink match."""

    path: str
    line: str
    description: str
    risk: int



def scan_commit(commit, rules: List[SinkRule], include_ext: Optional[List[str]] = None) -> List[ScanMatch]:

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

) -> None:
    repo = clone_repo(repo_url, branch)
    cfg = SinkConfig(sink_file)
    for commit in iter_commits(repo, branch):

        matches = scan_commit(commit, cfg.rules, include_ext=include_ext)

        if matches:
            print(f"Commit {commit.hexsha}: {commit.summary}")
            for m in matches:
                print(
                    f"  {m.path} -> {m.description} (risk {m.risk})\n    {m.line}"
                )


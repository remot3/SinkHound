from pathlib import Path
import tempfile

from git import Repo

from sinkhound.sinks import SinkConfig
from sinkhound.scanner import iter_commits, scan_commit, ScanMatch


def create_repo() -> Path:
    tmp = Path(tempfile.mkdtemp())
    repo = Repo.init(tmp)
    (tmp / "a.py").write_text("print('hello')\n")
    repo.index.add(["a.py"])
    repo.index.commit("initial commit")
    (tmp / "a.py").write_text("eval('danger')\n")
    repo.index.add(["a.py"])
    repo.index.commit("add eval")
    return tmp


def test_scan_detects_eval():
    repo_path = create_repo()
    repo = Repo(repo_path)
    cfg = SinkConfig(Path("sinks/php.yml"))
    commits = list(iter_commits(repo, "master"))
    found = False
    for commit in commits:
        matches = scan_commit(commit, cfg.rules)
        if any(m.description == "Usage of eval function" for m in matches):
            found = True
            break
    assert found


def test_include_extension_filters_files():
    repo_path = create_repo()
    repo = Repo(repo_path)
    cfg = SinkConfig(Path("sinks/php.yml"))
    commits = list(iter_commits(repo, "master"))
    target_commit = commits[-1]
    matches = scan_commit(target_commit, cfg.rules, include_ext=[".js"])
    assert matches == []


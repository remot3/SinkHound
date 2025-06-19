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


def create_repo_file_reads() -> Path:
    tmp = Path(tempfile.mkdtemp())
    repo = Repo.init(tmp)
    (tmp / "a.php").write_text('<?php\n$content = file_get_contents("test.txt");\n')
    repo.index.add(["a.php"])
    repo.index.commit("initial commit")
    (tmp / "a.php").write_text("<?php\n$content = file_get_contents($file);\n")
    repo.index.add(["a.php"])
    repo.index.commit("use variable input")
    return tmp


def create_repo_with_deletion() -> Path:
    tmp = Path(tempfile.mkdtemp())
    repo = Repo.init(tmp)
    (tmp / "a.php").write_text("<?php\necho 'hello';\n")
    repo.index.add(["a.php"])
    repo.index.commit("initial commit")
    (tmp / "a.php").unlink()
    repo.index.remove(["a.php"])
    repo.index.commit("remove file")
    return tmp


def create_repo_includes() -> Path:
    tmp = Path(tempfile.mkdtemp())
    repo = Repo.init(tmp)
    (tmp / "a.php").write_text("<?php\ninclude 'test.php';\n")
    repo.index.add(["a.php"])
    repo.index.commit("initial commit")
    (tmp / "a.php").write_text("<?php\ninclude($file);\n")
    repo.index.add(["a.php"])
    repo.index.commit("use variable include")
    return tmp


def create_repo_exec() -> Path:
    tmp = Path(tempfile.mkdtemp())
    repo = Repo.init(tmp)
    (tmp / "a.php").write_text("<?php\nexec('ls');\n")
    repo.index.add(["a.php"])
    repo.index.commit("initial commit")
    (tmp / "a.php").write_text("<?php\nexec($cmd);\n")
    repo.index.add(["a.php"])
    repo.index.commit("use variable exec")
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


def test_dynamic_file_read_flagged():
    repo_path = create_repo_file_reads()
    repo = Repo(repo_path)
    cfg = SinkConfig(Path("sinks/php.yml"))
    commits = list(iter_commits(repo, "master"))
    results = [scan_commit(c, cfg.rules) for c in commits]
    assert not results[0]
    assert results[1]


def test_deleted_files_are_ignored_with_include_ext():
    repo_path = create_repo_with_deletion()
    repo = Repo(repo_path)
    cfg = SinkConfig(Path("sinks/php.yml"))
    commits = list(iter_commits(repo, "master"))
    target_commit = commits[-1]

    matches = scan_commit(target_commit, cfg.rules, include_ext=[".php"])
    assert matches == []


def test_dynamic_include_flagged():
    repo_path = create_repo_includes()
    repo = Repo(repo_path)
    cfg = SinkConfig(Path("sinks/php.yml"))
    commits = list(iter_commits(repo, "master"))
    results = [scan_commit(c, cfg.rules) for c in commits]
    assert not results[0]
    assert results[1]


def test_dynamic_exec_flagged():
    repo_path = create_repo_exec()
    repo = Repo(repo_path)
    cfg = SinkConfig(Path("sinks/php.yml"))
    commits = list(iter_commits(repo, "master"))
    results = [scan_commit(c, cfg.rules) for c in commits]
    assert not results[0]
    assert results[1]


def test_iter_commits_respects_limit():
    repo_path = create_repo()
    repo = Repo(repo_path)
    commits = list(iter_commits(repo, "master", max_count=1))
    assert len(commits) == 1

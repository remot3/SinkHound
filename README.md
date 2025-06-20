# SinkHound

SinkHound is a security focused tool that scans the commit history of a Git repository to detect dangerous functions or code patterns known as *sinks*. Unlike traditional static analyzers that operate on the current code base, SinkHound inspects the diffs of every commit so you can trace when risky code was introduced.

## Features

- **Commit-aware sink tracing** – scans added lines in each commit
- **Customizable rule sets** – define sinks in YAML with descriptions and risk scores
- **Human-readable output** – shows the commit, sink description and offending line
- **File extension filtering** – only process files with certain extensions using `--include-ext`
- **Commit range limiting** – scan only the last N commits using `--commits`

- **Multi-format reporting** – console output today, JSON/HTML in the future

## Quick start

```bash
# install the command line interface
pip install .

# run a scan using the installed `sinkhound` command

sinkhound scan --sinks sinks/php.yml --branch main --repo https://github.com/codingo/NoSQLMap --include-ext php,yaml

# limit to last 100 commits
sinkhound scan --sinks sinks/php.yml --branch main --repo https://github.com/codingo/NoSQLMap --include-ext php,yaml -c 100

```

The command above will clone the repository, iterate over its commits and report any lines matching the sink rules defined in `sinks/php.yml`.


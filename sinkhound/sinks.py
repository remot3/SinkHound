"""Utilities for loading sink definitions from YAML."""

from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml


@dataclass
class SinkRule:
    pattern: str
    description: str
    risk: int


class SinkConfig:
    """Loads sink rules from a YAML file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.rules: List[SinkRule] = []
        self.load()

    def load(self) -> None:
        data = yaml.safe_load(self.path.read_text())
        for item in data.get("sinks", []):
            self.rules.append(
                SinkRule(
                    pattern=item.get("pattern"),
                    description=item.get("description", ""),
                    risk=int(item.get("risk", 0)),
                )
            )


import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class MonitorTarget:
    url: str
    variant_name: str
    label: str = ""

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.variant_name

    @property
    def state_key(self) -> str:
        return f"{self.url}::{self.variant_name}"


@dataclass
class AppConfig:
    targets: list[MonitorTarget]
    check_interval_sec: int = 600


def load_config(path: str | None = None) -> AppConfig:
    """YAML 設定ファイルを読み込む。"""
    config_path = path or os.getenv("CONFIG_PATH", "config.yaml")
    raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))

    targets = [MonitorTarget(**t) for t in raw["targets"]]
    if not targets:
        raise ValueError("targets が空です。監視対象を1つ以上設定してください。")

    return AppConfig(
        targets=targets,
        check_interval_sec=raw.get("check_interval_sec", 600),
    )

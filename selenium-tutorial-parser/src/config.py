# ruff: noqa: F401
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

__all__ = [
    "get_root_output_dir",
    "get_medias",
    "get_section_to_focus",
    "get_section_to_stop",
    "get_obs_path",
]

CONFIG_FILE = "config.json"

load_dotenv()


@dataclass
class Config:
    root_output_dir: str
    medias: tuple[str, ...]
    section_to_focus: tuple[tuple[str, ...], ...]
    section_to_stop: tuple[tuple[str, ...], ...]
    obs_path: str


def get_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_root_output_dir() -> Path:
    return Path(Config(**get_config()).root_output_dir)


def get_medias() -> tuple[str, ...]:
    return Config(**get_config()).medias


def get_section_to_focus() -> tuple[tuple[str, ...], ...]:
    return Config(**get_config()).section_to_focus


def get_section_to_stop() -> tuple[tuple[str, ...], ...]:
    return Config(**get_config()).section_to_stop


def get_obs_path() -> str:
    return Config(**get_config()).obs_path


if __name__ == "__main__":
    pass

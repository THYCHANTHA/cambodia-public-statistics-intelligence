"""Project paths and YAML configuration loaders."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIGS = ROOT / "configs"
CACHE_DIR = ROOT / "data" / "cache"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "reports" / "validation"
DB_PATH = PROCESSED_DIR / "cpsi.duckdb"

# Observation window requested from the API (validated in Phase 2).
START_YEAR = 1960
END_YEAR = 2025


def _load(name: str):
    return yaml.safe_load((CONFIGS / name).read_text(encoding="utf-8"))


def load_countries() -> list[dict]:
    return _load("countries.yaml")["countries"]


def load_indicators() -> list[dict]:
    """Flat list of indicator entries, each with its domain."""
    out = []
    for domain, items in _load("indicators.yaml")["domains"].items():
        for item in items:
            out.append({**item, "domain": domain})
    return out


def load_units() -> dict[str, dict]:
    return _load("units.yaml")["units"]

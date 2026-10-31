import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "app")]

from components.domain_page import render_domain  # noqa: E402

render_domain('Agriculture and Employment', "National indicators for agriculture's weight in the economy, land use and labour. Crop-level production is out of scope here.", ['agriculture_employment'], 'agri', '🌾')

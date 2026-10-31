import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "app")]

from components.domain_page import render_domain  # noqa: E402

render_domain('Demographics and Population', 'Population size, growth and urbanisation.', ['demographics'], 'demo', '👥')

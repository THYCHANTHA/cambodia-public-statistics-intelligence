import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "app")]

from components.domain_page import render_domain  # noqa: E402

render_domain('Economic Development', "Output, growth, prices and trade: how Cambodia's economy has developed and how it compares.", ['economy'], 'econ', '💹')

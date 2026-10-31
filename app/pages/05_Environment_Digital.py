import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "app")]

from components.domain_page import render_domain  # noqa: E402

render_domain('Environment, Energy and Digital Development', 'Electricity access, renewable energy, CO2 emissions per capita and internet use.', ['environment_digital'], 'env', '🔌')

"""Refresh command: download (cache-aware) then rebuild the database and reports.

    python scripts/run_pipeline.py            # reuse cached API responses, rebuild the database
    python scripts/run_pipeline.py --refresh  # re-download everything from the World Bank API first
    python scripts/run_pipeline.py --offline  # never touch the network
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv: list[str]) -> int:
    for script, args in (("download_data.py", argv), ("build_database.py", [])):
        code = subprocess.call([sys.executable, str(HERE / script), *args])
        if code:
            print(f"{script} failed with exit code {code}", file=sys.stderr)
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

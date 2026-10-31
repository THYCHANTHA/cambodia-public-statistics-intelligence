"""Download the curated catalogue (countries, indicator metadata, observations) into the raw-response cache.

Only the indicators in configs/indicators.yaml and the countries in configs/countries.yaml are requested.
Cached responses are reused; pass --refresh to re-download, --offline to forbid network access.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cpsi.config import CACHE_DIR, END_YEAR, START_YEAR, load_countries, load_indicators  # noqa: E402
from cpsi.ingestion.world_bank import WorldBankClient, WorldBankError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true", help="ignore the cache and re-download")
    ap.add_argument("--offline", action="store_true", help="use cached responses only")
    ap.add_argument("--metadata-only", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    client = WorldBankClient(CACHE_DIR, offline=args.offline)
    iso3 = [c["iso3"] for c in load_countries()]
    failures = []

    def run(label, fn):
        try:
            fn()
            print("ok  ", label, flush=True)
        except WorldBankError as exc:
            failures.append((label, str(exc)))
            print("FAIL", label, exc, flush=True)

    run("countries", lambda: client.countries(iso3, refresh=args.refresh))
    for ind in load_indicators():
        code = ind["code"]
        run(f"metadata {code}", lambda c=code: client.indicator_metadata(c, refresh=args.refresh))
        if not args.metadata_only:
            run(
                f"observations {code}",
                lambda c=code: client.observations(iso3, c, START_YEAR, END_YEAR, refresh=args.refresh),
            )
    print(f"network calls made: {client.calls}; failures: {len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

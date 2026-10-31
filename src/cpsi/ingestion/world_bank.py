"""World Bank Indicators API v2 client: pagination, timeouts, retries, response validation, raw-response cache.

Every API call result is stored as a JSON "bundle" (url, params, retrieved_at, all pages) so that the raw
response, not only the processed table, stays inspectable. Cached bundles are reused unless refresh=True.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import requests

log = logging.getLogger(__name__)

BASE_URL = "https://api.worldbank.org/v2"
RETRY_STATUS = {429, 500, 502, 503, 504}


class WorldBankError(Exception):
    """Invalid response, API-reported error, or exhausted retries."""


class OfflineCacheMiss(WorldBankError):
    """Offline mode was requested and the response is not cached."""


def validate_payload(payload) -> tuple[dict, list]:
    """Return (paging_header, records) or raise WorldBankError.

    The API answers HTTP 200 with ``[{"message": [...]}]`` for errors such as an unknown indicator,
    and with ``[header, null]`` when a query matches nothing.
    """
    if not isinstance(payload, list) or not payload:
        raise WorldBankError(f"unexpected payload type: {type(payload).__name__}")
    head = payload[0]
    if not isinstance(head, dict):
        raise WorldBankError("first element of payload is not an object")
    if "message" in head:
        raise WorldBankError(f"API error: {json.dumps(head['message'])[:300]}")
    if len(payload) != 2:
        raise WorldBankError(f"expected [header, records], got {len(payload)} elements")
    for key in ("page", "pages", "per_page", "total"):
        if key not in head:
            raise WorldBankError(f"paging header lacks '{key}'")
    records = payload[1]
    if records is None:
        records = []
    if not isinstance(records, list):
        raise WorldBankError("records element is not a list")
    return head, records


class WorldBankClient:
    def __init__(
        self,
        cache_dir: Path,
        *,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 4,
        backoff: float = 1.5,
        offline: bool = False,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.cache_dir = Path(cache_dir)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.offline = offline
        self.session = session or requests.Session()
        self.sleep = sleep
        self.calls = 0  # network calls actually made (cache hits excluded)

    # ---- low level ----
    def _get_json(self, url: str, params: dict):
        last: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                self.calls += 1
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code in RETRY_STATUS:
                    last = WorldBankError(f"HTTP {resp.status_code}")
                elif resp.status_code != 200:
                    raise WorldBankError(f"HTTP {resp.status_code} for {url}")
                else:
                    try:
                        return resp.json()
                    except ValueError as exc:
                        last = WorldBankError(f"invalid JSON: {exc}")
            except (requests.Timeout, requests.ConnectionError) as exc:
                last = exc
            if attempt < self.max_retries:
                delay = self.backoff * (2**attempt)
                log.warning("retry %d/%d for %s after %s (sleep %.1fs)",
                            attempt + 1, self.max_retries, url, last, delay)
                self.sleep(delay)
        raise WorldBankError(f"giving up on {url} after {self.max_retries + 1} attempts: {last}")

    def _cache_path(self, path: str, params: dict) -> Path:
        key = json.dumps({"path": path, "params": params}, sort_keys=True)
        digest = hashlib.sha256(key.encode()).hexdigest()[:16]
        safe = path.strip("/").replace("/", "_").replace(";", "+")[:60]
        return self.cache_dir / f"{safe}__{digest}.json"

    # ---- public ----
    def fetch(self, path: str, params: dict | None = None, *, refresh: bool = False) -> dict:
        """Fetch every page of ``path`` and return the bundle. Uses/updates the cache."""
        params = {**(params or {}), "format": "json"}
        cache_file = self._cache_path(path, params)
        if cache_file.exists() and not refresh:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        if self.offline:
            raise OfflineCacheMiss(f"offline mode and no cached response for {path} {params}")

        url = f"{self.base_url}/{path.lstrip('/')}"
        pages: list = []
        head, _ = validate_payload(first := self._get_json(url, params))
        pages.append(first)
        total_pages = int(head["pages"])
        for page in range(2, total_pages + 1):
            payload = self._get_json(url, {**params, "page": page})
            h, _ = validate_payload(payload)
            if int(h["page"]) != page:
                raise WorldBankError(f"asked for page {page}, got {h['page']}")
            pages.append(payload)
        n_records = sum(len(validate_payload(p)[1]) for p in pages)
        if n_records != int(head["total"]):
            raise WorldBankError(f"record count {n_records} != header total {head['total']} for {path}")

        bundle = {
            "url": url,
            "params": params,
            "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "pages": pages,
        }
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = cache_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(bundle), encoding="utf-8")
        tmp.replace(cache_file)
        return bundle

    @staticmethod
    def records(bundle: dict) -> list:
        out: list = []
        for page in bundle["pages"]:
            out.extend(validate_payload(page)[1])
        return out

    def countries(self, iso3: list[str], **kw) -> dict:
        return self.fetch(f"country/{';'.join(iso3)}", {"per_page": 100}, **kw)

    def indicator_metadata(self, code: str, **kw) -> dict:
        return self.fetch(f"indicator/{code}", {"per_page": 10}, **kw)

    def observations(self, iso3: list[str], code: str, start: int, end: int, per_page: int = 1000, **kw) -> dict:
        return self.fetch(
            f"country/{';'.join(iso3)}/indicator/{code}",
            {"per_page": per_page, "date": f"{start}:{end}"},
            **kw,
        )

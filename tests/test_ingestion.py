"""Offline tests for the World Bank client (mocked HTTP: deterministic, no network)."""

from __future__ import annotations

import pytest
import requests

from cpsi.ingestion.world_bank import OfflineCacheMiss, WorldBankClient, WorldBankError, validate_payload


class FakeResp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status

    def json(self):
        if isinstance(self._p, Exception):
            raise self._p
        return self._p


class FakeSession:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, dict(params or {}), timeout))
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def page(n, pages, total, rows):
    return [{"page": n, "pages": pages, "per_page": 2, "total": total}, rows]


def client(tmp_path, responses, **kw):
    s = FakeSession(responses)
    return WorldBankClient(tmp_path, session=s, sleep=lambda _: None, **kw), s


def test_pagination_collects_all_pages(tmp_path):
    c, s = client(tmp_path, [FakeResp(page(1, 2, 3, [{"a": 1}, {"a": 2}])), FakeResp(page(2, 2, 3, [{"a": 3}]))])
    b = c.fetch("country/KHM/indicator/X")
    assert [r["a"] for r in c.records(b)] == [1, 2, 3]
    assert s.calls[1][1]["page"] == 2
    assert all(call[2] == c.timeout for call in s.calls)


def test_cache_prevents_second_network_call(tmp_path):
    c, s = client(tmp_path, [FakeResp(page(1, 1, 1, [{"a": 1}]))])
    first = c.fetch("indicator/X")
    again = c.fetch("indicator/X")
    assert c.calls == 1 and first == again


def test_refresh_bypasses_cache(tmp_path):
    c, _ = client(tmp_path, [FakeResp(page(1, 1, 1, [{"a": 1}])), FakeResp(page(1, 1, 1, [{"a": 2}]))])
    c.fetch("indicator/X")
    assert c.records(c.fetch("indicator/X", refresh=True))[0]["a"] == 2


def test_offline_cache_miss_raises(tmp_path):
    c, s = client(tmp_path, [], offline=True)
    with pytest.raises(OfflineCacheMiss):
        c.fetch("indicator/X")
    assert not s.calls


def test_retry_on_503_then_success(tmp_path):
    c, s = client(tmp_path, [FakeResp({}, 503), FakeResp({}, 429), FakeResp(page(1, 1, 1, [{"a": 1}]))])
    assert c.records(c.fetch("indicator/X")) == [{"a": 1}]
    assert len(s.calls) == 3


def test_retry_on_timeout_then_giveup(tmp_path):
    c, s = client(tmp_path, [requests.Timeout("t")] * 3, max_retries=2)
    with pytest.raises(WorldBankError, match="giving up"):
        c.fetch("indicator/X")
    assert len(s.calls) == 3


def test_non_retryable_status_fails_immediately(tmp_path):
    c, s = client(tmp_path, [FakeResp({}, 404)])
    with pytest.raises(WorldBankError, match="404"):
        c.fetch("indicator/X")
    assert len(s.calls) == 1


def test_invalid_json_is_retried_then_fails(tmp_path):
    c, _ = client(tmp_path, [FakeResp(ValueError("bad"))] * 2, max_retries=1)
    with pytest.raises(WorldBankError, match="invalid JSON"):
        c.fetch("indicator/X")


def test_api_error_message_for_invalid_indicator(tmp_path):
    msg = [{"message": [{"id": "175", "key": "Invalid format", "value": "The indicator was not found."}]}]
    c, _ = client(tmp_path, [FakeResp(msg)])
    with pytest.raises(WorldBankError, match="not found"):
        c.fetch("country/KHM/indicator/NOPE")


def test_empty_result_is_valid_and_empty(tmp_path):
    c, _ = client(tmp_path, [FakeResp([{"page": 1, "pages": 0, "per_page": 50, "total": 0}, None])])
    assert c.records(c.fetch("country/KHM/indicator/X")) == []


def test_record_count_must_match_header_total(tmp_path):
    c, _ = client(tmp_path, [FakeResp(page(1, 1, 5, [{"a": 1}]))])
    with pytest.raises(WorldBankError, match="record count"):
        c.fetch("indicator/X")


def test_wrong_page_number_detected(tmp_path):
    c, _ = client(tmp_path, [FakeResp(page(1, 2, 3, [{}, {}])), FakeResp(page(1, 2, 3, [{}]))])
    with pytest.raises(WorldBankError, match="asked for page 2"):
        c.fetch("indicator/X")


@pytest.mark.parametrize("bad", [None, {}, [], "x", [[1], []], [{"page": 1}, []], [{"page": 1, "pages": 1, "per_page": 1, "total": 1}]])
def test_validate_payload_rejects_malformed(bad):
    with pytest.raises(WorldBankError):
        validate_payload(bad)

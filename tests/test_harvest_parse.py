from chainvalley.orchestrator import parse_harvest_decision


def test_parse_harvest_decision_valid() -> None:
    text = '{"harvest": 3, "note": "testing"}'
    assert parse_harvest_decision(text) == 3


def test_parse_harvest_decision_fenced() -> None:
    text = '```json\n{"harvest": 2}\n```'
    assert parse_harvest_decision(text) == 2


def test_parse_harvest_decision_over_quota_allowed() -> None:
    text = '{"harvest": 12}'
    assert parse_harvest_decision(text) == 12


def test_parse_harvest_decision_invalid() -> None:
    assert parse_harvest_decision("not json") is None

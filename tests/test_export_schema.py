import json

from chainvalley.export import RunRecord, run_record_to_json


def test_run_record_json_roundtrip() -> None:
    r = RunRecord(condition="soft", seed=1, rounds=[], transcripts=[], harvests=[], metrics={})
    s = run_record_to_json(r)
    assert json.loads(s)["condition"] == "soft"

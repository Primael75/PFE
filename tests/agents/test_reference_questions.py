"""Format checks for the reference questions (tests/agents/reference/)."""

import json
from collections import Counter
from pathlib import Path

QUESTIONS = Path(__file__).parent / "reference" / "questions.jsonl"
REPO = Path(__file__).parents[2]

REQUIRED = {
    "id": str,
    "axis": str,
    "question": str,
    "expected_answer": str,
    "expected_figures": list,
    "sources": list,
    "expected_tools": list,
    "refusal_expected": bool,
    "technician_referral": bool,
    "requirements": list,
}
AXES = {"diagnosis", "sowing", "markets", "coordinator"}
SENTINELS = {"uncertain", "off_topic"}


def load() -> list[dict]:
    lines = QUESTIONS.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_every_line_has_the_required_fields() -> None:
    for question in load():
        for field, kind in REQUIRED.items():
            assert isinstance(question.get(field), kind), (question.get("id"), field)
        assert question["axis"] in AXES, question["id"]


def test_ids_are_unique() -> None:
    ids = [question["id"] for question in load()]
    assert len(ids) == len(set(ids))


def test_comparison_set_covers_the_three_axes() -> None:
    comparison = [q for q in load() if q.get("set") == "comparison"]
    axes = Counter(question["axis"] for question in comparison)
    assert len(comparison) >= 10
    assert axes["sowing"] >= 3
    assert axes["markets"] >= 3


def test_every_answer_cites_a_source_or_refuses() -> None:
    for question in load():
        assert question["sources"] or question["refusal_expected"], question["id"]


def test_figures_have_unit_and_source() -> None:
    for question in load():
        for figure in question["expected_figures"]:
            assert figure["unit"] and figure["source"], question["id"]
            assert figure["value"] is not None or figure.get("to_fill"), question["id"]


def test_model_output_follows_diagnose_photo() -> None:
    for question in load():
        output = question.get("model_output")
        if output is None:
            continue
        assert set(output) == {"value", "uncertainty"}, question["id"]
        assert 0 <= output["uncertainty"] <= 1, question["id"]
        assert "_" in output["value"] or output["value"] in SENTINELS


def test_sheets_cited_exist() -> None:
    for question in load():
        for source in question["sources"]:
            if source.startswith("docs/plant-health/"):
                assert (REPO / source).is_file(), (question["id"], source)

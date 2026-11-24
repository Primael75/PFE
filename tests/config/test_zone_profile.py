"""Zone profiles: every brick reads them, so a typo must fail here, not later.

A misspelt commune gives an empty rainfall series without any error, hence
the checks on names and counts.
"""

from pathlib import Path

import pytest
import yaml

ZONES = Path(__file__).resolve().parents[2] / "config" / "zones"
PROFILES = sorted(ZONES.glob("*.yaml"))

CRITERION_FIELDS = {
    "name",
    "reference",
    "search_from",
    "search_to",
    "window_days",
    "window_threshold_mm",
    "check_days",
    "max_dry_spell_days",
    "wet_day_mm",
    "onset_day",
}
PROJECT_CROPS = {"maize", "sorghum", "cowpea", "cassava"}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def communes(profile: dict) -> list[str]:
    return [name for names in profile["communes"].values() for name in names]


def test_profiles_exist():
    assert [p.name for p in PROFILES] == ["zone-a.yaml"]


@pytest.mark.parametrize("path", PROFILES, ids=lambda p: p.stem)
def test_profile_id_matches_the_file_name(path):
    assert load(path)["zone"]["id"] == path.stem


@pytest.mark.parametrize("path", PROFILES, ids=lambda p: p.stem)
def test_communes_are_unique(path):
    names = communes(load(path))
    assert len(names) == len(set(names))


@pytest.mark.parametrize("path", PROFILES, ids=lambda p: p.stem)
def test_onset_criterion_is_complete(path):
    criterion = load(path)["onset_criterion"]
    assert set(criterion) == CRITERION_FIELDS
    assert criterion["onset_day"] in {"first_day_of_window", "threshold_day"}


@pytest.mark.parametrize("path", PROFILES, ids=lambda p: p.stem)
def test_crop_ranges_are_ordered(path):
    for crop in load(path)["crops"]:
        for key in ("water_need_mm", "optimal_ph"):
            low, high = crop[key]
            assert low <= high, f"{crop['id']} {key}"


@pytest.mark.parametrize("path", PROFILES, ids=lambda p: p.stem)
def test_sources_carry_a_licence(path):
    for name, source in load(path)["sources"].items():
        assert source.get("licence"), name


def test_zone_a_has_the_27_northern_communes():
    profile = load(ZONES / "zone-a.yaml")
    # The 8.7 N line gives exactly these four departments (27 communes).
    assert {d: len(n) for d, n in profile["communes"].items()} == {
        "Alibori": 6,
        "Atakora": 9,
        "Borgou": 8,
        "Donga": 4,
    }
    assert {"Segbana", "Kobli", "Parakou", "N'dali"} <= set(communes(profile))


def test_zone_a_has_the_four_project_crops():
    profile = load(ZONES / "zone-a.yaml")
    assert {crop["id"] for crop in profile["crops"]} == PROJECT_CROPS

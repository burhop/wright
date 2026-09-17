"""Check the additive human capability input and its recorded lineage, not CAD correctness."""

import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "tests/datasets/engineering-workflows"
SCENARIO = (
    INPUTS / "scenarios/sheet-metal-supplier-handoff/03-precision-instrument-chassis"
)
REVISION = (
    INPUTS
    / "revisions/2026-09-12-sheet-capabilities-r4/sheet-metal-supplier-handoff-03"
)
DOCK = INPUTS / "scenarios/sheet-metal-supplier-handoff/01-barcode-reader-wall-dock"
DOCK_REVISION = (
    INPUTS
    / "revisions/2026-09-12-sheet-capabilities-r4/sheet-metal-supplier-handoff-01"
)
TROUGH = INPUTS / "scenarios/sheet-metal-supplier-handoff/02-industrial-cable-trough"
TROUGH_REVISION = (
    INPUTS
    / "revisions/2026-09-12-sheet-capabilities-r4/sheet-metal-supplier-handoff-02"
)
TEXT_SUFFIXES = {".csv", ".json", ".md", ".svg", ".txt"}


def content_sha256(path: Path) -> str:
    """Hash Git text as LF while preserving byte identity for binary inputs."""
    content = path.read_bytes()
    if path.suffix.lower() in TEXT_SUFFIXES:
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


@pytest.mark.parametrize(
    "scenario,revision",
    [(SCENARIO, REVISION), (DOCK, DOCK_REVISION), (TROUGH, TROUGH_REVISION)],
    ids=["chassis", "wall-dock", "cable-trough"],
)
def test_r4_preserves_original_uploads_and_records_new_dataset_identity(
    scenario, revision
):
    ledger = json.loads((revision / "revision.json").read_text(encoding="utf-8"))

    assert (
        content_sha256(revision / "scenario.before.json")
        == ledger["original_manifest_sha256"]
    )
    assert (
        content_sha256(scenario / "scenario.json") == ledger["revised_manifest_sha256"]
    )
    assert content_sha256(scenario / ledger["addendum"]) == ledger["addendum_sha256"]
    assert all(
        content_sha256(scenario / name) == expected
        for name, expected in ledger["retained_original_files"].items()
    )
    before = json.loads((revision / "scenario.before.json").read_text(encoding="utf-8"))
    after = json.loads((scenario / "scenario.json").read_text(encoding="utf-8"))
    before["files"]["context"].append(ledger["addendum"])
    assert (
        after == before
    )  # No geometry, profile, output or supplier scope silently revised.
    spec = importlib.util.spec_from_file_location(
        "scripts.r4_campaign", ROOT / "scripts/engineering_dataset_campaign.py"
    )
    campaign = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(campaign)
    current = campaign.load_dataset(
        scenario / "scenario.json",
        INPUTS,
        json.loads((INPUTS / "campaign.json").read_text()),
    )
    assert (
        current["digest"] == ledger["dataset_digest"] != ledger["prior_dataset_digest"]
    )
    assert ledger["execution_started"] is False


def test_wall_dock_company_setup_has_consistent_clearances_and_retains_supplier_conflict():
    text = " ".join(
        (DOCK / "company-fabrication-capabilities-r4.md")
        .read_text(encoding="utf-8")
        .split()
    )
    # Check the authored numeric input against protected worst-case geometry;
    # this validates the policy's arithmetic, not an actual forming operation.
    assert "60+10=70 mm" in text
    assert "A 12 mm lip requires 22 mm" in text
    assert 60 + 10 < min(80, 90)
    assert 12 + 10 < 100
    assert 75 + 60 + 10 == 145 < 300
    assert 46 - 6 - 3 == 37 > 20
    assert "three planned press operations" in text
    assert all(
        label in text
        for label in ("F1: left front lip", "F2: right front lip", "R1: rear wall")
    )
    assert "no tool bridge across the cable opening" in text
    assert "not a swept-volume collision analysis" in text
    assert "not a replacement for stock revision R1" in text
    for boundary in [
        "A known applicable supplier hard-limit conflict still blocks",
        "Do not reclassify a hard requirement as a caution",
        "Do not claim that no geometry enters the caution region",
        "missing native evidence is unverified, never pass",
        "Do not count the two side-by-side front intervals as two successive bends",
        "the discrepancy is not excused as rounding or a dimensional tolerance",
        "Both exact supplier approval gates remain local simulations",
        "physical_fabrication=not_performed",
    ]:
        assert boundary in text
    # The prior attempt's selected T/R/K are historical arithmetic inputs only;
    # the company upload must require fresh evidence instead of freezing them.
    thickness, radius, k_factor = 0.063 * 25.4, 0.035 * 25.4, 0.42
    allowance = math.pi / 2 * (radius + k_factor * thickness)
    difference = 2 * (radius + thickness) - allowance - 0.096 * 25.4
    assert difference == pytest.approx(0.087854986982, abs=1e-12)
    assert all(value not in text for value in ("0.063", "0.035", "0.42", "0.096"))


def test_company_cut_table_is_consistent_at_upper_stock_bound_and_is_not_supplier_evidence():
    text = (SCENARIO / "company-fabrication-capabilities-r4.md").read_text(
        encoding="utf-8"
    )
    rows = [
        line.split("|")[1:-1]
        for line in text.splitlines()
        if re.search(r"\| [0-9.]+\*T \|", line)
    ]
    assert len(rows) == 4
    protected = {
        "Circular through-hole diameter": 3.4,
        "Through-slot width": 3.0,
        "Web between parallel cut edges": 5.0 - 3.0,
        "Hole/slot edge to an unbent free edge": 7.0 - 3.4 / 2,
    }
    for criterion, formula, stated, _feature in rows:
        multiplier = float(formula.strip().removesuffix("*T"))
        worst = float(stated.strip().removesuffix(" mm"))
        assert worst == pytest.approx(multiplier * 1.7)
        assert protected[criterion.strip()] > worst
    for boundary in [
        "Company limits do not establish supplier-compatible holes, webs or tool access",
        "known applicable supplier hard-limit conflict",
        "not a verified swept-volume",
        "mandatory in the existing measured-design and export",
        "supplier_acceptance=unverified",
        "No actual supplier upload",
    ]:
        assert boundary in " ".join(text.split())


def test_cable_trough_company_setup_closes_only_the_pre_cad_company_input_gap():
    text = " ".join(
        (TROUGH / "company-fabrication-capabilities-r4.md")
        .read_text(encoding="utf-8")
        .split()
    )
    assert 60 + 5 == 65 < 75
    assert 20 + 5 == 25 < 35
    assert 400 < 500
    assert 80 / 60 == pytest.approx(1.3333333333333333)
    for requirement in [
        "F1: left outward return",
        "F2: right outward return",
        "B1: left base-to-wall bend",
        "B2: right base-to-wall bend",
        "cad_input_status=ready_for_geometry_verification",
        "does not prove supplier tooling access",
        "Supplier-only confirmation gaps may remain downstream",
        "supplier_acceptance=unverified",
        "physical_fabrication=not_performed",
    ]:
        assert requirement in text
    manifest = json.loads((TROUGH / "scenario.json").read_text(encoding="utf-8"))
    assert manifest["files"]["context"][-1] == "company-fabrication-capabilities-r4.md"

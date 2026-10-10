"""Contract tests for the Grok X Revenue Builder skill (test-first)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "grok-x-revenue-builder"
SKILL = SKILL_DIR / "SKILL.md"
SCORECARD = SKILL_DIR / "references" / "revenue-scorecard.md"


def test_skill_exists_and_declares_invocation_contract():
    assert SKILL.is_file(), "missing Grok X Revenue Builder SKILL.md"
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: grok-x-revenue-builder" in text
    assert "description:" in text
    assert "When to use" in text
    assert "When not to use" in text


def test_skill_requires_evidence_not_invented_demand():
    text = SKILL.read_text(encoding="utf-8").lower()
    for phrase in ("source", "observed", "hypothesis", "do not invent", "evidence"):
        assert phrase in text


def test_skill_is_free_first_and_blocks_silent_paid_fallback():
    text = SKILL.read_text(encoding="utf-8").lower()
    assert "free-first" in text
    assert "paid" in text
    assert "approval" in text


def test_skill_preserves_human_approval_boundaries():
    text = SKILL.read_text(encoding="utf-8").lower()
    for phrase in ("public posts", "customer messages", "purchases", "production database"):
        assert phrase in text
    assert "live trading" in text


def test_skill_has_repeatable_revenue_workflow_and_scorecard():
    assert SCORECARD.is_file(), "missing revenue scorecard reference"
    text = SKILL.read_text(encoding="utf-8").lower()
    for phrase in ("demand", "qualify", "offer", "checkout", "delivery", "measure", "iterate"):
        assert phrase in text
    scorecard = SCORECARD.read_text(encoding="utf-8").lower()
    for phrase in ("evidence strength", "buyer urgency", "willingness to pay", "time to validate", "cost"):
        assert phrase in scorecard


def test_skill_does_not_claim_sales_without_verification():
    text = SKILL.read_text(encoding="utf-8").lower()
    assert "verified sale" in text
    assert "never claim revenue" in text

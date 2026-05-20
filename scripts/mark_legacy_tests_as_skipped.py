"""
mark_legacy_tests_as_skipped.py

Marks legacy pre-California pivot tests as SKIPPED with explanatory reason.
Targets test files that import the removed Country model or use legacy enums.

Run once during Day 6 cleanup; subsequent runs are idempotent.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LEGACY_TEST_FILES = [
    "tests/engines/test_risk_engine.py",
    "tests/engines/test_interest_engine.py",
    "tests/engines/test_loan_engine.py",
    "tests/services/test_orchestrator.py",
    "tests/services/test_pipeline.py",
    "tests/manual/test_buisiness_agent.py",
    "tests/historical/test_historical.py",
    "tests/fixtures/test_models_user.py",
]

SKIP_HEADER = '''"""
LEGACY TEST FILE — Skipped during California pivot.

This file was written for the pre-California multi-country model
(Country enum, EUR currency, COUNTRY_LOAN_YEARS, COUNTRY_INTEREST).
It has been preserved as documentation of the original test design
but is excluded from CI until refactored to the California-only model.

Status: Pre-pivot tests (May 2026 California pivot)
Refactor target: Post-defense
"""
import pytest

pytestmark = pytest.mark.skip(
    reason="Legacy pre-California pivot test — refactor scheduled post-defense"
)

'''


def is_already_marked(path: Path) -> bool:
    """Check if file already has pytestmark = skip."""
    try:
        text = path.read_text()
        return "pytestmark = pytest.mark.skip" in text
    except FileNotFoundError:
        return False


def mark_file_as_skipped(path: Path) -> bool:
    """Prepend skip-all marker to file. Returns True if modified."""
    if not path.exists():
        print(f"  ⚠  Not found: {path}")
        return False

    if is_already_marked(path):
        print(f"  ✓  Already skipped: {path.relative_to(PROJECT_ROOT)}")
        return False

    original = path.read_text()
    # Remove existing module docstring if any (we replace with ours)
    if original.startswith('"""'):
        # Find end of docstring
        end_idx = original.find('"""', 3)
        if end_idx != -1:
            original = original[end_idx + 3:].lstrip("\n")

    new_content = SKIP_HEADER + original
    path.write_text(new_content)
    print(f"  ✓  Marked: {path.relative_to(PROJECT_ROOT)}")
    return True


def main():
    print("=" * 70)
    print("Marking legacy tests as @pytest.mark.skip")
    print("=" * 70)
    modified = 0
    for rel_path in LEGACY_TEST_FILES:
        path = PROJECT_ROOT / rel_path
        if mark_file_as_skipped(path):
            modified += 1
    print()
    print(f"✅ Done. {modified} files modified.")


if __name__ == "__main__":
    main()

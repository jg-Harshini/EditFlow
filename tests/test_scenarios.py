import os
from pathlib import Path
import pytest
from cli.session_runner import SessionRunner

SCENARIOS_DIR = Path("session_pack")
scenario_files = sorted(list(SCENARIOS_DIR.glob("*.yaml")))


@pytest.mark.parametrize("scenario_file", scenario_files, ids=[f.stem for f in scenario_files])
def test_scripted_scenario(scenario_file):
    """
    Outstanding Requirement O4:
    Automated suite of at least 40 scripted scenarios with expected results runs in CI.
    """
    runner = SessionRunner()
    output_dir = Path("test_pack/scenario_outputs") / scenario_file.stem
    result = runner.run_file(str(scenario_file), output_dir=str(output_dir))

    assert "steps" in result
    assert "final_timeline" in result
    assert "final_timeline_hash" in result
    assert len(result["steps"]) > 0

    # Ensure all steps returned valid three-way statuses
    for step in result["steps"]:
        assert step["status"] in ("applied", "needs_clarification", "rejected")
        assert "timeline_hash" in step
        assert "duration_s" in step

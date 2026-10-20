#!/usr/bin/env python3
"""
Master Test Runner for Engineering Assessment 2
Executes unit tests, integration tests, worked example, hard cases, and all 42 scenarios.
Requires no external API keys.
"""

import os
import subprocess
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def run_all_tests():
    print("==================================================================")
    print(" Engineering Assessment 2 — Automated Verification Test Suite")
    print("==================================================================")

    # 1. Ensure test media exists
    print("\n[Step 1/3] Checking / generating synthetic test media assets...")
    try:
        from tests.generate_test_media import (
            generate_synthetic_audio,
            generate_synthetic_video,
        )
        generate_synthetic_video("test_pack/assets/interview.mp4", duration_s=225)
        generate_synthetic_video("test_pack/assets/short_test.mp4", duration_s=10)
        generate_synthetic_video("test_pack/assets/multispeaker.mp4", duration_s=150)
        generate_synthetic_audio("test_pack/assets/bg_music.mp3", duration_s=60)
        print("  -> Synthetic media assets verified.")
    except Exception as e:
        print(f"  -> Error generating media: {e}")
        return 1

    # 2. Run pytest across all test suites
    print("\n[Step 2/3] Running pytest (Unit, Anchoring, NLP, Worked Example, Hard Cases, API, OTIO)...")
    test_args = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_timeline_engine.py",
        "tests/test_content_anchoring.py",
        "tests/test_ambiguity_and_parser.py",
        "tests/test_worked_example.py",
        "tests/test_hard_cases.py",
        "tests/test_api_integration.py",
        "tests/test_otio_export.py",
        "tests/test_scenarios.py",
        "-v",
        "--tb=short",
    ]
    res_pytest = subprocess.run(test_args)
    if res_pytest.returncode != 0:
        print("\nPytest execution reported test failures.")
        return res_pytest.returncode

    # 3. Run Batch Runner CLI on all 42 scenarios
    print("\n[Step 3/3] Executing CLI Batch Runner across all 42 session scenarios...")
    batch_args = [
        sys.executable,
        "cli/batch_runner.py",
        "session_pack",
        "--output",
        "test_pack/batch_run_results",
    ]
    res_batch = subprocess.run(batch_args)
    if res_batch.returncode != 0:
        print("\nBatch runner reported test failures.")
        return res_batch.returncode

    print("\n==================================================================")
    print(" ALL TESTS & 42 SCRIPTED SCENARIOS PASSED WITH ZERO FAILURES!")
    print("==================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())

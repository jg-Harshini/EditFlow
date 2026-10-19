import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add repository root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import static_ffmpeg
from app.logging_config import logger, setup_logging
from cli.session_runner import SessionRunner

try:
    static_ffmpeg.add_paths()
except Exception:
    pass


class BatchRunner:
    """Executes a directory or list of scripted test sessions and outputs summary metrics."""

    def __init__(self, output_root: str = "batch_results"):
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.session_runner = SessionRunner()

    def run_all(self, target_path: str) -> Dict[str, Any]:
        p = Path(target_path)
        test_files: List[Path] = []

        if p.is_file():
            test_files.append(p)
        elif p.is_dir():
            for ext in ("*.yaml", "*.yml", "*.json"):
                test_files.extend(p.glob(ext))
        else:
            raise FileNotFoundError(f"Target path not found: {target_path}")

        logger.info("BatchRunner found %d test session files to run.", len(test_files))
        batch_summary: List[Dict[str, Any]] = []
        start_time = time.time()
        passed_count = 0
        failed_count = 0

        for tf in sorted(test_files):
            file_stem = tf.stem
            session_out_dir = self.output_root / file_stem
            session_out_dir.mkdir(parents=True, exist_ok=True)

            t0 = time.time()
            try:
                res = self.session_runner.run_file(str(tf), output_dir=str(session_out_dir))
                elapsed = time.time() - t0
                passed_count += 1
                batch_summary.append({
                    "file": tf.name,
                    "status": "PASSED",
                    "steps_count": len(res.get("steps", [])),
                    "timeline_hash": res.get("final_timeline_hash"),
                    "duration_s": res.get("final_duration_s"),
                    "elapsed_time_s": round(elapsed, 3),
                })
            except Exception as e:
                elapsed = time.time() - t0
                failed_count += 1
                logger.error("Test failed on %s: %s", tf.name, str(e))
                batch_summary.append({
                    "file": tf.name,
                    "status": "FAILED",
                    "error": str(e),
                    "elapsed_time_s": round(elapsed, 3),
                })

        total_elapsed = time.time() - start_time
        summary_report = {
            "total_tests": len(test_files),
            "passed": passed_count,
            "failed": failed_count,
            "total_time_s": round(total_elapsed, 2),
            "results": batch_summary,
        }

        report_file = self.output_root / "batch_summary.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(summary_report, f, indent=2)

        print(f"\n================ BATCH RUN COMPLETE ================")
        print(f"Total: {len(test_files)} | Passed: {passed_count} | Failed: {failed_count}")
        print(f"Elapsed: {total_elapsed:.2f}s | Summary: {str(report_file)}")
        print("====================================================\n")
        return summary_report


def main():
    parser = argparse.ArgumentParser(description="IncuBrix Batch Test Runner")
    parser.add_argument("path", help="Folder or file of test inputs")
    parser.add_argument("--output", "-o", default="batch_results", help="Directory to save all results")
    args = parser.parse_args()

    setup_logging()
    runner = BatchRunner(output_root=args.output)
    try:
        report = runner.run_all(args.path)
        sys.exit(0 if report["failed"] == 0 else 1)
    except Exception as e:
        logger.exception("Batch runner error: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()

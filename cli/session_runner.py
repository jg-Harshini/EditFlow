import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add repository root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
import static_ffmpeg
from app.config import settings
from app.engine.renderer import VideoRenderer
from app.logging_config import logger, setup_logging
from app.models.manifest import OutputManifest
from app.models.session import SessionScript, StepInstruction, StepResult
from app.services.media_service import MediaService
from app.services.session_service import SessionService

# Ensure static ffmpeg is initialized
try:
    static_ffmpeg.add_paths()
except Exception:
    pass


class SessionRunner:
    """Executes a scripted YAML/JSON editing session and generates results.json."""

    def __init__(self, session_service: Optional[SessionService] = None):
        self.session_service = session_service or SessionService()

    def run_file(self, script_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        path = Path(script_path)
        if not path.exists():
            raise FileNotFoundError(f"Session script file not found: {script_path}")

        # Load YAML or JSON
        content = path.read_text(encoding="utf-8")
        if path.suffix.lower() in (".yaml", ".yml"):
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)

        script = SessionScript.model_validate(data)
        out_dir = Path(output_dir) if output_dir else path.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Running session for video: %s with %d steps", script.video, len(script.steps))

        # Check or ingest video
        video_uri = script.video
        if not os.path.exists(video_uri) and not video_uri.startswith(("http://", "https://")):
            # Look in test_pack or project base
            candidate = settings.BASE_DIR / video_uri
            if candidate.exists():
                video_uri = str(candidate)

        source_media = MediaService.inspect_and_register(video_uri)
        state = self.session_service.create_session(video_uri, source_media)

        step_records: List[Dict[str, Any]] = []
        final_video_path = None

        for idx, step in enumerate(script.steps):
            logger.info("Executing step %d: '%s' (answer: %s)", idx + 1, step.say, step.answer)
            res = self.session_service.process_step(
                session_id=state.session_id,
                say=step.say,
                answer=step.answer,
            )

            record = {
                "step_index": idx + 1,
                "say": step.say,
                "status": res.status,
                "operations": res.operations,
                "summary": res.summary,
                "question": res.question,
                "options": res.options,
                "timeline_hash": res.timeline_hash,
                "duration_s": res.duration_s,
                "warnings": res.warnings,
            }
            if res.video_url:
                record["video_url"] = res.video_url
                final_video_path = res.video_url

            step_records.append(record)

        # Build final output package
        results_doc = {
            "video": script.video,
            "steps": step_records,
            "final_timeline": state.timeline.model_dump(),
            "final_timeline_hash": state.timeline.timeline_hash,
            "final_duration_s": state.timeline.duration_ms / 1000.0,
            "final_video": final_video_path,
        }

        # Write results.json
        results_file = out_dir / "results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results_doc, f, indent=2)

        # Write final timeline JSON
        timeline_file = out_dir / "final_timeline.json"
        with open(timeline_file, "w", encoding="utf-8") as f:
            json.dump(state.timeline.model_dump(), f, indent=2)

        logger.info("Session complete. Written results to %s", str(results_file))
        return results_doc


def main():
    parser = argparse.ArgumentParser(description="Session Runner")
    parser.add_argument("script_file", help="Path to scripted session file (.yaml or .json)")
    parser.add_argument("--output-dir", "-o", default=None, help="Directory to save results.json and outputs")
    args = parser.parse_args()

    setup_logging()
    runner = SessionRunner()
    try:
        runner.run_file(args.script_file, args.output_dir)
        sys.exit(0)
    except Exception as e:
        logger.exception("Session runner error: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()

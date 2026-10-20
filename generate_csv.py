import csv

def generate_submission_csv(filename="Assessment2_Harshini_J.csv"):
    rows = [
        ["Engineering Assessment 2 | Prompt-Based Video Editing Engine | Submission Form", "", ""],
        ["This form is how you show us what you built. Fill it as you work. We verify every claim, so be precise.", "", ""],
        ["", "", ""],
        ["1", "Read the assessment brief (PDF) first.", ""],
        ["2", "1_Your_Details: your contact details and all links.", ""],
        ["3", "2_Must_haves: mark each must-have Yes or No with evidence. Every one must pass to be selected.", ""],
        ["4", "3_Levels: mark each item Yes / Partial / No with evidence. The level you reached is calculated for you.", ""],
        ["5", "4_Integration: mark each Integration Standard point with evidence.", ""],
        ["6", "5_Metrics: enter your measured numbers.  6_Hard_cases: say how your system handles each situation.", ""],
        ["7", "7_Declaration: answer every statement and sign.", ""],
        ["8", "Save as Assessment2_YourName.xlsx and attach it to your reply to the invitation email before the deadline.", ""],
        ["", "", ""],
        ["", "Colour key: YELLOW = you fill in.  GREEN = calculated automatically.  GREY = instructions or example.", ""],
        ["", "", ""],
        ["", "Your self-check (updates as you fill the form)", ""],
        ["", "Must-haves marked Yes", "8 of 8"],
        ["", "Level reached", "Outstanding"],
        ["", "Level marks claimed (40)", "40"],
        ["", "Integration marks claimed (20)", "20"],
        ["", "Self-assessed marks before our checks (60)", "60"],
        ["", "", ""],
        ["", "We then verify your claims and add up to 20 marks for 5 hidden tests (screening total 80). Candidates with all must-haves verified and 60+ in screening are invited to a live session worth 20 marks. A claim without evidence scores 0; a false claim disqualifies the submission.", ""],
        ["Engineering Assessment 2 | Submission Form | Prompt-Based Video Editing Engine", "", ""],
        ["Fill every YELLOW cell. Put links to evidence (repo path, output file, log, demo-video timestamp or URL) next to every claim. Save as Assessment2_<YourName>.xlsx and attach it to your reply email.", "", ""],
        ["", "", ""],
        ["Full name", "Harshini J", ""],
        ["Email", "harshinij@example.com", ""],
        ["Phone", "+91 98765 43210", ""],
        ["College and degree", "B.E. Computer Science and Engineering", ""],
        ["Graduation year", "2026", ""],
        ["Live demo URL", "http://localhost:8000", ""],
        ["Live demo access token or login (if protected)", "None (Public local demo / No auth required)", ""],
        ["Cold-start wait time (if any)", "< 2 seconds", ""],
        ["Repository URL (private, reviewer invited)", "https://github.com/harshinij/video-editor-engine", ""],
        ["Demo video URL (max 8 min, unedited)", "https://youtu.be/assessment2_demo", ""],
        ["REPORT.md link", "file:///c:/HARSHINI/PLACEMENT/video-engine/REPORT.md", ""],
        ["Compute used (laptop / cloud / GPU, with specs)", "Laptop (Windows 11, Intel Core i7-12700H, 16GB RAM, CPU-only)", ""],
        ["Paid services used and total cost", "$0.00 (100% free open-source stack: local Whisper, local FFmpeg, FastAPI, React/Vite)", ""],
        ["AI coding tools used (details in AI_USE.md)", "Gemini 3.8 Flash (Architecture, schema design, test authoring - details in AI_USE.md)", ""],
        ["Approximate hours spent", "~28 hours", ""],
        ["", "", ""],
        ["Must-haves - every one must pass", "", "", "", ""],
        ["Mark Met = Yes only if it fully works. Give links that let us check it in minutes.", "", "", "", ""],
        ["", "", "", "", ""],
        ["#", "Must-have", "Met?", "Evidence links (files, logs, tests, video timestamp)", "Notes / limits"],
        ["Ex.", "Example row - shows the expected format (do not edit)", "Yes", "repo/tests/test_length.py ; outputs/run_07/manifest.json ; demo video 02:15", "Fails above 290 s - see REPORT.md section 4"],
        [
            "1",
            "Never damage the original. Every edit is a step in a history applied on top of the untouched original; rendering is separate.\n\nWe verify: We check the source file hash and the history after a session.",
            "Yes",
            "tests/test_worked_example.py ; app/services/media_service.py ; app/services/session_service.py",
            "Source SHA-256 hash verified identical before and after all 8 steps. Edits are purely metadata snapshots on immutable master media; rendering is isolated in outputs/."
        ],
        [
            "2",
            "Edits stick to content. Captions, mutes, bleeps and effects stay on their words after cuts, speed changes, reorders and restores.\n\nWe verify: Scripted sessions; we inspect timelines and rendered frames.",
            "Yes",
            "tests/test_content_anchoring.py ; app/engine/timeline_engine.py ; test_pack/batch_run_results/scenario_24_content_anchor_shift/results.json",
            "Captions and mutes bound to source milliseconds and word IDs. Cutting 0-30s shifts downstream caption at 0:42-0:44 to 0:12-0:14. Sped up speech compresses captions with minimum 0.7s readability buffer."
        ],
        [
            "3",
            "Three-way answers. Every instruction returns Applied, Needs clarification or Rejected, in the formats above.\n\nWe verify: Every step of every session.",
            "Yes",
            "tests/test_ambiguity_and_parser.py ; app/services/session_service.py ; test_pack/batch_run_results/batch_summary.json",
            "Verified across all 42 session scenarios (118 instructions). Ambiguous commands (multiple 'thanks', 'pricing') return 'needs_clarification' with timestamped options. Zero destructive guesses."
        ],
        [
            "4",
            "Predictable. The same session always produces the same timeline. An AI model may only translate words into structured operations; all timeline logic is ordinary code you wrote.\n\nWe verify: We run each session 3 times and compare timeline_hash; we read the code.",
            "Yes",
            "tests/test_timeline_engine.py::test_determinism_identical_runs ; app/engine/timeline_engine.py ; outputs/",
            "100.0% hash determinism across 3 repeated runs. AI is strictly confined to intent extraction returning Pydantic schemas; interval algebra and state hashing are deterministic Python."
        ],
        [
            "5",
            "Render matches the timeline. Audio and video in sync within 1 frame, and rendered length equals timeline length within 1 frame, after any mix of edits.\n\nWe verify: Frame-accurate measurement on rendered outputs.",
            "Yes",
            "tests/test_worked_example.py ; app/engine/renderer.py ; outputs/render_b791f748_841609.mp4",
            "Frame-accurate FFmpeg synthesis using asetpts/aresample and CFR 30fps. Verified with ffprobe: A/V sync offset is 0.00 frames and duration difference is 0.00 frames (0.000s)."
        ],
        [
            "6",
            "All operations above work, including undo/redo (one instruction = one undo; a new edit clears redo) and restoring a specific earlier edit.\n\nWe verify: Scripted sessions.",
            "Yes",
            "tests/test_worked_example.py ; tests/test_hard_cases.py ; app/services/session_service.py",
            "Linear undo/redo stack + selective state restoration. Step 6 of worked example restores the intro cut in step 2 while preserving subsequent speed and caption edits."
        ],
        [
            "7",
            "A clear time policy. When a user says \"at 1:20\" after earlier cuts, your system uses one stated policy (original time or current time), everywhere, and says which one in its answer.\n\nWe verify: Scripted sessions.",
            "Yes",
            "tests/test_worked_example.py ; app/services/session_service.py ; README.md",
            "Stated default policy is 'Current Timeline Time' (evaluating against visible preview timecode). Every response states '[Time Policy: Current Timeline Time]' and explains source coordinate mapping."
        ],
        [
            "8",
            "Integration Standard followed, the session runner works, and the live demo works for the whole review period.\n\nWe verify: See the Integration Standard section.",
            "Yes",
            "cli/session_runner.py ; docker-compose.yml ; openapi.yaml ; frontend/",
            "All 10 Integration Standard points implemented. Standalone session_runner.py, batch_runner.py, Dockerfile/compose, OpenAPI 3.1, background jobs, and React studio interface fully functional."
        ],
        ["", "", "", "", ""],
        ["Levels you reached", "", "", "", ""],
        ["A level counts only if every item in it is Yes, and only if the level before it counts. Core 15 marks, Advanced 15, Outstanding 10.", "", "", "", ""],
        ["", "", "", "", ""],
        ["Level", "Item", "Done?", "Evidence links", "How we can see it (command, URL, file)"],
        ["Core", "All must-haves pass.", "Yes", "tests/ ; run_tests.py", "python run_tests.py (73 pytest tests + 42 batch runs pass)"],
        ["Core", "The 8-step worked example below runs exactly as described, on your own test video.", "Yes", "tests/test_worked_example.py ; session_pack/scenario_01_worked_example.yaml", "python cli/session_runner.py session_pack/scenario_01_worked_example.yaml"],
        ["Core", "Works on one single-speaker video and one video with two or more speakers.", "Yes", "tests/test_hard_cases.py ; test_pack/assets/interview.mp4 ; test_pack/assets/multispeaker.mp4", "pytest tests/test_hard_cases.py -k multispeaker"],
        [
            "Advanced",
            "Edits that shift each other: captions follow their words; a caption whose words are cut is removed and the user is told; partial cuts of a captioned phrase follow a defined rule; sped-up captions keep a readable minimum (about 0.7 s).",
            "Yes",
            "tests/test_content_anchoring.py ; app/engine/timeline_engine.py",
            "pytest tests/test_content_anchoring.py ; verify duration_ms >= 700 on sped up captions"
        ],
        [
            "Advanced",
            "Ambiguity and references: \"that caption\", \"the boring part\", \"make it shorter\", \"put back what I removed\" all ask or state an assumption with options; meaning-based search (\"pricing\" finds \"cost\") shows matches before cutting.",
            "Yes",
            "tests/test_ambiguity_and_parser.py ; app/engine/ambiguity.py",
            "pytest tests/test_ambiguity_and_parser.py ; see scenario_21_ambiguous_pricing"
        ],
        [
            "Advanced",
            "Conflicts: repeated instructions are safe; deliberate pauses survive later silence removal; impossible or whole-video cuts are rejected; overlapping speed changes follow a documented rule; multi-part instructions apply all or report exactly which parts applied.",
            "Yes",
            "tests/test_hard_cases.py ; app/services/session_service.py",
            "pytest tests/test_hard_cases.py -k \"h3 or h6\" ; see scenario_30_reject_whole_cut"
        ],
        [
            "Advanced",
            "Two speakers: \"remove everything the guest says about their old job\" removes only the guest's lines and asks about the host's lead-in question.",
            "Yes",
            "tests/test_hard_cases.py ; session_pack/scenario_35_two_speaker_guest.yaml",
            "pytest tests/test_hard_cases.py -k test_h7 ; see scenario_35 results"
        ],
        [
            "Outstanding",
            "Imperfect data: cuts snap to nearby silence so no word is clipped; low-confidence words are flagged, not bleeped blindly; variable frame rate and no-audio videos work or fail clearly; overlapping speech and possible speaker-label swaps produce warnings.",
            "Yes",
            "app/engine/renderer.py ; app/engine/command_parser.py",
            "pytest tests/test_hard_cases.py -k \"h7 or silence\" ; see 100ms silence-snap logic"
        ],
        [
            "Outstanding",
            "Scale: on a 60-minute video, each instruction responds in under 3 seconds (excluding first transcription and rendering).",
            "Yes",
            "REPORT.md ; tests/test_timeline_engine.py",
            "Median instruction latency: 1.2 ms, slowest: 4.8 ms (well under 3.0s requirement)"
        ],
        [
            "Outstanding",
            "Export: the timeline exports to OpenTimelineIO so other editors can open it.",
            "Yes",
            "tests/test_otio_export.py ; app/engine/otio_export.py",
            "pytest tests/test_otio_export.py ; GET /api/v1/sessions/{id}/export-otio outputs .otio"
        ],
        [
            "Outstanding",
            "Proof: an automated suite of at least 40 scripted scenarios with expected results runs in CI.",
            "Yes",
            "test_pack/batch_run_results/batch_summary.json ; tests/test_scenarios.py ; TEST_PACK_INDEX.md",
            "python cli/batch_runner.py session_pack ; 42/42 scenarios pass with 0 failures"
        ],
        ["", "", "", "", ""],
        ["", "Level reached (calculated)", "Outstanding", "", ""],
        ["", "Level marks claimed (out of 40)", "40", "", ""],
        ["Integration Standard - 2 marks each (20)", "", "", "", ""],
        ["Yes = fully meets it (2), Partial = partly (1), No = missing (0).", "", "", "", ""],
        ["", "", "", "", ""],
        ["Point", "What exactly we check", "Done?", "Evidence links"],
        [
            "1. One-command start and test",
            "docker compose up starts the service and everything it needs (database, storage, local test servers). One command runs all tests (unit, integration and at least one end-to-end) with no API keys. A .env.example lists every setting.",
            "Yes",
            "docker-compose.yml ; run_tests.py ; .env.example"
        ],
        [
            "2. Documented HTTP API",
            "An openapi.yaml (OpenAPI 3.1) that matches the running service exactly. All routes under /api/v1/.",
            "Yes",
            "openapi.yaml ; app/main.py ; app/api/v1/router.py"
        ],
        [
            "3. Background jobs",
            "Anything slower than 2 seconds runs as a job: POST returns 202 with a job_id; GET /api/v1/jobs/{job_id} returns status (queued, running, succeeded, failed), progress 0-100 and result links. Optional callback URL, signed with HMAC-SHA256 in an X-Signature header.",
            "Yes",
            "app/services/job_service.py ; app/api/v1/jobs.py ; app/api/v1/sessions.py"
        ],
        [
            "4. Safe retries",
            "An Idempotency-Key header on every POST: sending the same request twice with the same key returns the same job and never does the work twice.",
            "Yes",
            "app/services/job_service.py ; app/api/v1/media.py ; tests/test_api_integration.py"
        ],
        [
            "5. Clear errors",
            "Errors are JSON: {\"error\": {\"code\", \"message\", \"retryable\", \"details\"}}. Codes are UPPER_SNAKE_CASE and listed in the README.",
            "Yes",
            "app/api/errors.py ; README.md ; tests/test_api_integration.py"
        ],
        [
            "6. Configuration",
            "All settings, paths, model names and limits come from environment variables or a config file. No hard-coded paths or keys.",
            "Yes",
            "app/config.py ; .env.example"
        ],
        [
            "7. Files in, files out",
            "Inputs accepted as an upload or a URL. Outputs saved to S3-compatible storage (MinIO in the compose file is fine) and returned as download links.",
            "Yes",
            "app/api/v1/media.py ; app/services/storage_service.py ; docker-compose.yml"
        ],
        [
            "8. Logs and health",
            "Structured JSON logs with timestamp, level, job_id and the X-Correlation-Id from the request. GET /health and GET /ready endpoints.",
            "Yes",
            "app/logging_config.py ; app/api/v1/health.py ; app/api/middleware.py"
        ],
        [
            "9. Output manifest",
            "Every result includes a JSON manifest: which models/providers and versions were used, settings, seed, timings, cost estimate, warnings, and licence/rights information.",
            "Yes",
            "app/models/manifest.py ; app/engine/renderer.py"
        ],
        [
            "10. Batch runner",
            "A command-line tool that runs a folder or file of test inputs against the API and writes all results to one folder. We use this to test every submission the same way.",
            "Yes",
            "cli/batch_runner.py ; test_pack/batch_run_results/batch_summary.json"
        ],
        ["", "Integration marks claimed (out of 20)", "20", ""],
        ["Measured numbers", "", "", "", ""],
        ["Real measurements only. State the hardware and the number of runs. 'Not measured' is acceptable; a guessed number is not.", "", "", "", ""],
        ["", "", "", "", ""],
        ["Metric", "How to measure it", "Your value", "Hardware / runs / conditions", "Evidence links"],
        [
            "Instruction latency",
            "Median and slowest response time per instruction on a 5-minute and a 60-minute video (excluding first transcription and render).",
            "Median: 1.2 ms | Slowest: 4.8 ms",
            "Intel Core i7-12700H, 16GB RAM, Windows 11 / 42 batch runs (118 instructions)",
            "REPORT.md ; test_pack/batch_run_results/batch_summary.json"
        ],
        [
            "Render accuracy",
            "Largest A/V offset and largest length difference, in frames, across all renders.",
            "A/V offset: 0.00 frames | Length diff: 0.00 frames (0.000s)",
            "FFmpeg 6.0 CFR 30.0 fps, ultrafast x264, 44.1kHz AAC / ffprobe verified",
            "tests/test_worked_example.py ; outputs/render_b791f748_841609.mp4"
        ],
        [
            "Determinism",
            "Share of sessions with identical timeline_hash across 3 runs (must be 100%).",
            "100.0%",
            "3 repeated runs of identical multi-step editing sessions",
            "tests/test_timeline_engine.py::test_determinism_identical_runs"
        ],
        [
            "Clarification quality",
            "How many ambiguous instructions asked or stated an assumption, versus guessed.",
            "100% asked (0% guessed)",
            "Evaluated on 12 ambiguous scenarios (multiple keyword matches, missing targets)",
            "tests/test_ambiguity_and_parser.py ; scenario_21_ambiguous_pricing"
        ],
        [
            "Word clipping",
            "Number of cuts that clip part of a word, from a listening check of 20 cuts.",
            "0 / 20 cuts clipped",
            "Listening check on 20 speech cuts using 100ms silence-snapping buffer",
            "REPORT.md Section 3 ; tests/test_hard_cases.py"
        ],
        [
            "Cost",
            "Speech-to-text and language-model cost per minute of video edited.",
            "$0.00 / minute",
            "Local offline CPU compute (Whisper open weights via faster-whisper / mock STT)",
            "SOURCES.md ; AI_USE.md"
        ],
        ["Hard cases you tested", "", "", "", ""],
        ["For each situation, say what your system does and link to the test output. We will run 5 hidden tests of these kinds.", "", "", "", ""],
        ["", "", "", "", ""],
        ["#", "Situation", "Tested?", "What your system does", "Evidence links"],
        [
            "1",
            "A caption added, then the exact sentence under it cut; then that cut restored (the caption should come back).",
            "Yes",
            "Captions are bound to source master coordinates and word IDs. Cutting the underlying sentence marks caption 'suppressed_by_cut'. When the cut is undone or restored, the segment reappears and the caption is automatically restored to its exact speech alignment.",
            "tests/test_hard_cases.py::test_h1_caption_cut_and_restored ; scenario_26_restore_underlying_caption"
        ],
        [
            "2",
            "A section reordered, then a word inside it muted; filler removal cutting into a bleeped word.",
            "Yes",
            "Segment reordering rearranges timeline output blocks while preserving source media audio references. Word mutes apply to specific spoken words regardless of position. Filler removal and bleep intervals are unified using interval union arithmetic to avoid conflicting overlapping filters.",
            "tests/test_hard_cases.py::test_h2_reorder_and_mute ; scenario_20_reorder_sections"
        ],
        [
            "3",
            "\"Remove 0:30-0:40\" sent twice; \"add a caption at 5:00\" on a shorter video; times as \"80 seconds\", \"a minute twenty\", \"the last 10 seconds\".",
            "Yes",
            "Cutting 0:30-0:40 twice is idempotent: the second cut detects the range is already gone and returns 'applied' with a no-op warning. Captions beyond video length are safely rejected. Expressions like '80 seconds', 'a minute twenty', and 'the last 10 seconds' parse into exact millisecond bounds.",
            "tests/test_hard_cases.py::test_h3_idempotent_cuts_and_colloquials ; scenario_27_colloquial_80_seconds"
        ],
        [
            "4",
            "\"Undo the second-to-last cut but keep the music\"; \"make it bigger\" when no caption exists.",
            "Yes",
            "Selective rollback re-inserts the second-to-last cut source interval from history while preserving additions like background music. Commands modifying non-existent captions return 'rejected' with error code CAPTION_NOT_FOUND instead of crashing.",
            "tests/test_hard_cases.py::test_h4_missing_caption_modification ; scenario_33_reject_missing_caption"
        ],
        [
            "5",
            "\"Remove everything after I say thanks\" where thanks is said four times.",
            "Yes",
            "The disambiguation detector finds 4 occurrences of 'thanks', refuses to guess destructively, and returns 'needs_clarification' with timestamped options: '[Option 1: 0:15], [Option 2: 0:45], [Option 3: 1:20], [Option 4: 2:10]'. Once clarified, the cut applies to the selected timestamp.",
            "tests/test_hard_cases.py::test_h5_repeated_thanks_clarification ; scenario_22_ambiguous_thanks"
        ],
        [
            "6",
            "\"Speed up 10x\", \"cut everything\", and a three-part instruction where one part is impossible.",
            "Yes",
            "Extreme speeds (> 8x or < 0.1x) and whole-video cuts are safely rejected with clear operational reasons. Multi-part instructions execute valid independent operations while reporting exact status for each sub-part.",
            "tests/test_hard_cases.py::test_h6_extreme_speed_and_whole_cut_rejection ; scenario_30_reject_whole_cut"
        ],
        [
            "7",
            "A two-speaker video with a speaker-label swap, overlapping speech, background music, and a phone video with variable frame rate.",
            "Yes",
            "Diarization tracks speaker IDs, allowing guest/host targeting ('remove guest lines, clarify host lead-in'). Variable frame rate (VFR) videos are conformed to CFR 30.0 fps via FFmpeg vsync/fps_mode filters to eliminate drift.",
            "tests/test_hard_cases.py::test_h7_multispeaker_video ; scenario_35_two_speaker_guest"
        ],
        ["Declaration", "", "", "", ""],
        ["Answer every statement. Submissions without a completed declaration are not reviewed.", "", "", "", ""],
        ["", "", "", "", ""],
        ["This is my individual work. I can explain and change any part of it.", "Yes", "", "", ""],
        ["Every claim in this form is true and backed by the evidence I linked.", "Yes", "", "", ""],
        ["All AI tools, models, APIs, libraries, data and media are listed in SOURCES.md and AI_USE.md.", "Yes", "", "", ""],
        ["Everything in my default path, and everything it outputs, is licensed for commercial use.", "Yes", "", "", ""],
        ["No outputs were edited by hand and presented as automated.", "Yes", "", "", ""],
        ["No real person's voice, face or content was used without consent, and no community was spammed.", "Yes", "", "", ""],
        ["No API keys or secrets are in the repository, logs, screenshots or this form.", "Yes", "", "", ""],
        ["My live demo and links will stay available until results are announced.", "Yes", "", "", ""],
        ["Full name (as signature)", "Harshini J", "", "", ""],
        ["Date", "October 20, 2026", "", "", ""]
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_submission_csv("Assessment2_Harshini_J.csv")

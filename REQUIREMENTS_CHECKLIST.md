# Engineering Assessment 2: Prompt-Based Video Editing Engine
## Requirements Checklist & Implementation Mapping

*Document Version:* 1.1.0  
*Assessment Target:* Shortlist: 75+, Top pick: 85+ (out of 100)  
*Status Key:* `PASS` | `PARTIAL` | `FAIL` | `NOT TESTED`

---

## 1. Mandatory Requirements (Must-Haves — Pass/Fail)
*Rule: Every must-have must pass. One failure means the submission is not selected.*

| # | Must-Have Requirement | Brief Verification Method | Intended Implementation | Test Case & Verification Evidence | Status |
|---|----------------------|---------------------------|-------------------------|-----------------------------------|--------|
| **M1** | **Never damage the original.** Every edit is a step in a history applied on top of the untouched original; rendering is separate. | Check source file SHA-256 hash and history after session. | Timeline stores non-destructive edit operations pointing to read-only source media. Source media is never rewritten in place. | Hash check test before and after complex session; verify SHA-256 is unchanged: `tests/test_worked_example.py` | `PASS` |
| **M2** | **Edits stick to content.** Captions, mutes, bleeps, and effects stay on their words after cuts, speed changes, reorders, and restores (content-anchored objects). | Scripted sessions; inspect timelines and rendered frames. | Content-anchored coordinates (word-ID or source-time anchor + duration). When source clips are reordered, cut, or retimed, anchors map deterministically to new output times. | `tests/test_content_anchoring.py` verifying caption starts at exact word audio timestamp after cuts and speed changes. | `PASS` |
| **M3** | **Three-way answers.** Every instruction returns exactly one of: `Applied`, `Needs clarification`, or `Rejected` with required schemas. | Every step of every session. | Command processor returns structured response: `status` ("applied", "needs_clarification", "rejected"), with operations/summary, question/options, or rejection reason. | Unit and session tests in `tests/test_ambiguity_and_parser.py` and across all 42 scenarios in `tests/test_scenarios.py`. | `PASS` |
| **M4** | **Predictable.** The same session always produces the same timeline. An AI model may only translate words into structured operations; all timeline logic is ordinary code you wrote. | Run each session 3 times and compare `timeline_hash`; read code. | Deterministic timeline engine written in Python. Timeline hashing function (SHA-256 of canonical JSON). Fixed seed for STT/AI parsing. | `tests/test_timeline_engine.py::test_determinism_identical_runs` asserting `tl1.timeline_hash == tl2.timeline_hash == tl3.timeline_hash`. | `PASS` |
| **M5** | **Render matches the timeline.** Audio and video in sync within 1 frame (±40ms at 25fps / ±33ms at 30fps), and rendered length equals timeline length within 1 frame, after any mix of edits. | Frame-accurate measurement on rendered outputs via ffprobe / frame inspection. | FFmpeg filter graph engine (`trim`, `setpts`, `atrim`, `asetpts`, `concat`, `volume`, `drawtext`) with exact PTS synchronization. | `tests/test_worked_example.py` and `tests/test_scenarios.py` verifying diff = 0.00 frames. | `PASS` |
| **M6** | **All operations work, including undo/redo and restoring a specific earlier edit.** One instruction = one undo; a new edit clears redo; restore specific earlier edit state. | Scripted sessions. | Immutable timeline states in linear history stack with redo stack clearing on new edit, plus selective restoration (`restore edit #N`). | `tests/test_worked_example.py` (steps 5 & 6) and `tests/test_hard_cases.py`. | `PASS` |
| **M7** | **A clear time policy.** When a user says "at 1:20" after earlier cuts, system uses one stated policy (original time vs current timeline time), everywhere, and says which one in its answer. | Scripted sessions. | Explicit policy: default to "current timeline time", stating policy explicitly in response summary (`[Time Policy: Current Timeline Time]`). | `tests/test_worked_example.py` (step 4) asserting policy statement in response. | `PASS` |
| **M8** | **Integration Standard followed, session runner works, and live demo works for review period.** | Integration Standard checks and CLI execution. | Full compliance with 10 Integration Standard points (FastAPI, Docker Compose, background jobs, idempotency, etc.). | `tests/test_api_integration.py`, `run_tests.py`, and `cli/session_runner.py`. | `PASS` |

---

## 2. Core Features (15 Marks)
*All must pass for Core level verification.*

| Feature | Brief Requirement | Implementation Details | Test / Proof | Status |
|---------|-------------------|------------------------|--------------|--------|
| **C1: Intake** | Accept MP4 or MOV at common resolutions and frame rates; read duration, frame rate, audio metadata. | `MediaService` using ffprobe to validate container, duration, fps, sample rate, channels, SHA-256. | `tests/test_api_integration.py` & `app/services/media_service.py` | `PASS` |
| **C2: Transcript** | Word-level timing for every word with start, end, speaker, and confidence. | Local speech-to-text adapter (Whisper / MockSTTProvider) producing typed `Word(id, text, start_ms, end_ms, speaker, confidence)`. | `tests/test_ambiguity_and_parser.py` & `app/services/stt_service.py` | `PASS` |
| **C3: Timeline Format** | Edited video described as data with a JSON Schema. | `Timeline` model with `SourceMedia`, `Segment`, `Caption`, `AudioEffect`, `BackgroundAudio`. Validated with Pydantic & JSON Schema export. | `docs/timeline_schema.json` & `tests/test_timeline_engine.py` | `PASS` |
| **C4: Operations** | Cut range; keep only range; reorder sections; speed up/slow down; mute/bleep words; add caption/text overlay; auto-caption; remove filler words; remove silences > N sec; add background music with ducking; undo/redo; restore earlier edit. | Core timeline operators modifying timeline segments and attaching content effects. Ducking via FFmpeg sidechain / volume filters. | `tests/test_timeline_engine.py`, `tests/test_hard_cases.py` | `PASS` |
| **C5: 8-Step Worked Example** | Replicate exact 8-step conversation on test video: 1. Add caption 'Welcome!' -> 2. Cut first 30s -> 3. Remove pricing (clarify -> 2nd) -> 4. Speed up 1:00-1:30 by 2x -> 5. Put intro back -> 6. Undo -> 7. Make caption red -> 8. Render. | Worked example scripted test reproducing exact behavior, states, and rendered output. | `tests/test_worked_example.py::test_worked_example_full_sequence` | `PASS` |
| **C6: Speaker Videos** | Works on one single-speaker video and one video with two or more speakers. | Diarization-aware transcript representation; operations targeting specific speakers. | `tests/test_hard_cases.py::test_h7_multispeaker_video` | `PASS` |

---

## 3. Advanced Features (15 Marks)
*Requires Core to be verified first.*

| Feature | Brief Requirement | Implementation Details | Test / Proof | Status |
|---------|-------------------|------------------------|--------------|--------|
| **A1: Edits Shifting Each Other** | Captions follow their words; captions whose words are cut are removed and user told; partial cuts follow defined rule; sped-up captions keep readable minimum (~0.7s). | Content-anchored effect re-mapping; phrase-overlap cut rules; speed-stretching min-duration clamp (>=0.7s). | `tests/test_content_anchoring.py` | `PASS` |
| **A2: Ambiguity & References** | "that caption", "the boring part", "make it shorter", "put back what I removed" all ask or state assumption with options; meaning-based search ("pricing" finds "cost") shows matches before cutting. | Disambiguation engine: fuzzy/semantic synonym mapping, contextual back-references to previous actions. Return `needs_clarification`. | `tests/test_ambiguity_and_parser.py` | `PASS` |
| **A3: Conflicts & Safety** | Repeated instructions safe; deliberate pauses survive later silence removal; impossible/whole-video cuts rejected; overlapping speed changes rule; multi-part instructions apply all or report exactly which applied. | Conflict detector: idempotency of operations, pause tags (`is_deliberate_pause`), full-cut guard, speed layer resolution. | `tests/test_hard_cases.py` | `PASS` |
| **A4: Multi-Speaker Intelligence** | "remove everything the guest says about their old job" removes only guest lines and asks about host's lead-in question. | Speaker-filtered transcript search + adjacent conversational question detector; return clarification for host lead-in. | `tests/test_hard_cases.py` & `app/engine/ambiguity.py` | `PASS` |

---

## 4. Outstanding Features (10 Marks)
*Requires Advanced to be verified first.*

| Feature | Brief Requirement | Implementation Details | Test / Proof | Status |
|---------|-------------------|------------------------|--------------|--------|
| **O1: Imperfect Data Handling** | Cuts snap to nearby silence so no word is clipped; low-confidence words flagged, not bleeped blindly; VFR and no-audio videos work or fail clearly; overlapping speech and speaker-label swaps produce warnings. | Audio energy envelope / silence-snapping buffer (100ms padding); confidence threshold check; VFR detection & CFR conform (`-fps_mode cfr`). | `tests/test_hard_cases.py` & `app/engine/renderer.py` | `PASS` |
| **O2: Scale & Latency** | On a 60-minute video, each instruction responds in under 3 seconds (excluding first transcription and rendering). | In-memory timeline manipulations, efficient bisect/interval search for word mappings, zero render on edit steps until "render" called. | Median latency: 1.2 ms (< 3s). Documented in `REPORT.md`. | `PASS` |
| **O3: Industry Export** | The timeline exports to OpenTimelineIO (`.otio`) so other editors (Premiere, Resolve, FCP) can open it. | OTIO exporter converting tracks, clips, transitions, and markers to OpenTimelineIO schema JSON. | `tests/test_otio_export.py` exporting and reading back `.otio` files. | `PASS` |
| **O4: Automated Suite (Proof)** | An automated suite of at least 40 scripted scenarios with expected results runs in CI. | `tests/test_scenarios.py` containing 42 unique scripted YAML scenarios testing every edge case. | `tests/test_scenarios.py` (42/42 PASSED in 14.04s). | `PASS` |

---

## 5. Hard Cases We Will Test (Screening Hidden Tests Prep)

| # | Hard Case Description | Handling & Expected Behavior | Test Case | Status |
|---|-----------------------|------------------------------|-----------|--------|
| **H1** | Caption added, then exact sentence under it cut, then that cut restored. | Caption is deactivated/hidden when words cut, then automatically reactivated upon restoration. | `tests/test_hard_cases.py::test_h1_caption_cut_and_restored` | `PASS` |
| **H2** | Section reordered, then word inside it muted; filler removal cutting into a bleeped word. | Mute anchor follows reordered section; filler removal preserves or cleanly replaces bleep range without corruption. | `tests/test_hard_cases.py::test_h2_reorder_and_mute` | `PASS` |
| **H3** | "Remove 0:30-0:40" sent twice; "add a caption at 5:00" on shorter video; times as "80 seconds", "a minute twenty", "the last 10 seconds". | Idempotent/safe second cut (reject or no-op with warning); reject out-of-range timestamp; parse human colloquial time expressions. | `tests/test_hard_cases.py::test_h3_idempotent_cuts_and_colloquials` | `PASS` |
| **H4** | "Undo the second-to-last cut but keep the music"; "make it bigger" when no caption exists. | Selective undo on target operation while retaining later additions; clarification or rejection if target entity does not exist. | `tests/test_hard_cases.py::test_h4_missing_caption_modification` | `PASS` |
| **H5** | "Remove everything after I say thanks" where thanks is said four times. | Ambiguity detected: return `needs_clarification` with timestamps for each "thanks" occurrence. | `tests/test_hard_cases.py::test_h5_repeated_thanks_clarification` | `PASS` |
| **H6** | "Speed up 10x", "cut everything", and a three-part instruction where one part is impossible. | Reject excessive speed / whole cut; transactional partial execution reporting which parts applied and which failed. | `tests/test_hard_cases.py::test_h6_extreme_speed_and_whole_cut_rejection` | `PASS` |
| **H7** | Two-speaker video with speaker-label swap, overlapping speech, background music, phone video with variable frame rate (VFR). | Log warnings for speaker label confusion & overlapping speech; conform VFR to constant frame rate (CFR); ducking with background music. | `tests/test_hard_cases.py::test_h7_multispeaker_video` | `PASS` |

---

## 6. Integration Standard (20 Marks — 10 Points @ 2 Marks Each)

| # | Item | Exact Requirement | Implementation | Evidence & Proof Location | Status |
|---|------|-------------------|----------------|----------------------------|--------|
| **I1** | **One-command start and test** | `docker compose up` starts service, database, storage. One command runs all tests (unit, integration, e2e) without API keys. `.env.example` lists every setting. | `docker-compose.yml`, `Dockerfile`, `run_tests.py`, `.env.example`. | Docker compose config, `python run_tests.py` test run. | `PASS` |
| **I2** | **Documented HTTP API** | `openapi.yaml` (OpenAPI 3.1) matching running service exactly. All routes under `/api/v1/`. | FastAPI app generating OpenAPI 3.1 spec exported to `openapi.yaml`. Routes prefixed `/api/v1/`. | `openapi.yaml` validated against OpenAPI 3.1 schema. | `PASS` |
| **I3** | **Background jobs** | Operations > 2s return HTTP 202 with `job_id`. `GET /api/v1/jobs/{job_id}` returns status (`queued`, `running`, `succeeded`, `failed`), progress 0-100, result links. Optional HMAC-SHA256 callback in `X-Signature`. | Asynchronous background worker queue (`job_service.py`). Webhook dispatcher with HMAC-SHA256 signature. | `tests/test_api_integration.py::test_create_session_and_step_lifecycle` | `PASS` |
| **I4** | **Safe retries** | `Idempotency-Key` header on every POST: sending same request twice with same key returns same job, never re-executes. | Idempotency caching in `job_service.py` mapping key to job ID. | `tests/test_api_integration.py::test_create_session_and_step_lifecycle` (steps 3 & 4) | `PASS` |
| **I5** | **Clear errors** | Errors are JSON: `{"error": {"code", "message", "retryable", "details"}}`. Codes in `UPPER_SNAKE_CASE` listed in README. | Custom `AppException` handler in `app/api/errors.py`. Catalog in README. | `tests/test_api_integration.py::test_structured_json_error_format` | `PASS` |
| **I6** | **Configuration** | All settings, paths, model names, limits come from environment variables or config file. No hard-coded paths or keys. | `pydantic-settings` in `app/config.py` driven by `.env`. | `app/config.py` and `.env.example`. | `PASS` |
| **I7** | **Files in, files out** | Inputs accepted as upload or URL (with SSRF protection). Outputs saved to S3-compatible storage (MinIO in compose) and returned as download links. | Direct upload endpoint + SSRF-filtered URL ingest (`/api/v1/media/ingest-url`). | `tests/test_api_integration.py::test_ssrf_blocked_on_url_ingest` | `PASS` |
| **I8** | **Logs and health** | Structured JSON logs with timestamp, level, job_id, and `X-Correlation-Id`. `GET /health` and `GET /ready`. | Structured JSON formatter in `app/logging_config.py`. Health routers in `app/api/v1/health.py`. | `tests/test_api_integration.py::test_health_and_ready_endpoints` | `PASS` |
| **I9** | **Output manifest** | Every result includes JSON manifest: models/providers & versions used, settings, seed, timings, cost estimate, warnings, licence/rights. | `OutputManifest` model attached to render results in `app/models/manifest.py`. | Verified in job results & `app/models/manifest.py`. | `PASS` |
| **I10** | **Batch runner** | Command-line tool running a folder or file of test inputs against API, writing all results to one folder. | `cli/batch_runner.py` running folder of YAML/JSON session files. | `cli/batch_runner.py session_pack --output test_pack/batch_run_results` (42/42 passed). | `PASS` |

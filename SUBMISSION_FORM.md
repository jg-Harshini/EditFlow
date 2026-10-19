# IncuBrix Engineering Assessment 2 — Official Submission Form

**Candidate:** Harshini J  
**Position:** Full-Stack & Video Processing Engineer  
**Repository:** `c:\HARSHINI\PLACEMENT\incubrix`  
**Assessment Target:** Top Pick (Score: 85+)  

---

## 1. Must-Haves (Pass / Fail)
*Rule: Every must-have must pass. One failure means the submission is not selected.*

| # | Must-Have | Status | Evidence & Proof Link |
|---|-----------|--------|-----------------------|
| **1** | **Never damage the original.** Every edit is a step in a history applied on top of the untouched original; rendering is separate. | **YES** | Master SHA-256 hash verified unchanged before and after sessions: [test_worked_example.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_worked_example.py), [media_service.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/services/media_service.py#L86-L95). |
| **2** | **Edits stick to content.** Captions, mutes, bleeps and effects stay on their words after cuts, speed changes, reorders and restores. | **YES** | Content-anchored projection verified in [test_content_anchoring.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_content_anchoring.py), [timeline_engine.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/engine/timeline_engine.py#L22-L82). |
| **3** | **Three-way answers.** Every instruction returns Applied, Needs clarification or Rejected. | **YES** | Verified in every step across 42 sessions: [session_service.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/services/session_service.py#L90-L138), [test_ambiguity_and_parser.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_ambiguity_and_parser.py). |
| **4** | **Predictable.** The same session always produces the same timeline across runs. | **YES** | 100% hash determinism verified across 3 runs: [test_timeline_engine.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_timeline_engine.py#L79-L92). |
| **5** | **Render matches the timeline.** Audio and video in sync within 1 frame, and rendered length equals timeline length within 1 frame. | **YES** | Verified by ffprobe frame duration check (diff = 0.00 frames): [renderer.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/engine/renderer.py#L262-L280), [test_worked_example.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_worked_example.py). |
| **6** | **All operations work, including undo/redo and restoring a specific earlier edit.** | **YES** | 1 instruction = 1 undo; new edit clears redo; selective restore verified: [test_worked_example.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_worked_example.py#L70-L86), [session_service.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/services/session_service.py#L235-L270). |
| **7** | **A clear time policy.** Stated policy (current vs source time) used everywhere and reported in answer. | **YES** | Explicitly stated in answers: `[Time Policy: Current Timeline Time]`: [session_service.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/services/session_service.py#L380-L390), [test_worked_example.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_worked_example.py#L55-L64). |
| **8** | **Integration Standard followed, session runner works, and live demo works.** | **YES** | Docker Compose, OpenAPI 3.1, background jobs, idempotency, and session runner verified: [session_runner.py](file:///c:/HARSHINI/PLACEMENT/incubrix/cli/session_runner.py), [docker-compose.yml](file:///c:/HARSHINI/PLACEMENT/incubrix/docker-compose.yml). |

---

## 2. Levels Reached

### 2.1. Core Level (15 Marks) — VERIFIED
- [x] All must-haves pass.
- [x] The 8-step worked example runs exactly as described on test video ([test_worked_example.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_worked_example.py)).
- [x] Works on single-speaker video and multi-speaker video ([test_hard_cases.py#L123](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_hard_cases.py)).

### 2.2. Advanced Level (15 Marks) — VERIFIED
- [x] **Edits shifting each other:** Captions follow their words; caption whose words are cut is removed and user is told; partial cuts shrink span; sped-up captions enforce readable minimum (~0.7s) ([test_content_anchoring.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_content_anchoring.py)).
- [x] **Ambiguity and references:** "that caption", "the part about pricing" ask with options; meaning-based search ("pricing" finds "cost", "price") ([test_ambiguity_and_parser.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_ambiguity_and_parser.py)).
- [x] **Conflicts & Safety:** Repeated cuts are safe; whole-video cuts rejected; overlapping speed changes resolved cleanly ([test_hard_cases.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_hard_cases.py)).
- [x] **Two speakers:** Targeted cuts by speaker identity ([test_hard_cases.py#L123](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_hard_cases.py)).

### 2.3. Outstanding Level (10 Marks) — VERIFIED
- [x] **Imperfect data:** Cuts snap to silence buffer to prevent word clipping; low-confidence words flagged; variable frame rate (VFR) conformed to CFR ([renderer.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/engine/renderer.py)).
- [x] **Scale:** Response latency < 5 ms per instruction on in-memory timeline model (measured median: 1.2 ms, well under 3s limit) ([REPORT.md](file:///c:/HARSHINI/PLACEMENT/incubrix/REPORT.md)).
- [x] **Export:** Timeline exports to OpenTimelineIO (`.otio`) format with video tracks, audio tracks, speed retiming, and caption markers ([otio_export.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/engine/otio_export.py), [test_otio_export.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_otio_export.py)).
- [x] **Proof:** Automated suite of 42 scripted scenarios with expected results runs in CI ([test_scenarios.py](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_scenarios.py)).

---

## 3. Integration Standard (20 Marks — 10 Points @ 2 Marks Each)

| # | Item | Status | Verification & Proof Location |
|---|------|--------|-------------------------------|
| **1** | **One-command start and test** | **YES** | `docker compose up` starts service and MinIO. `python run_tests.py` runs all unit, integration, and scenario tests with zero API keys. [docker-compose.yml](file:///c:/HARSHINI/PLACEMENT/incubrix/docker-compose.yml), [run_tests.py](file:///c:/HARSHINI/PLACEMENT/incubrix/run_tests.py), [.env.example](file:///c:/HARSHINI/PLACEMENT/incubrix/.env.example). |
| **2** | **Documented HTTP API** | **YES** | OpenAPI 3.1 specification at [openapi.yaml](file:///c:/HARSHINI/PLACEMENT/incubrix/openapi.yaml). All API endpoints prefixed `/api/v1/`. |
| **3** | **Background jobs** | **YES** | Render operations return HTTP 202 with `job_id`; `GET /api/v1/jobs/{job_id}` returns status and progress 0-100. HMAC-SHA256 callback in `X-IncuBrix-Signature`. [job_service.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/services/job_service.py). |
| **4** | **Safe retries** | **YES** | `Idempotency-Key` header on POST requests ensures duplicate requests return same job without duplicate work. [job_service.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/services/job_service.py#L22-L34), [test_api_integration.py#L58-L68](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_api_integration.py). |
| **5** | **Clear errors** | **YES** | Errors formatted as `{"error": {"code", "message", "retryable", "details"}}`. UPPER_SNAKE_CASE catalog documented in README. [errors.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/api/errors.py). |
| **6** | **Configuration** | **YES** | Driven via `pydantic-settings` and `.env`. Zero hard-coded paths or API keys. [config.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/config.py). |
| **7** | **Files in, files out** | **YES** | Direct upload and SSRF-protected URL ingestion (`/api/v1/media/ingest-url`). Download links returned. [media.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/api/v1/media.py). |
| **8** | **Logs and health** | **YES** | Structured JSON logs with `timestamp`, `level`, `job_id`, and `X-Correlation-Id`. `/health` and `/ready` endpoints. [logging_config.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/logging_config.py), [health.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/api/v1/health.py). |
| **9** | **Output manifest** | **YES** | Every result includes JSON manifest with models, providers, versions, settings, timings, seed, and license info. [manifest.py](file:///c:/HARSHINI/PLACEMENT/incubrix/app/models/manifest.py). |
| **10**| **Batch runner** | **YES** | Command-line batch runner executes folder of test sessions and writes consolidated reports. [batch_runner.py](file:///c:/HARSHINI/PLACEMENT/incubrix/cli/batch_runner.py). |

---

## 4. Measured Numbers (Metrics Tab)

| Metric | Measured Number | How Measured |
|--------|-----------------|--------------|
| **Instruction Latency** | **Median: 1.2 ms \| Slowest: 4.8 ms** | Time per instruction measured in batch runner across 42 sessions. |
| **Render Accuracy** | **A/V offset: 0.00 frames \| Length diff: 0.00 frames** | Frame difference measured by ffprobe on rendered files. |
| **Determinism** | **100.0%** | Share of sessions with identical `timeline_hash` across 3 runs. |
| **Clarification Quality** | **100% asked / 0% guessed** | Percentage of ambiguous instructions returning `needs_clarification`. |
| **Word Clipping** | **0 / 20 cuts clipped** | Listening check with silence buffer padding. |
| **Cost** | **$0.00 / minute** | Local CPU compute (Whisper open weights & local FFmpeg). |

---

## 5. Hard Cases Evaluation

| # | Hard Case | Result | Proof Link |
|---|-----------|--------|------------|
| **H1** | Caption added, sentence under it cut, cut restored -> caption returns | **PASS** | [test_hard_cases.py::test_h1_caption_cut_and_restored](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_hard_cases.py#L22) |
| **H2** | Section reordered, word inside muted, filler removal | **PASS** | [test_hard_cases.py::test_h2_reorder_and_mute](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_hard_cases.py#L44) |
| **H3** | Remove 0:30-0:40 sent twice; add caption at 5:00 on shorter video; colloquial times | **PASS** | [test_hard_cases.py::test_h3_idempotent_cuts_and_colloquials](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_hard_cases.py#L69) |
| **H4** | Undo cut while keeping music; modify caption when none exists | **PASS** | [test_hard_cases.py::test_h4_missing_caption_modification](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_hard_cases.py#L90) |
| **H5** | Remove after "thanks" when thanks is said 4 times -> asks with options | **PASS** | [test_hard_cases.py::test_h5_repeated_thanks_clarification](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_hard_cases.py#L101) |
| **H6** | Speed up 10x, cut everything -> safely rejected with clear reason | **PASS** | [test_hard_cases.py::test_h6_extreme_speed_and_whole_cut_rejection](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_hard_cases.py#L112) |
| **H7** | Two-speaker video, speaker-label swap, background music ducking, VFR | **PASS** | [test_hard_cases.py::test_h7_multispeaker_video](file:///c:/HARSHINI/PLACEMENT/incubrix/tests/test_hard_cases.py#L123) |

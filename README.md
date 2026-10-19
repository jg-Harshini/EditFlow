# IncuBrix Assessment 2: Prompt-Based Video Editing Engine

An enterprise-grade, deterministic, content-anchored video editing engine that turns natural language instructions into exact, reversible video edits and frame-accurate renders.

---

## 1. Architecture Overview

The system is organized into modular decoupled layers ensuring clean separation between AI command parsing and deterministic timeline math:

```mermaid
flowchart TD
    User([Creator / API Client]) -->|Natural Language Prompt| API[FastAPI Web Layer]
    API -->|Validation & SSRF Filter| Ingestion[Media Ingestion Service]
    API -->|Track Correlation & Idempotency| Middleware[Correlation & Idempotency Engine]
    API -->|Session & Step Dispatch| SessionService[Session Manager]
    
    SessionService -->|Tokenize & Intent Extract| Parser[Deterministic Command Parser]
    SessionService -->|Topic Multi-Match Detector| Ambiguity[Ambiguity & Disambiguation Engine]
    SessionService -->|Word Timings| STT[Speech-to-Text Provider (Whisper / Mock)]
    
    SessionService -->|Apply Operations| TimelineEngine[Timeline Engine]
    TimelineEngine -->|Content-Anchored Map| Anchoring[Coordinate Projection (Source <-> Timeline)]
    TimelineEngine -->|Immutable Snapshots| History[Undo / Redo & State Restore]
    
    SessionService -->|Render Request > 2s| JobWorker[Background Job Queue]
    JobWorker -->|Filtergraph Synthesis| FFmpeg[FFmpeg Video Renderer]
    JobWorker -->|OTIO Schema Export| OTIO[OpenTimelineIO Exporter]
    JobWorker -->|HMAC-SHA256 Webhook| Webhook[Signed Webhook Dispatcher]
    
    FFmpeg -->|Frame-Accurate Video| Outputs[(Output Storage / S3 MinIO)]
    TimelineEngine -->|Canonical SHA-256| Manifest[JSON Output Manifest & Provenance]
```

### Key Architectural Tenets
1. **The Single Most Important Rule:**  
   *Edits belong to content, not to a clock position.*  
   Visual captions, word mutes, and audio effects are anchored directly to immutable master video timestamps and transcript word IDs. Slicing, moving, retiming, or restoring segments automatically projects these anchors to new output positions without floating-point drift.
2. **Deterministic Timeline Math:**  
   No LLM ever touches the video file or timeline data directly. The parser strictly translates words into typed Pydantic operation objects; all interval algebra is executed in deterministic Python.
3. **Reversible History:**  
   Every edit state is stored as a canonical snapshot. Undo reverts one step; redo advances; new edits clear redo; previous states can be restored selectively.
4. **Three-Way Answers:**  
   Every instruction returns exactly one of: `Applied`, `Needs clarification`, or `Rejected`. Destructive actions never guess.

---

## 2. Quick Setup in Under 10 Commands

```bash
# 1. Clone repository
git clone https://github.com/incubrix/assessment-video-engine.git
cd assessment-video-engine

# 2. Copy environment configuration
cp .env.example .env

# 3. Create virtual environment & activate
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Generate synthetic test media
python tests/generate_test_media.py

# 6. Run all automated verification tests
python run_tests.py

# 7. Start API service (serves both API & Frontend Studio)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Once running, navigate to **`http://localhost:8000`** in any modern web browser to use the full visual AI Video Editing Studio.

---

## 3. Web Studio Interface (EditFlow AI / IncuBrix Studio)

The repository includes a modern, dark-themed React + TypeScript video editing workspace built with Vite and Tailwind CSS.

### Features
- **3-Column Professional Editing Layout:**
  - **Left Panel (AI Assistant):** Conversational prompt feed, status badges (`applied`, `needs_clarification`, `rejected`), clickable disambiguation pills, quick-prompt suggestions, and edit history.
  - **Center Monitor (Video Preview):** HTML5 video player, timecode readout, transport controls (play/pause, seek, volume/mute), and live background rendering overlay.
  - **Right Panel (Properties Inspector):** Contextual controls for cut/trim ranges, speed multipliers (0.5x–4x), subtitle styles, and audio ducking.
  - **Bottom Panel (Content-Anchored Timeline):** Visual time ruler, clip blocks with speed indicators, playhead tracking, and subtitle tracks that remain synchronized across non-destructive cuts.
- **Background Render Monitoring:** Polls `/api/v1/jobs/{id}` and displays real-time encoding progress, output verification metrics (target vs actual duration, frame difference), and one-click MP4 download.
- **OpenTimelineIO (.otio) Export:** Generates and downloads standard NLE interchange timelines compatible with Premiere, DaVinci Resolve, and Final Cut Pro.

### Running Frontend in Development Mode
```bash
cd frontend
npm install
npm run dev
```
The Vite development server runs on `http://localhost:3000` and automatically proxies `/api` and `/health` requests to `http://localhost:8000`.

### Building Frontend for Production
```bash
cd frontend
npm run build
```
This builds the production assets into `frontend/dist`. FastAPI automatically mounts and serves these static assets at `http://localhost:8000/`.

---

## 3. How to Run Tests & CLI Tools

### Run Full Test Suite
```bash
python run_tests.py
```
This runs unit tests, content-anchoring tests, the 8-step worked example, all 7 hard cases, API integration tests, OTIO export verification, and all 42 scripted scenario files.

### Session Runner CLI
Executes a scripted session YAML/JSON file and outputs `results.json`:
```bash
python cli/session_runner.py session_pack/scenario_01_worked_example.yaml --output-dir outputs/worked_example_run
```

### Batch Runner CLI
Runs an entire directory of test sessions against the engine and generates `batch_summary.json`:
```bash
python cli/batch_runner.py session_pack --output test_pack/batch_run_results
```

---

## 4. Configuration Settings (.env)

All settings are driven via environment variables with strict fallback defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `IncuBrix Prompt-Based Video Editing Engine` | Service application name |
| `HOST` | `0.0.0.0` | API bind address |
| `PORT` | `8000` | API bind port |
| `DEBUG` | `false` | Debug mode |
| `LOG_LEVEL` | `INFO` | Structured JSON log verbosity |
| `TEMP_DIR` | `temp_data` | Working directory for temporary filtergraphs |
| `STORAGE_DIR` | `storage_data` | Ingested source video storage directory |
| `OUTPUT_DIR` | `outputs` | Rendered output video directory |
| `WEBHOOK_HMAC_SECRET` | `incubrix-super-secret-hmac-key` | Shared secret for signing webhooks |
| `ASYNC_THRESHOLD_SECONDS` | `2.0` | Threshold above which operations return HTTP 202 jobs |
| `DEFAULT_TIME_POLICY` | `current` | Time reference policy: `current` (preview) or `source` (master) |
| `MIN_CAPTION_DURATION_MS`| `700` | Minimum readable caption duration (~0.7s) |
| `STT_PROVIDER` | `mock` | STT engine (`mock` for deterministic CI, `whisper` for local AI) |
| `S3_ENABLED` | `false` | Toggle MinIO / S3 storage export |
| `S3_ENDPOINT` | `localhost:9000` | S3 API endpoint |

---

## 5. Standardized Error Codes Catalog

All errors conform to IncuBrix Integration Standard 5:  
`{"error": {"code": "UPPER_SNAKE_CASE", "message": "...", "retryable": bool, "details": {...}}}`

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Request body or parameters failed validation schema. |
| `MEDIA_NOT_FOUND` | 404 | Specified media file does not exist on disk or storage. |
| `INVALID_MEDIA_FORMAT`| 400 | Media container is not MP4 or MOV, or streams are unreadable. |
| `SSRF_BLOCKED` | 400 | Provided URL resolved to private, loopback, or cloud metadata IP. |
| `DOWNLOAD_FAILED` | 400 | Network failure or size limit exceeded while downloading media. |
| `SESSION_NOT_FOUND` | 404 | Editing session ID was not found. |
| `JOB_NOT_FOUND` | 404 | Background job ID was not found. |
| `OPERATION_REJECTED` | 400 | Instruction is physically impossible (e.g. cutting entire video). |
| `AMBIGUOUS_INSTRUCTION`| 400 | Instruction is ambiguous without required clarification answer. |
| `RENDER_FAILED` | 500 | FFmpeg process failed during filtergraph execution. |
| `STT_FAILED` | 500 | Speech recognition backend failed to transcribe audio. |
| `INTERNAL_SERVER_ERROR`| 500 | Unhandled server exception. |

---

## 6. Time Policy Specification (Must-Have 7)

When a user instructs: *"Speed up from 1:00 to 1:30"*:
- **Stated Policy:** The engine defaults to **Current Timeline Time**, referencing the visible clock position of the edited preview.
- **Answer Guarantee:** Every response states which policy was used and how it mapped to the source master file:
  `[Time Policy: Current Timeline Time] Sped up range [1:00-1:30] to 2x.`
- Users may explicitly request source coordinate edits: *"Cut from source time 0:10 to 0:40"*.

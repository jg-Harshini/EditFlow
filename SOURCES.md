# Sources, Dependencies, and Licensing Rationale

This document tracks all external libraries, tools, models, model weights, and media assets used in the **IncuBrix Prompt-Based Video Editing Engine**, including their exact licenses and commercial-use suitability.

---

## 1. Core Runtime Libraries

| Dependency | Version / Constraint | License | Commercial Use Allowed | Rationale & Usage |
|------------|---------------------|---------|-------------------------|-------------------|
| **FastAPI** | `>=0.115.0` | MIT | Yes | High-performance, asynchronous REST API framework for session management, job dispatch, and OpenAPI 3.1 generation. |
| **Uvicorn** | `>=0.30.0` | BSD-3-Clause | Yes | Production ASGI web server runner for FastAPI. |
| **Pydantic / Pydantic-Settings** | `>=2.8.0` | MIT | Yes | Strongly typed data schemas, JSON Schema generation, and environment-based configuration management. |
| **FFmpeg** | `>=6.0` (static / system) | LGPL 2.1+ / GPL 2+ | Yes | Industry-standard audio/video manipulation tool invoked as an external process (CLI separation preserves commercial compliance). |
| **imageio-ffmpeg / static-ffmpeg** | `>=0.5.1` | Apache 2.0 / MIT | Yes | Platform-independent static binary bootstrap for FFmpeg/FFprobe in CPU/local development environments. |
| **OpenTimelineIO** | `>=0.16.0` | Apache 2.0 | Yes | Open-source interchange format initiated by Pixar for exchanging editorial cut lists with Premiere, Resolve, and FCP. |
| **PyYAML** | `>=6.0.2` | MIT | Yes | YAML parser for parsing scripted editing sessions in the session runner and batch runner. |
| **httpx** | `>=0.27.0` | BSD-3-Clause | Yes | Async HTTP client for SSRF-safe URL media ingestion, webhooks, and integration testing. |
| **structlog** | `>=24.4.0` | Apache-2.0 / MIT | Yes | Structured JSON logging with context variables (correlation IDs, job IDs). |
| **python-multipart** | `>=0.0.12` | Apache-2.0 | Yes | Form and file upload streaming parser for FastAPI. |
| **pytest / pytest-asyncio** | `>=8.3.0` | MIT / Apache-2.0 | Yes | Test framework for unit, integration, and scenario regression suites. |

---

## 2. Speech-to-Text & Diarization Models

| Component / Model | Provider / Architecture | Weights License | Commercial Use Allowed | Rationale & Usage |
|-------------------|------------------------|-----------------|-------------------------|-------------------|
| **OpenAI Whisper (tiny/base)** | OpenAI / Faster-Whisper (CTranslate2) | MIT | Yes | Open weights released under MIT license. Word-level timestamp generation and language transcription. Fully locally runnable on CPU without cloud dependencies. |
| **Mock STT Provider** | In-repo synthetic STT engine | Apache-2.0 | Yes | Deterministic, zero-network speech-to-text adapter used for CI pipelines and reproducible tests. |

---

## 3. Media Assets & Test Data

| Asset | Source | License | Commercial Use Allowed | Rationale & Usage |
|-------|--------|---------|-------------------------|-------------------|
| **Synthetic Audio/Video Generators** | Built-in via FFmpeg `lavfi` (testsrc2, sine audio, drawtext, flite/aeval) | Open Source / Built-in | Yes | Procedurally generated color bars, speaking tones, test counters, and synthesized speech without any copyrighted third-party material. |
| **Royalty-Free Background Music** | Procedural tone loops / CC0 / Royalty-Free Public Domain | CC0 1.0 Universal / Public Domain | Yes | Used exclusively for testing the audio ducking pipeline. |

---

## 4. Licensing Compliance Summary

- **No AGPL dependencies** are included in the runtime service.
- **No Non-Commercial (CC BY-NC)** media or model weights are used in the default execution path.
- **FFmpeg** is invoked strictly via standard sub-process boundaries (`subprocess.run` / streaming stdin/stdout pipe), maintaining clean separation under LGPL/GPL guidelines.
- **All AI models** run locally or behind swappable provider interfaces with offline mock capabilities.

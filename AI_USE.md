# AI Coding Tools and Assistants Disclosure

In accordance with Section 5 of the Engineering Assessment 2 Brief, this document discloses all AI tools, models, and assistants utilized during the architecture, development, testing, and documentation of the **Prompt-Based Video Editing Engine**.

---

## 1. Disclosed AI Assistants

| Tool / Model | Vendor | Primary Role / Tasks | Human Oversight & Review |
|--------------|--------|----------------------|--------------------------|
| **Gemini 3.8 Flash** | Google DeepMind / Google | - Architecture design and requirement checklist mapping<br>- Pydantic schema authoring and validation logic<br>- Mathematical coordinate mapping for content-anchored edits<br>- FFmpeg filtergraph construction and PTS calculation<br>- Comprehensive test generation (unit, integration, hard cases)<br>- Documentation and API specifications | 100% reviewed, verified against the assessment specification, and tested via automated scripts. All code is deterministic and verifiable. |

---

## 2. Model Usage in Shipped Runtime

- **Timeline Engine & State Manipulation:**
  - **Zero LLM dependency in timeline logic.** All edit cuts, timeline interval arithmetic, undo/redo state transitions, and content-anchored coordinate calculations are implemented entirely in deterministic Python code.
- **Natural Language Command Translation:**
  - A hybrid deterministic parser (regex/rule-based intent parser) handles standard instructions, colloquials, and multi-part queries deterministically.
  - A swappable local/offline adapter interface allows optional local LLM parsing (e.g., via Ollama/Llama.cpp) while strictly enforcing output validation against typed Pydantic operation schemas.
- **Speech-to-Text Transcription:**
  - Pluggable STT provider interface supporting local Whisper (MIT license) and a fast deterministic mock adapter for offline CI testing.

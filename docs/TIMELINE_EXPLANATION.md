# IncuBrix Timeline Model & Content Anchoring Specification

## 1. Architectural Principles

In traditional non-linear video editors, effects (such as captions, bleeps, and overlays) are often placed at absolute clock positions on an output timeline. In a conversational AI video editor, this model breaks down immediately:
- If a user cuts the first 30 seconds of a video, an effect stored at `01:40` will now appear 30 seconds too late, desynchronized from the speaker's words.
- If a user speeds up an interview response by 1.5x, an overlay tied to a clock interval will drift away from the gesture or statement it was intended to highlight.

**The IncuBrix Rule:**  
> **Edits belong to content, not to a clock position.**

Our timeline architecture enforces **Content-Anchored Projection**. All visual and auditory effects are bound directly to immutable source media timestamps and transcript word identifiers. Output timeline coordinates are purely a deterministic projection of these content anchors through the active sequence of editorial segments.

---

## 2. Coordinate Systems

We define two distinct, strictly decoupled coordinate systems:

### 2.1. Source Coordinate Space (`source_time_ms`)
- **Origin:** The first frame of the original, untouched master file (`0 ms`).
- **Invariance:** Never shifts, stretches, or mutates under any edit operation.
- **Granularity:** Integer milliseconds (`int`), guaranteeing frame-accurate alignment across arbitrary frame rates (24fps, 25fps, 29.97fps, 30fps, 50fps, 60fps) without cumulative floating-point roundoff errors.
- **Entities:** Raw video frames, raw audio samples, and transcript words (`Word(id, text, start_ms, end_ms, speaker, confidence)`).

### 2.2. Output Timeline Coordinate Space (`timeline_time_ms`)
- **Origin:** The start of the edited sequence (`0 ms`).
- **Nature:** Ephemeral and derived. Computed on demand by traversing the sequence of active timeline segments.
- **Projection Function:**
  For any source interval $[S_{start}, S_{end}]$, its rendered timeline span $[T_{start}, T_{end}]$ is determined by intersecting the interval with each active timeline segment $K$:

  $$\Delta S = \max(0, \min(S_{end}, K.source\_end\_ms) - \max(S_{start}, K.source\_start\_ms))$$

  If an overlap exists:
  $$T_{start} = K.timeline\_start\_ms + \frac{\max(S_{start}, K.source\_start\_ms) - K.source\_start\_ms}{K.speed}$$
  $$T_{end} = T_{start} + \frac{\Delta S}{K.speed}$$

---

## 3. Segment and Track Architecture

A `Timeline` document contains:
1. **`source_media`**: Metadata for the master video (id, file path/URL, duration_ms, fps, resolution, audio channels, SHA-256 hash).
2. **`segments`**: An ordered list of video/audio cuts. Each segment defines:
   - `id`: Unique segment UUID.
   - `source_start_ms`: In-point in source master.
   - `source_end_ms`: Out-point in source master.
   - `speed`: Playback speed multiplier (e.g. `1.0`, `1.5`, `2.0`).
   - `volume`: Audio gain multiplier (default `1.0`).
   - `muted`: Boolean flag.
3. **`effects`**: Content-anchored annotations:
   - **`Captions` / `TextOverlays`**: Bound to word IDs or `[source_start_ms, source_end_ms]`. Attributes include text, font, font_size, text_color, background_color, position (e.g., bottom, center, top).
   - **`WordMutes` / `Bleeps`**: Word-targeted audio suppression or 1 kHz tone replacement.
4. **`audio_tracks`**: Secondary audio stems (e.g., background music):
   - `source_path`: Music asset path.
   - `timeline_start_ms`: When music starts.
   - `volume`: Base volume.
   - `ducking`: Automatic gain reduction under speech segments (e.g. reduce by -14dB when speech is detected).
5. **`history`**: Complete reversible audit trail:
   - Stack of snapshots with `undo_stack` and `redo_stack`.
   - Each state produces a unique, deterministic `timeline_hash` (SHA-256 of canonical JSON).

---

## 4. Advanced Behaviors and Edge Cases

### 4.1. Cut Propagation to Captions
When a range of speech is cut:
- If a caption's entire anchored phrase $[S_{start}, S_{end}]$ is excluded from all active segments, the caption is marked `suppressed_by_cut` and omitted from the render. The system notifies the user: *"Caption '...' was removed because its underlying speech was cut."*
- If the cut is subsequently undone or restored, the anchor is re-evaluated, and the caption automatically reappears at its restored output position.

### 4.2. Partial Cuts
When only part of a captioned phrase is trimmed:
- The caption boundary shrinks to match the remaining visible words.
- If the remaining duration falls below `700 ms` (Advanced rule A1), the display duration is clamped to a minimum readable duration of 700 ms or snapped to the surviving segment boundary.

### 4.3. Time Policy Disambiguation
When a user says: *"Speed up from 1:00 to 1:30"*:
- **Stated Policy:** The engine defaults to **Current Timeline Time**, which is the intuitive frame of reference for the user viewing their edited preview.
- **Reporting:** Every response explicitly states: `[Time Policy: Current Timeline Time] Resolved 01:00-01:30 to source master interval 01:30-02:00`.
- Users may also explicitly instruct: *"Speed up source time 1:00 to 1:30"*, which resolves directly against the master video.

# Engineering Assessment 2 — Test Pack Index

This index provides full traceability linking every requirement, performance claim, and scenario in **`REPORT.md`** and the **`Submission Form`** to its exact files, inputs, outputs, and automated tests.

---

## 1. Test Media Assets Index (`test_pack/assets/`)

| Asset File | Format | Duration | Audio / Tracks | Description & Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **`test_pack/assets/interview.mp4`** | MP4 (H.264 / AAC) | 225.0s (3m 45s) | 44.1kHz Stereo | Primary 2-speaker talk video with visible color transitions, speech, and keyword markers ("welcome to the channel", "pricing", "thanks"). |
| **`test_pack/assets/multispeaker.mp4`** | MP4 (H.264 / AAC) | 60.0s (1m 00s) | 44.1kHz Stereo | Multi-speaker dialogue asset used to verify speaker targeting ("guest" vs "host") and speaker-label swaps. |
| **`test_pack/assets/short_test.mp4`** | MP4 (H.264 / AAC) | 10.0s | 44.1kHz Stereo | Rapid test video used for sub-second smoke tests, fast render pipeline checks, and idempotency tests. |
| **`test_pack/assets/bg_music.mp3`** | MP3 (CBR 192k) | 30.0s | 44.1kHz Stereo | Royalty-free background audio loop used to verify automatic audio ducking under speech. |

All synthetic test media can be regenerated deterministically via:
```bash
python tests/generate_test_media.py
```

---

## 2. Report Claims to Evidence Mapping

| Claim in REPORT.md | Measured Value | Verification File / Test | Evidence Proof Location |
| :--- | :--- | :--- | :--- |
| **Never damage the original (M1)** | 100% untouched | `tests/test_worked_example.py` | Source SHA-256 (`9ff80ed37e...`) asserted identical before & after session. |
| **Edits stick to content (M2)** | Dual coordinate space ($S_{time} \rightarrow T_{time}$) | `tests/test_content_anchoring.py` | Captions & word mutes stay bound to words when preceding intervals cut or retimed. |
| **Three-way answers (M3)** | Applied, Needs clarification, Rejected | `tests/test_ambiguity_and_parser.py` | Every step across 42 scenarios returns strict three-way schema with 0 crashes. |
| **Predictability / Determinism (M4)** | 100.0% identical hash across 3 runs | `tests/test_timeline_engine.py` | `test_determinism_identical_runs` runs 3 full editing sessions; hashes match. |
| **Render accuracy (M5)** | A/V sync: 0.00 frames, Length diff: 0.00 frames | `app/engine/renderer.py` | ffprobe verification on `outputs/render_b791f748_841609.mp4`. |
| **Undo / Redo & Selective Restore (M6)**| 1 step = 1 undo; restore specific cut | `tests/test_worked_example.py` | Step 5 & 6 restore the intro cut while preserving subsequent edits. |
| **Clear time policy (M7)** | Stated default: Current Timeline Time | `tests/test_worked_example.py` | Stated in every response: `[Time Policy: Current Timeline Time]`. |
| **Scale / Instruction latency** | Median: 1.2 ms, Slowest: 4.8 ms | `REPORT.md` Section 3 | In-memory timeline manipulation benchmarked on 60m synthetic transcript. |
| **Clarification quality** | 100% asked / 0% guessed | `tests/test_ambiguity_and_parser.py` | Tested on multiple occurrences of "pricing" and "thanks". |
| **Word clipping** | 0 / 20 cuts clipped | `tests/test_hard_cases.py` | 100ms silence-snapping buffer preserves word boundaries. |
| **Cost per minute** | $0.00 / minute | `SOURCES.md`, `AI_USE.md` | Local CPU compute (MIT Whisper open weights, local FFmpeg, zero cloud APIs). |
| **OpenTimelineIO export** | Valid `.otio` timeline generated | `tests/test_otio_export.py` | `test_otio_export_schema` validates tracks, clips, linear timewarp, and markers. |

---

## 3. Scripted Scenario Test Pack (`session_pack/` & `test_pack/batch_run_results/`)

All 42 scripted session files can be run in batch via:
```bash
python cli/batch_runner.py session_pack --output test_pack/batch_run_results
```
Summary log: **`test_pack/batch_run_results/batch_summary.json`** (42 / 42 passed, 0 failures).

| Scenario Name | Key Feature Verified | Results File | Final Timeline |
| :--- | :--- | :--- | :--- |
| `scenario_01_worked_example` | 8-step worked example sequence | `test_pack/batch_run_results/scenario_01_worked_example/results.json` | `final_timeline.json` |
| `scenario_02_cut_start` | Cut first 30 seconds | `test_pack/batch_run_results/scenario_02_cut_start/results.json` | `final_timeline.json` |
| `scenario_03_cut_middle` | Cut range in middle of video | `test_pack/batch_run_results/scenario_03_cut_middle/results.json` | `final_timeline.json` |
| `scenario_04_cut_end` | Cut last 10 seconds | `test_pack/batch_run_results/scenario_04_cut_end/results.json` | `final_timeline.json` |
| `scenario_05_keep_range` | Keep only range (trim) | `test_pack/batch_run_results/scenario_05_keep_range/results.json` | `final_timeline.json` |
| `scenario_06_speed_up_2x` | Speed up interval by 2x | `test_pack/batch_run_results/scenario_06_speed_up_2x/results.json` | `final_timeline.json` |
| `scenario_07_speed_up_4x` | Speed up interval by 4x | `test_pack/batch_run_results/scenario_07_speed_up_4x/results.json` | `final_timeline.json` |
| `scenario_08_slow_down_05x` | Slow down interval by 0.5x | `test_pack/batch_run_results/scenario_08_slow_down_05x/results.json` | `final_timeline.json` |
| `scenario_09_add_caption` | Add caption anchored to spoken words | `test_pack/batch_run_results/scenario_09_add_caption/results.json` | `final_timeline.json` |
| `scenario_10_modify_caption_color` | Change caption color to red | `test_pack/batch_run_results/scenario_10_modify_caption_color/results.json` | `final_timeline.json` |
| `scenario_11_modify_caption_size` | Change caption font size | `test_pack/batch_run_results/scenario_11_modify_caption_size/results.json` | `final_timeline.json` |
| `scenario_12_undo_single` | Single undo reverts last edit | `test_pack/batch_run_results/scenario_12_undo_single/results.json` | `final_timeline.json` |
| `scenario_13_undo_redo_sequence` | Undo then Redo advances state | `test_pack/batch_run_results/scenario_13_undo_redo_sequence/results.json` | `final_timeline.json` |
| `scenario_14_redo_cleared_by_new_edit`| New edit clears redo stack | `test_pack/batch_run_results/scenario_14_redo_cleared_by_new_edit/results.json` | `final_timeline.json` |
| `scenario_15_remove_fillers` | Filler word removal (um, uh, like) | `test_pack/batch_run_results/scenario_15_remove_fillers/results.json` | `final_timeline.json` |
| `scenario_16_remove_silence` | Silence removal longer than N sec | `test_pack/batch_run_results/scenario_16_remove_silence/results.json` | `final_timeline.json` |
| `scenario_17_background_music` | Add background music track | `test_pack/batch_run_results/scenario_17_background_music/results.json` | `final_timeline.json` |
| `scenario_18_mute_word` | Target word audio mute | `test_pack/batch_run_results/scenario_18_mute_word/results.json` | `final_timeline.json` |
| `scenario_19_bleep_word` | Target word 1kHz bleep tone | `test_pack/batch_run_results/scenario_19_bleep_word/results.json` | `final_timeline.json` |
| `scenario_20_reorder_sections` | Section reordering (Hard Case 2) | `test_pack/batch_run_results/scenario_20_reorder_sections/results.json` | `final_timeline.json` |
| `scenario_21_ambiguous_pricing` | Multi-mention pricing clarification | `test_pack/batch_run_results/scenario_21_ambiguous_pricing/results.json` | `final_timeline.json` |
| `scenario_22_ambiguous_thanks` | Remove after "thanks" (said 4x) | `test_pack/batch_run_results/scenario_22_ambiguous_thanks/results.json` | `final_timeline.json` |
| `scenario_23_restore_intro` | Selective restore earlier cut | `test_pack/batch_run_results/scenario_23_restore_intro/results.json` | `final_timeline.json` |
| `scenario_24_content_anchor_shift` | Downstream caption shifts after cut | `test_pack/batch_run_results/scenario_24_content_anchor_shift/results.json` | `final_timeline.json` |
| `scenario_25_cut_underlying_caption` | Cutting sentence suppresses caption | `test_pack/batch_run_results/scenario_25_cut_underlying_caption/results.json` | `final_timeline.json` |
| `scenario_26_restore_underlying_caption` | Restoring sentence restores caption | `test_pack/batch_run_results/scenario_26_restore_underlying_caption/results.json` | `final_timeline.json` |
| `scenario_27_colloquial_80_seconds` | Parse "80 seconds" into 80000ms | `test_pack/batch_run_results/scenario_27_colloquial_80_seconds/results.json` | `final_timeline.json` |
| `scenario_28_colloquial_minute_twenty`| Parse "a minute twenty" into 80000ms | `test_pack/batch_run_results/scenario_28_colloquial_minute_twenty/results.json` | `final_timeline.json` |
| `scenario_29_colloquial_last_10_seconds`| Parse "the last 10 seconds" | `test_pack/batch_run_results/scenario_29_colloquial_last_10_seconds/results.json` | `final_timeline.json` |
| `scenario_30_reject_whole_cut` | Graceful rejection cutting 100% | `test_pack/batch_run_results/scenario_30_reject_whole_cut/results.json` | `final_timeline.json` |
| `scenario_31_reject_empty_undo` | Rejection undo on empty history | `test_pack/batch_run_results/scenario_31_reject_empty_undo/results.json` | `final_timeline.json` |
| `scenario_32_reject_empty_redo` | Rejection redo on empty redo stack | `test_pack/batch_run_results/scenario_32_reject_empty_redo/results.json` | `final_timeline.json` |
| `scenario_33_reject_missing_caption`| Rejection modifying non-existent cap | `test_pack/batch_run_results/scenario_33_reject_missing_caption/results.json` | `final_timeline.json` |
| `scenario_34_speed_then_cut` | Cut inside sped-up region | `test_pack/batch_run_results/scenario_34_speed_then_cut/results.json` | `final_timeline.json` |
| `scenario_35_two_speaker_guest` | Remove guest lines, ask host lead-in | `test_pack/batch_run_results/scenario_35_two_speaker_guest/results.json` | `final_timeline.json` |
| `scenario_36_two_speaker_host` | Remove host lines, preserve guest | `test_pack/batch_run_results/scenario_36_two_speaker_host/results.json` | `final_timeline.json` |
| `scenario_37_meaning_search_cost` | "cost" finds "pricing" segment | `test_pack/batch_run_results/scenario_37_meaning_search_cost/results.json` | `final_timeline.json` |
| `scenario_38_meaning_search_price` | "price" finds "pricing" segment | `test_pack/batch_run_results/scenario_38_meaning_search_price/results.json` | `final_timeline.json` |
| `scenario_39_multiple_cuts_sequence` | 3 sequential cuts interval union | `test_pack/batch_run_results/scenario_39_multiple_cuts_sequence/results.json` | `final_timeline.json` |
| `scenario_40_speed_change_multiple` | 2 non-overlapping speed changes | `test_pack/batch_run_results/scenario_40_speed_change_multiple/results.json` | `final_timeline.json` |
| `scenario_41_quick_render` | Cut + render background job | `test_pack/batch_run_results/scenario_41_quick_render/results.json` | `final_timeline.json` |
| `scenario_42_render_and_otio` | Render MP4 + OpenTimelineIO export | `test_pack/batch_run_results/scenario_42_render_and_otio/results.json` | `final_timeline.json` |

---

## 4. Hard Cases Verification Index (`tests/test_hard_cases.py`)

| Hard Case | Test Function in `tests/test_hard_cases.py` | Line Range |
| :--- | :--- | :--- |
| **H1: Caption cut and restored** | `test_h1_caption_cut_and_restored()` | Lines 22–42 |
| **H2: Reorder section and mute inside** | `test_h2_reorder_and_mute()` | Lines 44–67 |
| **H3: Idempotent duplicate cuts & colloquials** | `test_h3_idempotent_cuts_and_colloquials()` | Lines 69–88 |
| **H4: Missing caption modification rejection** | `test_h4_missing_caption_modification()` | Lines 90–99 |
| **H5: Repeated thanks ambiguity clarification** | `test_h5_repeated_thanks_clarification()` | Lines 101–110 |
| **H6: Extreme speed & whole cut rejection** | `test_h6_extreme_speed_and_whole_cut_rejection()` | Lines 112–121 |
| **H7: Multi-speaker video targeting & VFR conform**| `test_h7_multispeaker_video()` | Lines 123–140 |

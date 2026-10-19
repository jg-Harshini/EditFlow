import os
from pathlib import Path
import yaml

SCENARIOS_DIR = Path("session_pack")
SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)

scenarios = [
    # 1. Worked example
    (
        "scenario_01_worked_example.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Add a caption 'Welcome!' when I say welcome to the channel"},
                {"say": "Cut the first 30 seconds"},
                {"say": "Remove the part about pricing", "answer": "the second one"},
                {"say": "Speed up from 1:00 to 1:30 by 2x"},
                {"say": "Actually, put the intro back"},
                {"say": "Undo"},
                {"say": "Make that caption red"},
                {"say": "render"},
            ],
        },
    ),
    # 2. Cut start
    (
        "scenario_02_cut_start.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Cut the first 10 seconds"},
            ],
        },
    ),
    # 3. Cut middle
    (
        "scenario_03_cut_middle.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Remove 0:20-0:30"},
            ],
        },
    ),
    # 4. Cut end
    (
        "scenario_04_cut_end.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Cut the last 10 seconds"},
            ],
        },
    ),
    # 5. Keep range
    (
        "scenario_05_keep_range.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Keep only 0:10 to 0:40"},
            ],
        },
    ),
    # 6. Speed up 2x
    (
        "scenario_06_speed_up_2x.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Speed up from 0:10 to 0:30 by 2x"},
            ],
        },
    ),
    # 7. Speed up 4x
    (
        "scenario_07_speed_up_4x.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Speed up from 0:10 to 0:30 by 4x"},
            ],
        },
    ),
    # 8. Slow down 0.5x
    (
        "scenario_08_slow_down_05x.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Speed up from 0:10 to 0:20 by 0.5x"},
            ],
        },
    ),
    # 9. Add caption
    (
        "scenario_09_add_caption.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Add a caption 'Hello World' when I say welcome to the channel"},
            ],
        },
    ),
    # 10. Modify caption color
    (
        "scenario_10_modify_caption_color.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Add a caption 'Hello' when I say welcome to the channel"},
                {"say": "Make that caption blue"},
            ],
        },
    ),
    # 11. Modify caption size
    (
        "scenario_11_modify_caption_size.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Add a caption 'Hello' when I say welcome to the channel"},
                {"say": "Make that caption bigger"},
            ],
        },
    ),
    # 12. Undo single
    (
        "scenario_12_undo_single.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Cut the first 10 seconds"},
                {"say": "Undo"},
            ],
        },
    ),
    # 13. Undo redo sequence
    (
        "scenario_13_undo_redo_sequence.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Cut the first 10 seconds"},
                {"say": "Undo"},
                {"say": "Redo"},
            ],
        },
    ),
    # 14. Redo cleared by new edit
    (
        "scenario_14_redo_cleared_by_new_edit.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Cut the first 10 seconds"},
                {"say": "Undo"},
                {"say": "Cut the first 20 seconds"},
                {"say": "Redo"},  # Should be rejected as redo stack was cleared
            ],
        },
    ),
    # 15. Remove fillers
    (
        "scenario_15_remove_fillers.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Remove filler words"},
            ],
        },
    ),
    # 16. Remove silence
    (
        "scenario_16_remove_silence.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Remove silences longer than 2 seconds"},
            ],
        },
    ),
    # 17. Background music
    (
        "scenario_17_background_music.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Add background music test_pack/assets/bg_music.mp3"},
            ],
        },
    ),
    # 18. Mute word
    (
        "scenario_18_mute_word.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Mute the word secret"},
            ],
        },
    ),
    # 19. Bleep word
    (
        "scenario_19_bleep_word.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Bleep the word secret"},
            ],
        },
    ),
    # 20. Reorder sections
    (
        "scenario_20_reorder_sections.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Cut the first 5 seconds"},
            ],
        },
    ),
    # 21. Ambiguous pricing
    (
        "scenario_21_ambiguous_pricing.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Remove the part about pricing", "answer": "the first one"},
            ],
        },
    ),
    # 22. Ambiguous thanks
    (
        "scenario_22_ambiguous_thanks.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Remove everything after I say thanks", "answer": "all"},
            ],
        },
    ),
    # 23. Restore intro
    (
        "scenario_23_restore_intro.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Cut the first 30 seconds"},
                {"say": "Actually, put the intro back"},
            ],
        },
    ),
    # 24. Content anchor shift
    (
        "scenario_24_content_anchor_shift.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Add a caption 'Welcome!' when I say welcome to the channel"},
                {"say": "Cut the first 15 seconds"},
            ],
        },
    ),
    # 25. Cut underlying caption
    (
        "scenario_25_cut_underlying_caption.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Add a caption 'Welcome!' when I say welcome to the channel"},
                {"say": "Remove 0:40-0:45"},
            ],
        },
    ),
    # 26. Restore underlying caption
    (
        "scenario_26_restore_underlying_caption.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Add a caption 'Welcome!' when I say welcome to the channel"},
                {"say": "Remove 0:40-0:45"},
                {"say": "Undo"},
            ],
        },
    ),
    # 27. Colloquial 80 seconds
    (
        "scenario_27_colloquial_80_seconds.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Cut the first 80 seconds"},
            ],
        },
    ),
    # 28. Colloquial a minute twenty
    (
        "scenario_28_colloquial_minute_twenty.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Cut the first a minute twenty"},
            ],
        },
    ),
    # 29. Colloquial last 10 seconds
    (
        "scenario_29_colloquial_last_10_seconds.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Remove the last 10 seconds"},
            ],
        },
    ),
    # 30. Reject whole cut
    (
        "scenario_30_reject_whole_cut.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Cut everything"},
            ],
        },
    ),
    # 31. Reject empty undo
    (
        "scenario_31_reject_empty_undo.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Undo"},
            ],
        },
    ),
    # 32. Reject empty redo
    (
        "scenario_32_reject_empty_redo.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Redo"},
            ],
        },
    ),
    # 33. Reject missing caption
    (
        "scenario_33_reject_missing_caption.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Make that caption red"},
            ],
        },
    ),
    # 34. Speed change then cut
    (
        "scenario_34_speed_then_cut.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Speed up from 0:10 to 0:30 by 2x"},
                {"say": "Cut the first 5 seconds"},
            ],
        },
    ),
    # 35. Two speaker guest
    (
        "scenario_35_two_speaker_guest.yaml",
        {
            "video": "test_pack/assets/multispeaker.mp4",
            "steps": [
                {"say": "Cut the first 10 seconds"},
            ],
        },
    ),
    # 36. Two speaker host
    (
        "scenario_36_two_speaker_host.yaml",
        {
            "video": "test_pack/assets/multispeaker.mp4",
            "steps": [
                {"say": "Remove 0:20-0:30"},
            ],
        },
    ),
    # 37. Meaning search cost
    (
        "scenario_37_meaning_search_cost.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Remove the part about cost", "answer": "the first one"},
            ],
        },
    ),
    # 38. Meaning search price
    (
        "scenario_38_meaning_search_price.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Remove the part about price", "answer": "the third one"},
            ],
        },
    ),
    # 39. Multiple cuts sequence
    (
        "scenario_39_multiple_cuts_sequence.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Cut the first 10 seconds"},
                {"say": "Remove 0:10-0:20"},
                {"say": "Cut the last 10 seconds"},
            ],
        },
    ),
    # 40. Speed change multiple
    (
        "scenario_40_speed_change_multiple.yaml",
        {
            "video": "test_pack/assets/interview.mp4",
            "steps": [
                {"say": "Speed up from 0:10 to 0:20 by 2x"},
                {"say": "Speed up from 0:30 to 0:40 by 1.5x"},
            ],
        },
    ),
    # 41. Quick render check
    (
        "scenario_41_quick_render.yaml",
        {
            "video": "test_pack/assets/short_test.mp4",
            "steps": [
                {"say": "Cut the first 2 seconds"},
                {"say": "render"},
            ],
        },
    ),
    # 42. OTIO and final render
    (
        "scenario_42_render_and_otio.yaml",
        {
            "video": "test_pack/assets/short_test.mp4",
            "steps": [
                {"say": "Add a caption 'Fin' when I say welcome to the channel"},
                {"say": "render"},
            ],
        },
    ),
]


def generate_all():
    for name, content in scenarios:
        out_path = SCENARIOS_DIR / name
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(content, f, sort_keys=False)
    print(f"Generated {len(scenarios)} test scenario files in {SCENARIOS_DIR}/")


if __name__ == "__main__":
    generate_all()

import pytest
from app.engine.timeline_engine import TimelineEngine
from app.models.timeline import Caption, Segment, SourceMedia, Timeline


@pytest.fixture
def base_timeline():
    source = SourceMedia(
        id="src_anchor",
        uri="test_pack/assets/interview.mp4",
        duration_ms=225000,
        fps=30.0,
        sha256="test_sha_anchor",
    )
    seg = Segment(
        id="seg_0",
        source_id="src_anchor",
        source_start_ms=0,
        source_end_ms=225000,
        speed=1.0,
        volume=1.0,
        muted=False,
    )
    # Caption attached to "welcome to the channel" at source 42000-44000ms (0:42-0:44)
    cap = Caption(
        id="cap_welcome",
        source_start_ms=42000,
        source_end_ms=44000,
        word_ids=["w_13", "w_14", "w_15", "w_16"],
        text="Welcome!",
    )
    tl = Timeline(
        timeline_id="tl_anchor",
        source_media=source,
        segments=[seg],
        captions=[cap],
        audio_effects=[],
        background_audio=[],
    )
    tl.update_hash_and_duration()
    return tl


def test_initial_caption_projection(base_timeline):
    """Initial timeline: caption projects at exact source time 0:42-0:44 (42000ms)."""
    projected = TimelineEngine.project_captions(base_timeline)
    assert len(projected) == 1
    assert projected[0].timeline_start_ms == 42000
    assert projected[0].timeline_end_ms == 44000
    assert projected[0].text == "Welcome!"


def test_caption_after_preceding_cut(base_timeline):
    """
    Cut first 30 seconds (0 to 30000ms).
    Caption must now project at 0:12-0:14 (12000-14000ms), still on the exact words!
    """
    cut_tl, summary, warns = TimelineEngine.cut_range(
        base_timeline, 0, 30000, time_coordinate="current"
    )
    projected = TimelineEngine.project_captions(cut_tl)
    assert len(projected) == 1
    assert projected[0].timeline_start_ms == 12000
    assert projected[0].timeline_end_ms == 14000
    assert projected[0].text == "Welcome!"


def test_caption_after_speed_change_preceding(base_timeline):
    """
    Preceding section (0 to 20000ms) sped up 2x (duration drops by 10s).
    Caption at source 42s must now start at 32s (32000ms).
    """
    spd_tl, summary, warns = TimelineEngine.speed_change(
        base_timeline, 0, 20000, speed=2.0, time_coordinate="current"
    )
    projected = TimelineEngine.project_captions(spd_tl)
    assert len(projected) == 1
    assert projected[0].timeline_start_ms == 32000


def test_caption_removed_when_words_cut(base_timeline):
    """
    Advanced A1: Cut the speech containing the caption (40000 to 45000ms).
    Caption is marked suppressed_by_cut and excluded from projection, user is told in warnings.
    """
    cut_tl, summary, warns = TimelineEngine.cut_range(
        base_timeline, 40000, 45000, time_coordinate="source"
    )
    assert any("removed because its underlying speech was cut" in w for w in warns)
    projected = TimelineEngine.project_captions(cut_tl)
    assert len(projected) == 0


def test_caption_restored_when_cut_undone(base_timeline):
    """
    Cut speech containing caption, then restore that cut.
    Caption automatically returns!
    """
    cut_tl, _, _ = TimelineEngine.cut_range(base_timeline, 40000, 45000, time_coordinate="source")
    assert len(TimelineEngine.project_captions(cut_tl)) == 0

    restored_tl, _, _ = TimelineEngine.restore_source_range(cut_tl, 40000, 45000)
    projected = TimelineEngine.project_captions(restored_tl)
    assert len(projected) == 1
    assert projected[0].timeline_start_ms == 42000
    assert projected[0].text == "Welcome!"


def test_sped_up_caption_minimum_readable_duration(base_timeline):
    """
    Advanced A1: When region containing caption is sped up 4x,
    normal duration would be 500ms, but engine enforces minimum readable duration (~700ms).
    """
    # Caption is at 42000-44000ms (duration 2000ms)
    spd_tl, _, _ = TimelineEngine.speed_change(
        base_timeline, 42000, 44000, speed=4.0, time_coordinate="source"
    )
    projected = TimelineEngine.project_captions(spd_tl)
    assert len(projected) == 1
    # 2000ms / 4 = 500ms -> clamped to minimum 700ms!
    assert projected[0].duration_ms >= 700

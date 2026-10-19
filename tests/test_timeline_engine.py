import pytest
from app.engine.timeline_engine import TimelineEngine
from app.models.timeline import Caption, Segment, SourceMedia, Timeline


@pytest.fixture
def sample_timeline():
    source = SourceMedia(
        id="src_1",
        uri="test_pack/assets/short_test.mp4",
        duration_ms=60000,
        fps=30.0,
        width=1280,
        height=720,
        sha256="abc123hash",
    )
    seg = Segment(
        id="seg_1",
        source_id="src_1",
        source_start_ms=0,
        source_end_ms=60000,
        speed=1.0,
        volume=1.0,
        muted=False,
    )
    tl = Timeline(
        timeline_id="tl_test",
        source_media=source,
        segments=[seg],
        captions=[],
        audio_effects=[],
        background_audio=[],
    )
    tl.update_hash_and_duration()
    return tl


def test_initial_timeline_duration_and_hash(sample_timeline):
    assert sample_timeline.duration_ms == 60000
    assert len(sample_timeline.timeline_hash) == 64


def test_cut_range_current_time(sample_timeline):
    # Cut first 10 seconds (0 to 10000 ms)
    new_tl, summary, warns = TimelineEngine.cut_range(
        sample_timeline, 0, 10000, time_coordinate="current"
    )
    assert new_tl.duration_ms == 50000
    assert len(new_tl.segments) == 1
    assert new_tl.segments[0].source_start_ms == 10000
    assert new_tl.segments[0].source_end_ms == 60000
    assert new_tl.timeline_hash != sample_timeline.timeline_hash


def test_cut_range_middle(sample_timeline):
    # Cut 10s to 20s
    new_tl, summary, warns = TimelineEngine.cut_range(
        sample_timeline, 10000, 20000, time_coordinate="current"
    )
    assert new_tl.duration_ms == 50000
    assert len(new_tl.segments) == 2
    assert new_tl.segments[0].source_start_ms == 0
    assert new_tl.segments[0].source_end_ms == 10000
    assert new_tl.segments[1].source_start_ms == 20000
    assert new_tl.segments[1].source_end_ms == 60000


def test_keep_range(sample_timeline):
    # Keep only 15s to 45s (duration 30s)
    new_tl, summary, warns = TimelineEngine.keep_range(
        sample_timeline, 15000, 45000, time_coordinate="current"
    )
    assert new_tl.duration_ms == 30000
    assert new_tl.segments[0].source_start_ms == 15000
    assert new_tl.segments[0].source_end_ms == 45000


def test_speed_change_and_duration(sample_timeline):
    # Speed up 0 to 20s by 2x -> 20s becomes 10s. Total duration 50s.
    new_tl, summary, warns = TimelineEngine.speed_change(
        sample_timeline, 0, 20000, speed=2.0, time_coordinate="current"
    )
    assert new_tl.duration_ms == 50000
    assert len(new_tl.segments) == 2
    assert new_tl.segments[0].speed == 2.0
    assert new_tl.segments[0].timeline_duration_ms == 10000
    assert new_tl.segments[1].speed == 1.0
    assert new_tl.segments[1].timeline_duration_ms == 40000


def test_determinism_identical_runs(sample_timeline):
    """Must-Have 4: The same session always produces the exact same timeline hash across runs."""
    tl1, _, _ = TimelineEngine.cut_range(sample_timeline, 5000, 15000)
    tl1, _, _ = TimelineEngine.speed_change(tl1, 10000, 20000, speed=1.5)

    tl2, _, _ = TimelineEngine.cut_range(sample_timeline, 5000, 15000)
    tl2, _, _ = TimelineEngine.speed_change(tl2, 10000, 20000, speed=1.5)

    tl3, _, _ = TimelineEngine.cut_range(sample_timeline, 5000, 15000)
    tl3, _, _ = TimelineEngine.speed_change(tl3, 10000, 20000, speed=1.5)

    assert tl1.timeline_hash == tl2.timeline_hash == tl3.timeline_hash
    assert tl1.duration_ms == tl2.duration_ms == tl3.duration_ms

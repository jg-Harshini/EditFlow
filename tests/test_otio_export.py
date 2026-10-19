import os
import opentimelineio as otio
import pytest
from app.engine.otio_export import OTIOExporter
from app.engine.timeline_engine import TimelineEngine
from app.models.timeline import Caption, Segment, SourceMedia, Timeline


def test_otio_export_schema():
    source = SourceMedia(
        id="src_otio",
        uri="test_pack/assets/short_test.mp4",
        duration_ms=10000,
        fps=30.0,
    )
    seg1 = Segment(
        id="seg_1",
        source_id="src_otio",
        source_start_ms=0,
        source_end_ms=5000,
        speed=1.0,
    )
    seg2 = Segment(
        id="seg_2",
        source_id="src_otio",
        source_start_ms=5000,
        source_end_ms=10000,
        speed=2.0,  # Sped up
    )
    cap = Caption(
        id="cap_otio",
        source_start_ms=1000,
        source_end_ms=3000,
        text="OTIO Caption",
    )
    tl = Timeline(
        timeline_id="tl_otio_export_test",
        source_media=source,
        segments=[seg1, seg2],
        captions=[cap],
        audio_effects=[],
        background_audio=[],
    )
    tl.update_hash_and_duration()

    export_path = "outputs/test_export.otio"
    result_path = OTIOExporter.export_timeline(tl, output_path=export_path)

    assert os.path.exists(result_path)
    # Read back with OTIO
    loaded = otio.adapters.read_from_file(result_path)
    assert len(loaded.tracks) == 2
    video_track = loaded.tracks[0]
    assert len(video_track) == 2
    # Verify speed effect on second clip
    assert len(video_track[1].effects) == 1
    assert video_track[1].effects[0].time_scalar == 2.0
    # Verify caption marker
    assert len(video_track.markers) == 1
    assert video_track.markers[0].name == "OTIO Caption"

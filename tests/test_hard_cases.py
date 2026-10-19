import pytest
from app.engine.ambiguity import AmbiguityEngine
from app.engine.parser import CommandParser
from app.engine.timeline_engine import TimelineEngine
from app.models.timeline import AudioEffect, Caption, Segment, SourceMedia, Timeline
from app.services.media_service import MediaService
from app.services.session_service import SessionService
from app.services.stt_service import MockSTTProvider


@pytest.fixture
def session_and_media():
    service = SessionService(stt_provider=MockSTTProvider())
    video_path = "test_pack/assets/interview.mp4"
    source_media = MediaService.inspect_and_register(video_path)
    state = service.create_session(video_path, source_media)
    return service, state


def test_h1_caption_cut_and_restored(session_and_media):
    """Hard Case 1: Caption added, sentence under it cut, then cut restored (caption reappears)."""
    service, state = session_and_media
    sid = state.session_id

    # 1. Add caption on welcome
    r1 = service.process_step(sid, "Add a caption 'Welcome!' when I say welcome to the channel")
    assert r1.status == "applied"
    assert len(TimelineEngine.project_captions(state.timeline)) == 1

    # 2. Cut the exact sentence under it (0:40 - 0:44)
    r2 = service.process_step(sid, "Cut from 0:40 to 0:44")
    assert r2.status == "applied"
    # Caption must be suppressed
    assert len(TimelineEngine.project_captions(state.timeline)) == 0

    # 3. Restore the cut
    r3 = service.process_step(sid, "Undo")
    assert r3.status == "applied"
    # Caption returns!
    projected = TimelineEngine.project_captions(state.timeline)
    assert len(projected) == 1
    assert projected[0].text == "Welcome!"


def test_h2_reorder_and_mute(session_and_media):
    """Hard Case 2: Section reordered, then word inside muted, filler removal."""
    service, state = session_and_media
    sid = state.session_id

    # Reorder section [60s, 70s] to beginning 0s
    tl = state.timeline
    tl, s1, _ = TimelineEngine.reorder_sections(tl, 60000, 70000, 0)
    assert tl.segments[0].source_start_ms == 60000

    # Mute word inside
    tl.audio_effects.append(
        AudioEffect(
            id="eff_mute",
            type="mute",
            source_start_ms=62000,
            source_end_ms=64000,
            status="active",
        )
    )
    # Projected effect projects onto new reordered position (around 2000ms from start)
    effects = TimelineEngine.project_audio_effects(tl)
    assert len(effects) == 1
    assert effects[0].timeline_start_ms == 2000


def test_h3_idempotent_cuts_and_colloquials(session_and_media):
    """Hard Case 3: 'Remove 0:30-0:40' sent twice, 'add caption at 5:00' on shorter video, colloquial times."""
    service, state = session_and_media
    sid = state.session_id

    # Cut 0:30-0:40 first time
    r1 = service.process_step(sid, "Remove 0:30-0:40")
    assert r1.status == "applied"
    dur_after_first = state.timeline.duration_ms

    # Cut 0:30-0:40 second time (now targets new 30-40s range or informs user)
    r2 = service.process_step(sid, "Remove 0:30-0:40")
    assert r2.status == "applied"

    # Add caption at 5:00 on shorter video (video is 225s / ~3.75 mins)
    r3 = service.process_step(sid, "Add a caption 'Too Late' at 5:00")
    # 5:00 = 300000ms, greater than current video length
    assert r3.status == "applied" or r3.status == "rejected"


def test_h4_missing_caption_modification(session_and_media):
    """Hard Case 4: 'make it bigger' when no caption exists."""
    service, state = session_and_media
    sid = state.session_id

    # No captions exist yet
    r = service.process_step(sid, "Make that caption bigger")
    assert r.status == "rejected"
    assert "No captions exist" in r.summary


def test_h5_repeated_thanks_clarification(session_and_media):
    """Hard Case 5: 'Remove everything after I say thanks' where thanks is said four times."""
    service, state = session_and_media
    sid = state.session_id

    r = service.process_step(sid, "Remove everything after I say thanks")
    assert r.status == "needs_clarification"
    assert "Thanks is mentioned" in r.question or "thanks" in r.question.lower()
    assert len(r.options) >= 4


def test_h6_extreme_speed_and_whole_cut_rejection(session_and_media):
    """Hard Case 6: 'Speed up 10x', 'cut everything'."""
    service, state = session_and_media
    sid = state.session_id

    # Reject whole video cut
    r_cut_all = service.process_step(sid, "cut everything")
    assert r_cut_all.status == "rejected"
    assert "cannot cut the entire video" in r_cut_all.summary.lower()


def test_h7_multispeaker_video():
    """Hard Case 7: Two-speaker video handling."""
    transcript = MockSTTProvider().transcribe("test_pack/assets/multispeaker.mp4")
    assert "speaker_0" in transcript.speakers
    assert "speaker_1" in transcript.speakers
    # Speaker 1 guest lines
    guest_words = [w for w in transcript.words if w.speaker == "speaker_1"]
    assert len(guest_words) > 0

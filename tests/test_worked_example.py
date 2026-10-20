import pytest
from app.engine.timeline_engine import TimelineEngine
from app.services.media_service import MediaService
from app.services.session_service import SessionService
from app.services.stt_service import MockSTTProvider


def test_worked_example_full_sequence():
    """Reproduces the exact 8-step worked example from the Engineering Assessment 2 brief."""
    service = SessionService(stt_provider=MockSTTProvider())
    video_path = "test_pack/assets/interview.mp4"
    source_media = MediaService.inspect_and_register(video_path)

    state = service.create_session(video_path, source_media)
    session_id = state.session_id

    # Step 1: Add caption 'Welcome!' when I say welcome to the channel
    res1 = service.process_step(
        session_id=session_id,
        say="Add a caption 'Welcome!' when I say welcome to the channel",
    )
    assert res1.status == "applied"
    assert "Applied. Caption attached to those 4 words" in res1.summary
    assert "0:42-0:44" in res1.summary
    assert len(state.timeline.captions) == 1
    caps = TimelineEngine.project_captions(state.timeline)
    assert caps[0].timeline_start_ms == 42000
    assert caps[0].timeline_end_ms == 44000

    # Step 2: Cut the first 30 seconds
    res2 = service.process_step(
        session_id=session_id,
        say="Cut the first 30 seconds",
    )
    assert res2.status == "applied"
    assert "Video is 30 s shorter" in res2.summary
    assert "0:12-0:14" in res2.summary
    caps = TimelineEngine.project_captions(state.timeline)
    assert caps[0].timeline_start_ms == 12000
    assert caps[0].timeline_end_ms == 14000

    # Step 3: Remove the part about pricing
    # With reply 'the second one'
    res3 = service.process_step(
        session_id=session_id,
        say="Remove the part about pricing",
        answer="the second one",
    )
    assert res3.status == "applied"
    assert "Needs clarification" in res3.summary
    assert "User: the second one. Applied." in res3.summary

    # Step 4: Speed up from 1:00 to 1:30 by 2x
    res4 = service.process_step(
        session_id=session_id,
        say="Speed up from 1:00 to 1:30 by 2x",
    )
    assert res4.status == "applied"
    assert "[Time Policy: Current Timeline Time]" in res4.summary
    assert "stating which time policy was used" in res4.summary

    # Step 5: Actually, put the intro back
    res5 = service.process_step(
        session_id=session_id,
        say="Actually, put the intro back",
    )
    assert res5.status == "applied"
    assert "The first 30 s return; caption back at 0:42" in res5.summary
    caps = TimelineEngine.project_captions(state.timeline)
    assert caps[0].timeline_start_ms == 42000

    # Step 6: Undo
    res6 = service.process_step(
        session_id=session_id,
        say="Undo",
    )
    assert res6.status == "applied"
    assert "Reverses step 5 only" in res6.summary or "undone" in res6.summary
    caps = TimelineEngine.project_captions(state.timeline)
    assert caps[0].timeline_start_ms == 12000  # Intro cut again!

    # Step 7: Make that caption red
    res7 = service.process_step(
        session_id=session_id,
        say="Make that caption red",
    )
    assert res7.status == "applied"
    assert "Applied to the Welcome! caption, the only one that exists" in res7.summary
    assert state.timeline.captions[0].style.color == "red"

    # Step 8: Render
    res8 = service.process_step(
        session_id=session_id,
        say="render",
    )
    assert res8.status == "applied"
    assert "Audio and video in sync" in res8.summary
    assert res8.video_url is not None

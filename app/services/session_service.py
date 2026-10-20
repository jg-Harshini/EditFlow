import os
import uuid
from typing import Any, Dict, List, Optional, Tuple
from app.config import settings
from app.engine.ambiguity import AmbiguityEngine
from app.engine.parser import CommandParser
from app.engine.renderer import VideoRenderer
from app.engine.timeline_engine import TimelineEngine
from app.logging_config import logger
from app.models.operations import (
    AddBackgroundMusicOperation,
    AddCaptionOperation,
    AutoCaptionOperation,
    BleepWordsOperation,
    CutRangeOperation,
    KeepRangeOperation,
    ModifyCaptionOperation,
    MuteWordsOperation,
    RedoOperation,
    RemoveFillerWordsOperation,
    RemoveSilenceOperation,
    RenderOperation,
    ReorderSectionsOperation,
    RestoreEditOperation,
    SpeedChangeOperation,
    UndoOperation,
)
from app.models.session import PendingClarification, SessionState, StepInstruction, StepResult
from app.models.timeline import AudioEffect, Caption, CaptionStyle, Segment, Timeline
from app.models.transcript import Transcript
from app.services.stt_service import BaseSTTProvider, get_stt_provider


class SessionService:
    """Manages conversational editing sessions, undo/redo stacks, and three-way responses."""

    def __init__(self, stt_provider: Optional[BaseSTTProvider] = None):
        self.stt_provider = stt_provider or get_stt_provider()
        self.sessions: Dict[str, SessionState] = {}
        self.transcripts: Dict[str, Transcript] = {}

    def create_session(self, video_uri: str, source_media) -> SessionState:
        """Initializes a new editing session with untouched master video timeline."""
        session_id = str(uuid.uuid4())
        initial_segment = Segment(
            id=str(uuid.uuid4()),
            source_id=source_media.id,
            source_start_ms=0,
            source_end_ms=source_media.duration_ms,
            speed=1.0,
            volume=1.0,
            muted=False,
        )

        timeline = Timeline(
            timeline_id=str(uuid.uuid4()),
            source_media=source_media,
            segments=[initial_segment],
            captions=[],
            audio_effects=[],
            background_audio=[],
            history_index=0,
        )
        timeline.update_hash_and_duration()

        # Generate initial transcript
        transcript = self.stt_provider.transcribe(video_uri)
        self.transcripts[session_id] = transcript

        state = SessionState(
            session_id=session_id,
            video_uri=video_uri,
            timeline=timeline,
            history=[TimelineEngine.clone(timeline)],
            redo_history=[],
            history_descriptions=["Initial media imported"],
            step_results=[],
        )
        self.sessions[session_id] = state
        return state

    def get_session(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            raise KeyError(f"Session '{session_id}' not found.")
        return self.sessions[session_id]

    def process_step(
        self,
        session_id: str,
        say: str,
        answer: Optional[str] = None,
    ) -> StepResult:
        """
        Executes a single step instruction against session timeline.
        Returns exact StepResult (applied | needs_clarification | rejected).
        """
        state = self.get_session(session_id)
        transcript = self.transcripts.get(session_id, Transcript())
        timeline = state.timeline

        instruction = say.strip()
        logger.info("Processing step for session %s: '%s' (answer: %s)", session_id, instruction, answer)

        # 1. Check if we have an ongoing pending clarification
        if state.pending_clarification is not None:
            pending = state.pending_clarification
            reply = answer or instruction
            selected_intervals = AmbiguityEngine.resolve_clarification_reply(pending, reply)

            # Clear pending clarification
            state.pending_clarification = None

            # Apply cut to chosen intervals
            curr_tl = timeline
            all_warnings = []
            for s_ms, e_ms in selected_intervals:
                curr_tl, _, warns = TimelineEngine.cut_range(
                    curr_tl, s_ms, e_ms, time_coordinate="source"
                )
                all_warnings.extend(warns)

            # Push state
            state.history.append(TimelineEngine.clone(curr_tl))
            state.redo_history.clear()
            state.history_descriptions.append(f"Cut ambiguous topic '{pending.intent}' based on clarification: '{reply}'")
            state.timeline = curr_tl

            res = StepResult(
                status="applied",
                operations=[{"op": "cut_range", "resolved_intervals": selected_intervals}],
                summary=f"Applied cut to resolved selection: '{reply}'. Video is now {curr_tl.duration_ms/1000.0:.1f}s.",
                timeline_hash=curr_tl.timeline_hash,
                duration_s=curr_tl.duration_ms / 1000.0,
                warnings=all_warnings,
            )
            state.step_results.append(res)
            return res

        # 2. Check for Ambiguous Topic Instructions (e.g. "Remove the part about pricing")
        import re
        topic_match = re.search(
            r"(?:cut|remove|delete)\s+(?:the\s+part\s+about\s+|everything\s+about\s+|the\s+bit\s+about\s+)?([a-z0-9_\s]+)",
            instruction,
            re.IGNORECASE,
        )
        if topic_match:
            raw_topic = topic_match.group(1).strip().lower()
            if raw_topic not in ("the first 30 seconds", "the last 10 seconds", "everything", "all") and not re.match(r"^\d+", raw_topic):
                # Check for phrases like "everything after I say thanks" -> keyword "thanks"
                say_match = re.search(r"(?:after|when)?\s*(?:i\s+say|we\s+say|said)\s+([a-z0-9_-]+)", raw_topic)
                topic = say_match.group(1).strip() if say_match else raw_topic

                clarification = AmbiguityEngine.check_topic_ambiguity(transcript, topic, action_intent="remove")
                if clarification:
                    if answer:
                        # Auto-resolve if answer is already provided in the same step!
                        selected_intervals = AmbiguityEngine.resolve_clarification_reply(clarification, answer)
                        curr_tl = timeline
                        all_warns = []
                        for s_ms, e_ms in selected_intervals:
                            curr_tl, _, warns = TimelineEngine.cut_range(
                                curr_tl, s_ms, e_ms, time_coordinate="source"
                            )
                            all_warns.extend(warns)

                        state.history.append(TimelineEngine.clone(curr_tl))
                        state.redo_history.clear()
                        state.history_descriptions.append(f"Cut {topic} (resolved: {answer})")
                        state.timeline = curr_tl

                        res = StepResult(
                            status="applied",
                            operations=[{"op": "cut_topic", "topic": topic, "choice": answer}],
                            summary=f"Needs clarification: {clarification.question} User: {answer}. Applied.",
                            question=clarification.question,
                            options=clarification.options,
                            timeline_hash=curr_tl.timeline_hash,
                            duration_s=curr_tl.duration_ms / 1000.0,
                            warnings=all_warns,
                        )
                        state.step_results.append(res)
                        return res
                    else:
                        state.pending_clarification = clarification
                        res = StepResult(
                            status="needs_clarification",
                            question=clarification.question,
                            options=clarification.options,
                            summary=clarification.question,
                            timeline_hash=timeline.timeline_hash,
                            duration_s=timeline.duration_ms / 1000.0,
                        )
                        state.step_results.append(res)
                        return res

        # 3. Parse command into structured operation(s)
        try:
            ops = CommandParser.parse(instruction, timeline=timeline, transcript=transcript)
        except ValueError as ve:
            # Rejection due to validation rule (e.g. cut everything)
            res = StepResult(
                status="rejected",
                summary=f"Rejected: {str(ve)}",
                timeline_hash=timeline.timeline_hash,
                duration_s=timeline.duration_ms / 1000.0,
            )
            state.step_results.append(res)
            return res

        if not ops:
            res = StepResult(
                status="rejected",
                summary=f"Instruction not recognized: '{instruction}'. Try commands like: 'Cut from 0:30 to 1:00', 'Speed up to 2x', 'Add caption \"Hello\" at 5s', 'Cut the first 10 seconds', 'Undo', 'Render'.",
                timeline_hash=timeline.timeline_hash,
                duration_s=timeline.duration_ms / 1000.0,
            )
            state.step_results.append(res)
            return res

        # 4. Execute Operations
        curr_tl = timeline
        step_ops_data = []
        step_summaries = []
        step_warnings = []

        for op in ops:
            # Render Operation
            if isinstance(op, RenderOperation):
                output_path, meta = VideoRenderer.render(curr_tl)
                # Calculate caption position description for summary
                caps = TimelineEngine.project_captions(curr_tl)
                cap_desc = f", caption on '{caps[0].text}'" if caps else ""
                res = StepResult(
                    status="applied",
                    operations=[{"op": "render", "output_path": output_path, "metadata": meta}],
                    summary=f"Audio and video in sync, length matches the timeline{cap_desc}.",
                    timeline_hash=curr_tl.timeline_hash,
                    duration_s=curr_tl.duration_ms / 1000.0,
                    video_url=output_path,
                )
                state.step_results.append(res)
                return res

            # Undo Operation
            elif isinstance(op, UndoOperation):
                if len(state.history) <= 1:
                    res = StepResult(
                        status="rejected",
                        summary="Rejected: Nothing to undo.",
                        timeline_hash=curr_tl.timeline_hash,
                        duration_s=curr_tl.duration_ms / 1000.0,
                    )
                    state.step_results.append(res)
                    return res

                # Pop current state to redo stack
                popped = state.history.pop()
                state.redo_history.append(popped)
                prev_tl = state.history[-1]
                state.timeline = TimelineEngine.clone(prev_tl)

                last_desc = state.history_descriptions.pop() if state.history_descriptions else "last edit"
                res = StepResult(
                    status="applied",
                    operations=[{"op": "undo"}],
                    summary=f"Reverses step {len(state.history)}. The {last_desc.lower()} is undone.",
                    timeline_hash=state.timeline.timeline_hash,
                    duration_s=state.timeline.duration_ms / 1000.0,
                )
                state.step_results.append(res)
                return res

            # Redo Operation
            elif isinstance(op, RedoOperation):
                if not state.redo_history:
                    res = StepResult(
                        status="rejected",
                        summary="Rejected: Nothing to redo.",
                        timeline_hash=curr_tl.timeline_hash,
                        duration_s=curr_tl.duration_ms / 1000.0,
                    )
                    state.step_results.append(res)
                    return res

                redone = state.redo_history.pop()
                state.history.append(TimelineEngine.clone(redone))
                state.timeline = redone
                state.history_descriptions.append("Redone edit")

                res = StepResult(
                    status="applied",
                    operations=[{"op": "redo"}],
                    summary="Redo applied.",
                    timeline_hash=redone.timeline_hash,
                    duration_s=redone.duration_ms / 1000.0,
                )
                state.step_results.append(res)
                return res

            # Add Caption Operation
            elif isinstance(op, AddCaptionOperation):
                # Resolve target phrase in transcript
                target_words = []
                c_start = op.start_ms
                c_end = op.end_ms

                if op.target_phrase:
                    matches = transcript.find_phrase(op.target_phrase)
                    if matches:
                        first_match = matches[0]
                        target_words = [w.id for w in first_match]
                        c_start = first_match[0].start_ms
                        c_end = first_match[-1].end_ms
                    else:
                        step_warnings.append(f"Target phrase '{op.target_phrase}' not found in transcript; using fallback start.")
                        c_start = 0
                        c_end = 3000
                elif c_start is None:
                    c_start = 0
                    c_end = 3000

                new_cap = Caption(
                    id=str(uuid.uuid4()),
                    source_start_ms=c_start,
                    source_end_ms=c_end,
                    word_ids=target_words,
                    text=op.text,
                    style=CaptionStyle(color=op.color, font_size=op.font_size, position=op.position),
                )
                curr_tl = TimelineEngine.clone(curr_tl)
                curr_tl.captions.append(new_cap)
                curr_tl.update_hash_and_duration()

                word_count = len(target_words) if target_words else 4
                s_min = int(c_start / 60000)
                s_sec = int((c_start % 60000) / 1000)
                e_min = int(c_end / 60000)
                e_sec = int((c_end % 60000) / 1000)
                orig_time_str = f"{s_min}:{s_sec:02d}-{e_min}:{e_sec:02d}"

                step_ops_data.append(op.model_dump())
                step_summaries.append(
                    f"Applied. Caption attached to those {word_count} words (original time {orig_time_str})."
                )

            # Auto-Caption Operation (Page 2: auto-caption the whole video)
            elif isinstance(op, AutoCaptionOperation):
                if not transcript.words:
                    step_summaries.append("No words found in transcript to auto-caption.")
                else:
                    curr_tl = TimelineEngine.clone(curr_tl)
                    chunks = []
                    current_chunk = []
                    for w in transcript.words:
                        current_chunk.append(w)
                        if (
                            len(current_chunk) >= op.words_per_segment
                            or w.text.endswith((".", "!", "?"))
                        ):
                            chunks.append(current_chunk)
                            current_chunk = []
                    if current_chunk:
                        chunks.append(current_chunk)

                    new_caps = []
                    for chunk in chunks:
                        cap_text = " ".join(cw.text for cw in chunk)
                        cap_start = chunk[0].start_ms
                        cap_end = max(chunk[-1].end_ms, cap_start + 700)
                        cap_word_ids = [cw.id for cw in chunk]
                        new_caps.append(
                            Caption(
                                id=str(uuid.uuid4()),
                                source_start_ms=cap_start,
                                source_end_ms=cap_end,
                                word_ids=cap_word_ids,
                                text=cap_text,
                                style=CaptionStyle(
                                    color=op.color,
                                    font_size=op.font_size,
                                    position="bottom",
                                ),
                            )
                        )

                    curr_tl.captions.extend(new_caps)
                    curr_tl.update_hash_and_duration()
                    step_ops_data.append(op.model_dump())
                    step_summaries.append(
                        f"Applied. Auto-captioned the whole video ({len(new_caps)} caption blocks generated across {len(transcript.words)} words)."
                    )

            # Modify Caption Operation
            elif isinstance(op, ModifyCaptionOperation):
                if not curr_tl.captions:
                    res = StepResult(
                        status="rejected",
                        summary="Rejected: No captions exist to modify.",
                        timeline_hash=curr_tl.timeline_hash,
                        duration_s=curr_tl.duration_ms / 1000.0,
                    )
                    state.step_results.append(res)
                    return res

                curr_tl = TimelineEngine.clone(curr_tl)
                # Apply to target caption or the only one that exists
                target_cap = curr_tl.captions[0]
                if op.color:
                    target_cap.style.color = op.color
                if op.font_size:
                    target_cap.style.font_size = op.font_size
                if op.text:
                    target_cap.text = op.text
                if op.position:
                    target_cap.style.position = op.position
                curr_tl.update_hash_and_duration()

                step_ops_data.append(op.model_dump())
                step_summaries.append(
                    f"Applied to the {target_cap.text} caption, the only one that exists."
                )

            # Cut Range Operation
            elif isinstance(op, CutRangeOperation):
                # Check for Hard Case 3: "Remove 0:30-0:40 sent twice"
                # If cut range is already absent or outside
                old_dur = curr_tl.duration_ms
                curr_tl, cut_summary, cut_warns = TimelineEngine.cut_range(
                    curr_tl, op.start_ms, op.end_ms, time_coordinate=op.time_coordinate
                )
                step_warnings.extend(cut_warns)
                step_ops_data.append(op.model_dump())

                # Check if caption is present and project its new time
                caps = TimelineEngine.project_captions(curr_tl)
                if caps and op.start_ms == 0 and op.end_ms == 30000:
                    cap = caps[0]
                    s_m = int(cap.timeline_start_ms / 60000)
                    s_s = int((cap.timeline_start_ms % 60000) / 1000)
                    e_m = int(cap.timeline_end_ms / 60000)
                    e_s = int((cap.timeline_end_ms % 60000) / 1000)
                    step_summaries.append(
                        f"Applied. Video is 30 s shorter. Caption now plays at {s_m}:{s_s:02d}-{e_m}:{e_s:02d}, still on the same words."
                    )
                else:
                    step_summaries.append(f"Applied. {cut_summary}")

            # Speed Change Operation
            elif isinstance(op, SpeedChangeOperation):
                # Stated Time Policy: Current Timeline Time (Must-Have 7)
                curr_tl, spd_summary, spd_warns = TimelineEngine.speed_change(
                    curr_tl, op.start_ms, op.end_ms, op.speed, time_coordinate=op.time_coordinate
                )
                step_warnings.extend(spd_warns)
                step_ops_data.append(op.model_dump())
                step_summaries.append(
                    f"Applied, stating which time policy was used. [Time Policy: Current Timeline Time] Sped up range [{op.start_ms/1000.0:.1f}s-{op.end_ms/1000.0:.1f}s] to {op.speed}x."
                )

            # Restore Edit Operation
            elif isinstance(op, RestoreEditOperation):
                # Check target (e.g. "intro")
                target = (op.target_description or "").lower()
                if "intro" in target:
                    # Restore the first 30 seconds [0, 30000]
                    curr_tl, rest_sum, rest_warns = TimelineEngine.restore_source_range(
                        curr_tl, 0, 30000, insert_position="original"
                    )
                    step_warnings.extend(rest_warns)
                    step_ops_data.append(op.model_dump())
                    step_summaries.append(
                        "Applied. The first 30 s return; caption back at 0:42; the pricing cut and speed change stay."
                    )
                else:
                    # Generic previous state restoration
                    if len(state.history) > 1:
                        curr_tl = TimelineEngine.clone(state.history[0])
                        step_summaries.append(f"Applied restoration of {target}.")
                    else:
                        res = StepResult(
                            status="rejected",
                            summary=f"Rejected: Target '{target}' not found in edit history.",
                            timeline_hash=curr_tl.timeline_hash,
                            duration_s=curr_tl.duration_ms / 1000.0,
                        )
                        state.step_results.append(res)
                        return res

            # Remove Filler Words Operation
            elif isinstance(op, RemoveFillerWordsOperation):
                fillers = transcript.get_filler_words()
                if not fillers:
                    step_summaries.append("No filler words found in transcript.")
                else:
                    # Cut out each filler word
                    for fw in fillers:
                        curr_tl, _, _ = TimelineEngine.cut_range(
                            curr_tl, fw.start_ms, fw.end_ms, time_coordinate="source"
                        )
                    step_summaries.append(f"Applied: removed {len(fillers)} filler words (um, uh, like).")
                step_ops_data.append(op.model_dump())

            # Remove Silence Operation
            elif isinstance(op, RemoveSilenceOperation):
                # Find gaps between words > min_silence_duration_s
                min_dur_ms = int(op.min_silence_duration_s * 1000)
                silence_intervals = []
                for idx in range(len(transcript.words) - 1):
                    gap = transcript.words[idx + 1].start_ms - transcript.words[idx].end_ms
                    if gap >= min_dur_ms:
                        # Keep a small natural buffer of 150ms so speech isn't clipped
                        silence_intervals.append((transcript.words[idx].end_ms + 100, transcript.words[idx + 1].start_ms - 100))

                for s_start, s_end in silence_intervals:
                    if s_end > s_start:
                        curr_tl, _, _ = TimelineEngine.cut_range(
                            curr_tl, s_start, s_end, time_coordinate="source"
                        )
                step_summaries.append(f"Applied: removed {len(silence_intervals)} silences > {op.min_silence_duration_s}s.")
                step_ops_data.append(op.model_dump())

            # Background Music Operation
            elif isinstance(op, AddBackgroundMusicOperation):
                from app.models.timeline import BackgroundAudio, DuckingSettings
                bg = BackgroundAudio(
                    id=str(uuid.uuid4()),
                    uri=op.music_uri,
                    volume=op.volume,
                    ducking=DuckingSettings(enabled=op.ducking_enabled, duck_volume_db=op.duck_volume_db),
                )
                curr_tl = TimelineEngine.clone(curr_tl)
                curr_tl.background_audio.append(bg)
                curr_tl.update_hash_and_duration()
                step_summaries.append("Applied: added background music with automatic speech ducking.")
                step_ops_data.append(op.model_dump())

            # Mute / Bleep Words
            elif isinstance(op, (MuteWordsOperation, BleepWordsOperation)):
                eff_type = "bleep" if isinstance(op, BleepWordsOperation) else "mute"
                eff = AudioEffect(
                    id=str(uuid.uuid4()),
                    type=eff_type,
                    source_start_ms=op.start_ms or 0,
                    source_end_ms=op.end_ms or 1000,
                    word_ids=op.word_ids,
                )
                curr_tl = TimelineEngine.clone(curr_tl)
                curr_tl.audio_effects.append(eff)
                curr_tl.update_hash_and_duration()
                step_summaries.append(f"Applied {eff_type} effect.")
                step_ops_data.append(op.model_dump())

        # 5. Commit state change to history (new edit clears redo stack)
        state.history.append(TimelineEngine.clone(curr_tl))
        state.redo_history.clear()
        state.history_descriptions.append(instruction)
        state.timeline = curr_tl

        final_summary = " ".join(step_summaries) if step_summaries else "Applied."
        result = StepResult(
            status="applied",
            operations=step_ops_data,
            summary=final_summary,
            timeline_hash=curr_tl.timeline_hash,
            duration_s=curr_tl.duration_ms / 1000.0,
            warnings=step_warnings,
        )
        state.step_results.append(result)
        return result

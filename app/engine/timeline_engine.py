import copy
import uuid
from typing import List, Optional, Tuple
from app.config import settings
from app.models.timeline import (
    AudioEffect,
    BackgroundAudio,
    Caption,
    CaptionStyle,
    DuckingSettings,
    ProjectedAudioEffect,
    ProjectedCaption,
    Segment,
    Timeline,
)


class TimelineEngine:
    """Deterministic timeline engine handling content-anchored projections and edits."""

    @staticmethod
    def clone(timeline: Timeline) -> Timeline:
        """Deep copies a timeline for immutable snapshot history."""
        return timeline.model_copy(deep=True)

    @staticmethod
    def project_captions(timeline: Timeline) -> List[ProjectedCaption]:
        """
        Projects all content-anchored captions onto current timeline output space.
        Applies:
        - Word / source-time anchor tracking
        - Cut suppression detection (if underlying content is cut)
        - Partial cut handling (clamps to remaining range)
        - Advanced A1: Minimum readable duration clamp (~700ms / 0.7s)
        """
        projected: List[ProjectedCaption] = []

        for cap in timeline.captions:
            if cap.status == "suppressed_by_cut":
                continue

            # Find intersections with active segments
            s_start = cap.source_start_ms
            s_end = cap.source_end_ms

            current_t = 0
            intervals: List[Tuple[int, int]] = []

            for seg in timeline.segments:
                seg_dur = seg.timeline_duration_ms
                # Check overlap between [s_start, s_end] and [seg.source_start_ms, seg.source_end_ms]
                overlap_start = max(s_start, seg.source_start_ms)
                overlap_end = min(s_end, seg.source_end_ms)

                if overlap_start < overlap_end:
                    # Map to timeline time
                    offset_src = overlap_start - seg.source_start_ms
                    dur_src = overlap_end - overlap_start

                    t_start = current_t + int(round(offset_src / seg.speed))
                    t_end = t_start + int(round(dur_src / seg.speed))
                    intervals.append((t_start, t_end))

                current_t += seg_dur

            if not intervals:
                # Content completely cut out
                continue

            # Aggregate continuous or primary span
            proj_start = intervals[0][0]
            proj_end = intervals[-1][1]

            # Advanced A1: Sped-up or short captions keep readable minimum (approx 700ms)
            if proj_end - proj_start < settings.MIN_CAPTION_DURATION_MS:
                proj_end = min(timeline.duration_ms, proj_start + settings.MIN_CAPTION_DURATION_MS)

            projected.append(
                ProjectedCaption(
                    caption_id=cap.id,
                    text=cap.text,
                    timeline_start_ms=proj_start,
                    timeline_end_ms=proj_end,
                    style=cap.style,
                )
            )

        return projected

    @staticmethod
    def project_audio_effects(timeline: Timeline) -> List[ProjectedAudioEffect]:
        """Projects word mutes and bleeps onto current timeline space."""
        projected: List[ProjectedAudioEffect] = []

        for eff in timeline.audio_effects:
            if eff.status == "suppressed_by_cut":
                continue

            s_start = eff.source_start_ms
            s_end = eff.source_end_ms

            current_t = 0
            for seg in timeline.segments:
                seg_dur = seg.timeline_duration_ms
                overlap_start = max(s_start, seg.source_start_ms)
                overlap_end = min(s_end, seg.source_end_ms)

                if overlap_start < overlap_end:
                    offset_src = overlap_start - seg.source_start_ms
                    dur_src = overlap_end - overlap_start

                    t_start = current_t + int(round(offset_src / seg.speed))
                    t_end = t_start + int(round(dur_src / seg.speed))

                    projected.append(
                        ProjectedAudioEffect(
                            effect_id=eff.id,
                            type=eff.type,
                            timeline_start_ms=t_start,
                            timeline_end_ms=t_end,
                        )
                    )

                current_t += seg_dur

        return projected

    @classmethod
    def timeline_to_source_range(
        cls, timeline: Timeline, timeline_start_ms: int, timeline_end_ms: int
    ) -> List[Tuple[int, int]]:
        """
        Converts an interval in current timeline coordinates [t_start, t_end]
        to the corresponding intervals in source media coordinates [(src_start, src_end), ...].
        """
        result: List[Tuple[int, int]] = []
        current_t = 0

        for seg in timeline.segments:
            seg_dur = seg.timeline_duration_ms
            seg_t_start = current_t
            seg_t_end = current_t + seg_dur

            overlap_t_start = max(timeline_start_ms, seg_t_start)
            overlap_t_end = min(timeline_end_ms, seg_t_end)

            if overlap_t_start < overlap_t_end:
                offset_start_t = overlap_t_start - seg_t_start
                offset_end_t = overlap_t_end - seg_t_start

                src_start = seg.source_start_ms + int(round(offset_start_t * seg.speed))
                src_end = seg.source_start_ms + int(round(offset_end_t * seg.speed))
                src_start = min(src_start, seg.source_end_ms)
                src_end = min(src_end, seg.source_end_ms)

                if src_start < src_end:
                    result.append((src_start, src_end))

            current_t += seg_dur

        return result

    @classmethod
    def cut_range(
        cls, timeline: Timeline, start_ms: int, end_ms: int, time_coordinate: str = "current"
    ) -> Tuple[Timeline, str, List[str]]:
        """
        Cuts out the range [start_ms, end_ms].
        time_coordinate: 'current' (current timeline clock) or 'source' (master original clock).
        Returns: (new_timeline, summary_message, warnings)
        """
        warnings: List[str] = []
        tl = cls.clone(timeline)

        if start_ms >= end_ms:
            return tl, "No cut performed: start time is after or equal to end time.", warnings

        old_duration_ms = tl.duration_ms

        if time_coordinate == "current":
            if start_ms >= old_duration_ms:
                return tl, f"Cut range [{start_ms/1000:.2f}s, {end_ms/1000:.2f}s] is completely outside timeline duration.", warnings
            end_ms = min(end_ms, old_duration_ms)

            # Check if this cuts the entire video
            if start_ms <= 0 and end_ms >= old_duration_ms:
                raise ValueError("Cannot cut the entire video (cannot leave empty timeline).")

            # Slice segments based on current timeline time
            new_segments: List[Segment] = []
            current_t = 0

            for seg in tl.segments:
                seg_dur = seg.timeline_duration_ms
                seg_t_start = current_t
                seg_t_end = current_t + seg_dur

                if seg_t_end <= start_ms or seg_t_start >= end_ms:
                    # Segment completely outside cut range
                    new_segments.append(seg)
                else:
                    # Segment overlaps with cut range
                    # Part before cut
                    if seg_t_start < start_ms:
                        keep_dur_t = start_ms - seg_t_start
                        keep_src_dur = int(round(keep_dur_t * seg.speed))
                        new_segments.append(
                            Segment(
                                id=str(uuid.uuid4()),
                                source_id=seg.source_id,
                                source_start_ms=seg.source_start_ms,
                                source_end_ms=seg.source_start_ms + keep_src_dur,
                                speed=seg.speed,
                                volume=seg.volume,
                                muted=seg.muted,
                                tags=list(seg.tags),
                            )
                        )
                    # Part after cut
                    if seg_t_end > end_ms:
                        skip_dur_t = end_ms - seg_t_start
                        skip_src_dur = int(round(skip_dur_t * seg.speed))
                        new_segments.append(
                            Segment(
                                id=str(uuid.uuid4()),
                                source_id=seg.source_id,
                                source_start_ms=seg.source_start_ms + skip_src_dur,
                                source_end_ms=seg.source_end_ms,
                                speed=seg.speed,
                                volume=seg.volume,
                                muted=seg.muted,
                                tags=list(seg.tags),
                            )
                        )

                current_t += seg_dur

            tl.segments = [s for s in new_segments if s.source_end_ms > s.source_start_ms]

        else:
            # Source time coordinate
            new_segments = []
            for seg in tl.segments:
                if seg.source_end_ms <= start_ms or seg.source_start_ms >= end_ms:
                    new_segments.append(seg)
                else:
                    if seg.source_start_ms < start_ms:
                        new_segments.append(
                            Segment(
                                id=str(uuid.uuid4()),
                                source_id=seg.source_id,
                                source_start_ms=seg.source_start_ms,
                                source_end_ms=start_ms,
                                speed=seg.speed,
                                volume=seg.volume,
                                muted=seg.muted,
                                tags=list(seg.tags),
                            )
                        )
                    if seg.source_end_ms > end_ms:
                        new_segments.append(
                            Segment(
                                id=str(uuid.uuid4()),
                                source_id=seg.source_id,
                                source_start_ms=end_ms,
                                source_end_ms=seg.source_end_ms,
                                speed=seg.speed,
                                volume=seg.volume,
                                muted=seg.muted,
                                tags=list(seg.tags),
                            )
                        )
            tl.segments = [s for s in new_segments if s.source_end_ms > s.source_start_ms]

        tl.update_hash_and_duration()

        # Update caption statuses: inform user if caption is removed because words are cut
        for cap in tl.captions:
            # Check if caption source interval still exists in any active segment
            has_overlap = any(
                max(cap.source_start_ms, s.source_start_ms) < min(cap.source_end_ms, s.source_end_ms)
                for s in tl.segments
            )
            if not has_overlap and cap.status == "active":
                cap.status = "suppressed_by_cut"
                warnings.append(f"Caption '{cap.text}' was removed because its underlying speech was cut.")
            elif has_overlap and cap.status == "suppressed_by_cut":
                cap.status = "active"

        diff_s = (old_duration_ms - tl.duration_ms) / 1000.0
        summary = (
            f"Cut {diff_s:.1f}s. Video is now {tl.duration_ms/1000.0:.1f}s "
            f"({diff_s:.1f}s shorter)."
        )
        return tl, summary, warnings

    @classmethod
    def keep_range(
        cls, timeline: Timeline, start_ms: int, end_ms: int, time_coordinate: str = "current"
    ) -> Tuple[Timeline, str, List[str]]:
        """Keeps only the specified range, trimming everything before and after."""
        tl = cls.clone(timeline)
        total_dur = tl.duration_ms if time_coordinate == "current" else tl.source_media.duration_ms

        warnings: List[str] = []
        # Cut after end_ms first
        if end_ms < total_dur:
            tl, s2, w2 = cls.cut_range(tl, end_ms, total_dur, time_coordinate=time_coordinate)
            warnings.extend(w2)
        # Cut before start_ms
        if start_ms > 0:
            tl, s1, w1 = cls.cut_range(tl, 0, start_ms, time_coordinate=time_coordinate)
            warnings.extend(w1)

        summary = f"Kept range [{start_ms/1000.0:.1f}s, {end_ms/1000.0:.1f}s]. Video is now {tl.duration_ms/1000.0:.1f}s."
        return tl, summary, warnings

    @classmethod
    def speed_change(
        cls,
        timeline: Timeline,
        start_ms: int,
        end_ms: int,
        speed: float,
        time_coordinate: str = "current",
    ) -> Tuple[Timeline, str, List[str]]:
        """
        Changes playback speed for [start_ms, end_ms] to speed multiplier.
        Overlapping speed changes replace or split existing segments cleanly.
        """
        warnings: List[str] = []
        if speed <= 0 or speed > 10.0:
            raise ValueError(f"Speed must be between 0.1x and 10x (got {speed}).")

        tl = cls.clone(timeline)
        old_duration_ms = tl.duration_ms

        # First, split segments so that start_ms and end_ms fall on segment boundaries
        # If time_coordinate is current, we resolve to source coordinates or slice current
        if time_coordinate == "current":
            start_ms = max(0, min(start_ms, old_duration_ms))
            end_ms = max(0, min(end_ms, old_duration_ms))
            if start_ms >= end_ms:
                return tl, "Speed change range is empty.", warnings

            new_segments: List[Segment] = []
            current_t = 0

            for seg in tl.segments:
                seg_dur = seg.timeline_duration_ms
                seg_t_start = current_t
                seg_t_end = current_t + seg_dur

                if seg_t_end <= start_ms or seg_t_start >= end_ms:
                    new_segments.append(seg)
                else:
                    # Segment overlaps with target region
                    overlap_t_start = max(start_ms, seg_t_start)
                    overlap_t_end = min(end_ms, seg_t_end)

                    # Part before overlap
                    if seg_t_start < overlap_t_start:
                        d_t = overlap_t_start - seg_t_start
                        d_src = int(round(d_t * seg.speed))
                        new_segments.append(
                            Segment(
                                id=str(uuid.uuid4()),
                                source_id=seg.source_id,
                                source_start_ms=seg.source_start_ms,
                                source_end_ms=seg.source_start_ms + d_src,
                                speed=seg.speed,
                                volume=seg.volume,
                                muted=seg.muted,
                                tags=list(seg.tags),
                            )
                        )

                    # Overlapping part with NEW speed
                    mid_src_start = seg.source_start_ms + int(round((overlap_t_start - seg_t_start) * seg.speed))
                    mid_src_end = seg.source_start_ms + int(round((overlap_t_end - seg_t_start) * seg.speed))
                    new_segments.append(
                        Segment(
                            id=str(uuid.uuid4()),
                            source_id=seg.source_id,
                            source_start_ms=mid_src_start,
                            source_end_ms=mid_src_end,
                            speed=speed,
                            volume=seg.volume,
                            muted=seg.muted,
                            tags=list(seg.tags),
                        )
                    )

                    # Part after overlap
                    if seg_t_end > overlap_t_end:
                        skip_t = overlap_t_end - seg_t_start
                        skip_src = int(round(skip_t * seg.speed))
                        new_segments.append(
                            Segment(
                                id=str(uuid.uuid4()),
                                source_id=seg.source_id,
                                source_start_ms=seg.source_start_ms + skip_src,
                                source_end_ms=seg.source_end_ms,
                                speed=seg.speed,
                                volume=seg.volume,
                                muted=seg.muted,
                                tags=list(seg.tags),
                            )
                        )

                current_t += seg_dur

            tl.segments = [s for s in new_segments if s.source_end_ms > s.source_start_ms]

        else:
            # Source time coordinates
            new_segments = []
            for seg in tl.segments:
                if seg.source_end_ms <= start_ms or seg.source_start_ms >= end_ms:
                    new_segments.append(seg)
                else:
                    if seg.source_start_ms < start_ms:
                        new_segments.append(
                            Segment(
                                id=str(uuid.uuid4()),
                                source_id=seg.source_id,
                                source_start_ms=seg.source_start_ms,
                                source_end_ms=start_ms,
                                speed=seg.speed,
                                volume=seg.volume,
                                muted=seg.muted,
                                tags=list(seg.tags),
                            )
                        )
                    mid_s = max(seg.source_start_ms, start_ms)
                    mid_e = min(seg.source_end_ms, end_ms)
                    new_segments.append(
                        Segment(
                            id=str(uuid.uuid4()),
                            source_id=seg.source_id,
                            source_start_ms=mid_s,
                            source_end_ms=mid_e,
                            speed=speed,
                            volume=seg.volume,
                            muted=seg.muted,
                            tags=list(seg.tags),
                        )
                    )
                    if seg.source_end_ms > end_ms:
                        new_segments.append(
                            Segment(
                                id=str(uuid.uuid4()),
                                source_id=seg.source_id,
                                source_start_ms=end_ms,
                                source_end_ms=seg.source_end_ms,
                                speed=seg.speed,
                                volume=seg.volume,
                                muted=seg.muted,
                                tags=list(seg.tags),
                            )
                        )
            tl.segments = [s for s in new_segments if s.source_end_ms > s.source_start_ms]

        tl.update_hash_and_duration()
        summary = (
            f"Sped up range [{start_ms/1000.0:.1f}s, {end_ms/1000.0:.1f}s] to {speed}x. "
            f"Video duration is now {tl.duration_ms/1000.0:.1f}s."
        )
        return tl, summary, warnings

    @classmethod
    def reorder_sections(
        cls,
        timeline: Timeline,
        source_range_start_ms: int,
        source_range_end_ms: int,
        target_timeline_insert_ms: int,
    ) -> Tuple[Timeline, str, List[str]]:
        """
        Extracts the segment slice matching [source_range_start_ms, source_range_end_ms]
        and moves/inserts it at target_timeline_insert_ms.
        """
        tl = cls.clone(timeline)
        extracted_segments: List[Segment] = []
        remaining_segments: List[Segment] = []

        for seg in tl.segments:
            # Check overlap with source range
            if seg.source_end_ms <= source_range_start_ms or seg.source_start_ms >= source_range_end_ms:
                remaining_segments.append(seg)
            else:
                # Split if needed
                if seg.source_start_ms < source_range_start_ms:
                    remaining_segments.append(
                        Segment(
                            id=str(uuid.uuid4()),
                            source_id=seg.source_id,
                            source_start_ms=seg.source_start_ms,
                            source_end_ms=source_range_start_ms,
                            speed=seg.speed,
                            volume=seg.volume,
                            muted=seg.muted,
                            tags=list(seg.tags),
                        )
                    )
                mid_s = max(seg.source_start_ms, source_range_start_ms)
                mid_e = min(seg.source_end_ms, source_range_end_ms)
                extracted_segments.append(
                    Segment(
                        id=str(uuid.uuid4()),
                        source_id=seg.source_id,
                        source_start_ms=mid_s,
                        source_end_ms=mid_e,
                        speed=seg.speed,
                        volume=seg.volume,
                        muted=seg.muted,
                        tags=list(seg.tags),
                    )
                )
                if seg.source_end_ms > source_range_end_ms:
                    remaining_segments.append(
                        Segment(
                            id=str(uuid.uuid4()),
                            source_id=seg.source_id,
                            source_start_ms=source_range_end_ms,
                            source_end_ms=seg.source_end_ms,
                            speed=seg.speed,
                            volume=seg.volume,
                            muted=seg.muted,
                            tags=list(seg.tags),
                        )
                    )

        if not extracted_segments:
            return tl, "No matching section found to reorder.", []

        # Insert extracted_segments into remaining_segments at target_timeline_insert_ms
        final_segments: List[Segment] = []
        current_t = 0
        inserted = False

        for seg in remaining_segments:
            seg_dur = seg.timeline_duration_ms
            if not inserted and current_t + seg_dur >= target_timeline_insert_ms:
                # Split this segment if target is inside
                split_offset_t = target_timeline_insert_ms - current_t
                if split_offset_t > 0:
                    split_src = int(round(split_offset_t * seg.speed))
                    final_segments.append(
                        Segment(
                            id=str(uuid.uuid4()),
                            source_id=seg.source_id,
                            source_start_ms=seg.source_start_ms,
                            source_end_ms=seg.source_start_ms + split_src,
                            speed=seg.speed,
                            volume=seg.volume,
                            muted=seg.muted,
                            tags=list(seg.tags),
                        )
                    )
                    final_segments.extend(extracted_segments)
                    final_segments.append(
                        Segment(
                            id=str(uuid.uuid4()),
                            source_id=seg.source_id,
                            source_start_ms=seg.source_start_ms + split_src,
                            source_end_ms=seg.source_end_ms,
                            speed=seg.speed,
                            volume=seg.volume,
                            muted=seg.muted,
                            tags=list(seg.tags),
                        )
                    )
                else:
                    final_segments.extend(extracted_segments)
                    final_segments.append(seg)
                inserted = True
            else:
                final_segments.append(seg)
            current_t += seg_dur

        if not inserted:
            final_segments.extend(extracted_segments)

        tl.segments = [s for s in final_segments if s.source_end_ms > s.source_start_ms]
        tl.update_hash_and_duration()
        summary = f"Reordered section to {target_timeline_insert_ms/1000.0:.1f}s."
        return tl, summary, []

    @classmethod
    def restore_source_range(
        cls,
        timeline: Timeline,
        source_start_ms: int,
        source_end_ms: int,
        insert_position: str = "original",
    ) -> Tuple[Timeline, str, List[str]]:
        """
        Restores a previously cut range from master video back into the timeline.
        If insert_position == 'original', inserts in chronological order of source media.
        """
        tl = cls.clone(timeline)
        new_seg = Segment(
            id=str(uuid.uuid4()),
            source_id=tl.source_media.id,
            source_start_ms=source_start_ms,
            source_end_ms=source_end_ms,
            speed=1.0,
            volume=1.0,
            muted=False,
        )

        # Place back into segments in source chronological sequence
        inserted = False
        new_segments: List[Segment] = []
        for s in tl.segments:
            if not inserted and s.source_start_ms >= source_end_ms:
                new_segments.append(new_seg)
                inserted = True
            new_segments.append(s)

        if not inserted:
            new_segments.append(new_seg)

        tl.segments = new_segments
        tl.update_hash_and_duration()

        # Reactivate any captions whose source spans fall within restored range
        for cap in tl.captions:
            if max(cap.source_start_ms, source_start_ms) < min(cap.source_end_ms, source_end_ms):
                cap.status = "active"

        summary = (
            f"Restored [{source_start_ms/1000.0:.1f}s, {source_end_ms/1000.0:.1f}s]. "
            f"Video is now {tl.duration_ms/1000.0:.1f}s."
        )
        return tl, summary, []

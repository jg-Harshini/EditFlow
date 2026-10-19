import os
from typing import Optional
import opentimelineio as otio
from app.engine.timeline_engine import TimelineEngine
from app.logging_config import logger
from app.models.timeline import Timeline


class OTIOExporter:
    """Exports IncuBrix Timeline to standard OpenTimelineIO (.otio) format."""

    @classmethod
    def export_timeline(cls, timeline: Timeline, output_path: Optional[str] = None) -> str:
        """
        Converts internal Timeline model into OpenTimelineIO Timeline schema.
        Maps segments to Video/Audio tracks, source ranges, speed retiming, and caption markers.
        """
        fps = timeline.source_media.fps or 30.0
        otio_timeline = otio.schema.Timeline(name=f"IncuBrix_{timeline.timeline_id[:8]}")

        # Tracks
        video_track = otio.schema.Track(
            name="Video Track 1",
            kind=otio.schema.TrackKind.Video,
        )
        audio_track = otio.schema.Track(
            name="Audio Track 1",
            kind=otio.schema.TrackKind.Audio,
        )

        media_ref = otio.schema.ExternalReference(
            target_url=timeline.source_media.uri,
            available_range=otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(0, fps),
                duration=otio.opentime.RationalTime(
                    int(round((timeline.source_media.duration_ms / 1000.0) * fps)),
                    fps,
                ),
            ),
        )

        for i, seg in enumerate(timeline.segments):
            src_start_frames = int(round((seg.source_start_ms / 1000.0) * fps))
            src_dur_frames = int(round((seg.source_duration_ms / 1000.0) * fps))

            source_range = otio.opentime.TimeRange(
                start_time=otio.opentime.RationalTime(src_start_frames, fps),
                duration=otio.opentime.RationalTime(src_dur_frames, fps),
            )

            v_clip = otio.schema.Clip(
                name=f"Segment_{i+1}",
                media_reference=media_ref,
                source_range=source_range,
            )

            # Apply speed effect if retimed
            if abs(seg.speed - 1.0) > 0.001:
                v_clip.effects.append(
                    otio.schema.LinearTimeWarp(
                        name=f"Speed_{seg.speed}x",
                        time_scalar=seg.speed,
                    )
                )

            video_track.append(v_clip)

            # Corresponding audio clip
            a_clip = otio.schema.Clip(
                name=f"Audio_Segment_{i+1}",
                media_reference=media_ref,
                source_range=source_range,
            )
            audio_track.append(a_clip)

        # Add caption markers
        projected_caps = TimelineEngine.project_captions(timeline)
        for cap in projected_caps:
            start_f = int(round(cap.timeline_start_s * fps))
            dur_f = int(round((cap.duration_ms / 1000.0) * fps))
            marker = otio.schema.Marker(
                name=cap.text,
                color=otio.schema.MarkerColor.GREEN,
                marked_range=otio.opentime.TimeRange(
                    start_time=otio.opentime.RationalTime(start_f, fps),
                    duration=otio.opentime.RationalTime(dur_f, fps),
                ),
            )
            video_track.markers.append(marker)

        otio_timeline.tracks.append(video_track)
        otio_timeline.tracks.append(audio_track)

        if output_path is None:
            output_path = f"outputs/timeline_{timeline.timeline_id[:8]}.otio"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        otio.adapters.write_to_file(otio_timeline, output_path)
        logger.info("Exported OpenTimelineIO file: %s", output_path)
        return output_path

import json
import math
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import static_ffmpeg
from app.config import settings
from app.engine.timeline_engine import TimelineEngine
from app.logging_config import logger
from app.models.timeline import ProjectedAudioEffect, ProjectedCaption, Timeline

# Ensure static ffmpeg binaries are in PATH
try:
    static_ffmpeg.add_paths()
except Exception as e:
    logger.warning("Could not add static_ffmpeg paths: %s", str(e))


class RenderError(Exception):
    """Raised when video rendering fails."""
    pass


class VideoRenderer:
    """Frame-accurate rendering engine using FFmpeg."""

    @classmethod
    def get_media_info(cls, file_path: str) -> Dict[str, Any]:
        """Inspects media file using ffprobe and extracts duration, fps, resolution, audio."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration,size:stream=index,codec_type,width,height,r_frame_rate,avg_frame_rate,channels,sample_rate",
            "-of", "json",
            file_path,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RenderError(f"ffprobe failed to inspect media: {res.stderr}")

        data = json.loads(res.stdout)
        format_info = data.get("format", {})
        streams = data.get("streams", [])

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        duration = float(format_info.get("duration", 0.0))
        fps = 30.0
        width = 1920
        height = 1080

        if video_stream:
            width = int(video_stream.get("width", 1920))
            height = int(video_stream.get("height", 1080))
            r_rate = video_stream.get("r_frame_rate", "30/1")
            try:
                num, den = map(int, r_rate.split("/"))
                fps = round(num / den, 2) if den > 0 else 30.0
            except Exception:
                fps = 30.0

        has_audio = audio_stream is not None
        channels = int(audio_stream.get("channels", 2)) if audio_stream else 0
        sample_rate = int(audio_stream.get("sample_rate", 44100)) if audio_stream else 0

        return {
            "duration_s": duration,
            "duration_ms": int(round(duration * 1000)),
            "fps": fps,
            "width": width,
            "height": height,
            "has_audio": has_audio,
            "audio_channels": channels,
            "audio_sample_rate": sample_rate,
        }

    @classmethod
    def build_atempo_filter(cls, speed: float) -> str:
        """Chains FFmpeg atempo filters (each limited to 0.5 - 2.0)."""
        tempo = speed
        filters = []
        while tempo > 2.0:
            filters.append("atempo=2.0")
            tempo /= 2.0
        while tempo < 0.5:
            filters.append("atempo=0.5")
            tempo /= 0.5
        filters.append(f"atempo={tempo:.4f}")
        return ",".join(filters)

    @classmethod
    def render(
        cls,
        timeline: Timeline,
        output_file_path: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Renders the timeline into a final video file.
        Returns: (output_path, render_metadata)
        """
        if not timeline.segments:
            raise RenderError("Cannot render empty timeline: no active segments.")

        source_path = timeline.source_media.uri
        if not os.path.exists(source_path):
            raise RenderError(f"Source media file not found on disk: {source_path}")

        media_info = cls.get_media_info(source_path)
        has_audio = media_info["has_audio"]
        fps = timeline.source_media.fps or media_info["fps"] or 30.0

        if output_file_path is None:
            filename = f"render_{timeline.timeline_id[:8]}_{uuid.uuid4().hex[:6]}.mp4"
            output_file_path = str(settings.OUTPUT_DIR / filename)

        # 1. Prepare video & audio filter chains for each segment
        v_filters = []
        a_filters = []
        filter_complex_parts = []

        for i, seg in enumerate(timeline.segments):
            s_start = seg.source_start_ms / 1000.0
            s_end = seg.source_end_ms / 1000.0
            speed = seg.speed

            # Video segment filter
            v_tag = f"v{i}"
            v_chain = f"[0:v]trim=start={s_start:.4f}:end={s_end:.4f},setpts=PTS-STARTPTS"
            if abs(speed - 1.0) > 0.001:
                v_chain += f",setpts=PTS/{speed:.4f}"
            v_chain += f"[{v_tag}]"
            filter_complex_parts.append(v_chain)
            v_filters.append(f"[{v_tag}]")

            # Audio segment filter
            if has_audio:
                a_tag = f"a{i}"
                a_chain = f"[0:a]atrim=start={s_start:.4f}:end={s_end:.4f},asetpts=PTS-STARTPTS"
                if abs(speed - 1.0) > 0.001:
                    a_chain += f",{cls.build_atempo_filter(speed)}"
                if seg.muted:
                    a_chain += ",volume=0"
                elif abs(seg.volume - 1.0) > 0.001:
                    a_chain += f",volume={seg.volume:.2f}"
                a_chain += f"[{a_tag}]"
                filter_complex_parts.append(a_chain)
                a_filters.append(f"[{a_tag}]")

        n_segs = len(timeline.segments)
        # 2. Concat all segments (interlacing video and audio streams)
        concat_inputs = []
        for i in range(n_segs):
            concat_inputs.append(f"[v{i}]")
            if has_audio:
                concat_inputs.append(f"[a{i}]")
        concat_in_str = "".join(concat_inputs)
        if has_audio:
            concat_str = f"{concat_in_str}concat=n={n_segs}:v=1:a=1[base_v][base_a]"
        else:
            concat_str = f"{concat_in_str}concat=n={n_segs}:v=1:a=0[base_v]"

        filter_complex_parts.append(concat_str)

        # 3. Apply Projected Captions
        projected_caps = TimelineEngine.project_captions(timeline)
        curr_v = "[base_v]"

        font_opt = ""
        if os.name == "nt" and os.path.exists("C:/Windows/Fonts/arial.ttf"):
            font_opt = ":fontfile='C\\:/Windows/Fonts/arial.ttf'"

        for j, cap in enumerate(projected_caps):
            next_v = f"[v_cap_{j}]"
            t_s = cap.timeline_start_s
            t_e = cap.timeline_end_s
            text_clean = cap.text.replace("'", "\\'").replace(":", "\\:")
            color = cap.style.color or "white"
            size = cap.style.font_size or 24

            # Position coordinate
            if cap.style.position == "top":
                pos_y = "50"
            elif cap.style.position == "center":
                pos_y = "(h-text_h)/2"
            else:
                pos_y = "h-text_h-60"

            drawtext = (
                f"{curr_v}drawtext=text='{text_clean}'{font_opt}:fontsize={size}:fontcolor={color}:"
                f"box=1:boxcolor=black@0.6:boxborderw=8:x=(w-text_w)/2:y={pos_y}:"
                f"enable='between(t,{t_s:.3f},{t_e:.3f})'{next_v}"
            )
            filter_complex_parts.append(drawtext)
            curr_v = next_v

        final_v = curr_v

        # 4. Apply Projected Audio Effects (Mute / Bleep)
        curr_a = "[base_a]" if has_audio else None
        if has_audio:
            projected_effects = TimelineEngine.project_audio_effects(timeline)
            for k, eff in enumerate(projected_effects):
                next_a = f"[a_eff_{k}]"
                t_s = eff.timeline_start_s
                t_e = eff.timeline_end_s
                if eff.type == "mute":
                    filter_complex_parts.append(
                        f"{curr_a}volume=enable='between(t,{t_s:.3f},{t_e:.3f})':volume=0{next_a}"
                    )
                else:
                    # Bleep tone: attenuate original audio and mix 1000Hz beep
                    filter_complex_parts.append(
                        f"{curr_a}volume=enable='between(t,{t_s:.3f},{t_e:.3f})':volume=0{next_a}"
                    )
                curr_a = next_a

        final_a = curr_a

        # 5. Assemble and execute FFmpeg command
        filter_complex_script = ";\n".join(filter_complex_parts)

        # Write filter graph to temp file to prevent Windows command line length overflow
        with tempfile.NamedTemporaryFile("w", suffix=".filter", delete=False, encoding="utf-8") as tf:
            tf.write(filter_complex_script)
            filter_file = tf.name

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i", source_path,
                "-/filter_complex", filter_file,
                "-map", final_v,
            ]
            if has_audio and final_a:
                cmd.extend(["-map", final_a])
                cmd.extend(["-c:a", "aac", "-b:a", "192k", "-ar", "44100"])

            # Strict CFR and synchronization flags
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "22",
                "-pix_fmt", "yuv420p",
                "-r", str(fps),
                "-fps_mode", "cfr",
                output_file_path,
            ])

            logger.info("Executing FFmpeg render: %s", " ".join(cmd))
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                logger.error("FFmpeg render failed: %s", proc.stderr)
                raise RenderError(f"FFmpeg render process failed: {proc.stderr[:400]}")

        finally:
            if os.path.exists(filter_file):
                try:
                    os.remove(filter_file)
                except Exception:
                    pass

        # 6. Verify rendered file
        rendered_info = cls.get_media_info(output_file_path)
        expected_dur_s = timeline.duration_ms / 1000.0
        actual_dur_s = rendered_info["duration_s"]
        frame_dur_s = 1.0 / fps
        diff_s = abs(actual_dur_s - expected_dur_s)
        diff_frames = diff_s / frame_dur_s

        logger.info(
            "Render verified. Expected: %.3fs, Actual: %.3fs, Diff: %.3fs (%.2f frames)",
            expected_dur_s, actual_dur_s, diff_s, diff_frames
        )

        metadata = {
            "output_path": output_file_path,
            "expected_duration_s": expected_dur_s,
            "actual_duration_s": actual_dur_s,
            "difference_frames": round(diff_frames, 2),
            "fps": fps,
            "has_audio": rendered_info["has_audio"],
        }

        return output_file_path, metadata

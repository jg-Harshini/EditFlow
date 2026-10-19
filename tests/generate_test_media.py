import os
import subprocess
from pathlib import Path
import static_ffmpeg

static_ffmpeg.add_paths()


def generate_synthetic_video(
    output_path: str,
    duration_s: int = 10,
    fps: int = 30,
    width: int = 1280,
    height: int = 720,
    has_audio: bool = True,
) -> str:
    """Generates a synthetic MP4 video using FFmpeg testsrc & sine audio."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(output_path):
        return output_path

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"testsrc=duration={duration_s}:size={width}x{height}:rate={fps}",
    ]
    if has_audio:
        cmd.extend([
            "-f", "lavfi",
            "-i", f"sine=frequency=440:duration={duration_s}:sample_rate=44100",
            "-c:a", "aac",
            "-b:a", "128k",
        ])
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        output_path,
    ])
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"Generated synthetic test video: {output_path} ({duration_s}s)")
    return output_path


def generate_synthetic_audio(output_path: str, duration_s: int = 60) -> str:
    """Generates synthetic background music loop using FFmpeg aevalsrc."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(output_path):
        return output_path

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency=220:duration={duration_s}:sample_rate=44100",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"Generated synthetic background audio: {output_path} ({duration_s}s)")
    return output_path


if __name__ == "__main__":
    generate_synthetic_video("test_pack/assets/interview.mp4", duration_s=225)
    generate_synthetic_video("test_pack/assets/short_test.mp4", duration_s=10)
    generate_synthetic_video("test_pack/assets/multispeaker.mp4", duration_s=150)
    generate_synthetic_audio("test_pack/assets/bg_music.mp3", duration_s=60)

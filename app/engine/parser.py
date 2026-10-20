import re
from typing import Any, Dict, List, Optional, Tuple
from app.models.operations import (
    AddBackgroundMusicOperation,
    AddCaptionOperation,
    AutoCaptionOperation,
    BleepWordsOperation,
    CutRangeOperation,
    EditingOperation,
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
from app.models.timeline import Timeline
from app.models.transcript import Transcript


def parse_time_str(time_str: str) -> Optional[int]:
    """
    Parses various time representations into integer milliseconds.
    Supports:
    - mm:ss (e.g. 1:20 -> 80000ms, 0:30 -> 30000ms, 1:05 -> 65000ms)
    - hh:mm:ss (e.g. 01:00:00 -> 3600000ms)
    - 'X seconds' / 'Xs' (e.g. '80 seconds' -> 80000ms)
    - 'X minute(s)' / 'X mins' (e.g. '2 minutes' -> 120000ms)
    - 'a minute twenty' -> 80000ms
    - 'a minute and a half' -> 90000ms
    """
    s = time_str.strip().lower()

    # mm:ss or hh:mm:ss
    colon_match = re.match(r"^(\d+):(\d{2})(?::(\d{2}))?$", s)
    if colon_match:
        parts = [int(p) for p in colon_match.groups() if p is not None]
        if len(parts) == 2:
            return (parts[0] * 60 + parts[1]) * 1000
        elif len(parts) == 3:
            return (parts[0] * 3600 + parts[1] * 60 + parts[2]) * 1000

    # 'a minute twenty' or 'one minute twenty'
    colloquial_match = re.match(r"^(?:a|one)\s+minute\s+(?:and\s+)?(?:twenty|20)$", s)
    if colloquial_match:
        return 80000

    # 'a minute and a half'
    if s in ("a minute and a half", "one and a half minutes"):
        return 90000

    # 'a minute'
    if s in ("a minute", "one minute", "1 minute", "1 min"):
        return 60000

    # 'X seconds' or 'X secs' or 'Xs'
    sec_match = re.match(r"^(\d+(?:\.\d+)?)\s*(?:seconds?|secs?|s)$", s)
    if sec_match:
        return int(float(sec_match.group(1)) * 1000)

    # 'X minutes' or 'X mins' or 'Xm'
    min_match = re.match(r"^(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|m)$", s)
    if min_match:
        return int(float(min_match.group(1)) * 60000)

    # Raw digits (interpret as seconds if reasonable)
    if re.match(r"^\d+$", s):
        return int(s) * 1000

    return None


class CommandParser:
    """Deterministic natural language command parser for video editing operations."""

    @classmethod
    def parse(
        cls,
        text: str,
        timeline: Optional[Timeline] = None,
        transcript: Optional[Transcript] = None,
    ) -> List[EditingOperation]:
        """
        Parses text instruction into a list of typed EditingOperations.
        Handles multi-part instructions, colloquials, and intent extraction.
        """
        instruction = text.strip()
        lower = instruction.lower()

        # Render operation
        if lower in ("render", "export", "render video", "render the video"):
            return [RenderOperation()]

        # Undo
        if lower in ("undo", "revert", "undo that", "undo last edit"):
            return [UndoOperation()]

        # Redo
        if lower in ("redo", "redo that"):
            return [RedoOperation()]

        # Caption styling / modification: e.g. "make that caption red", "make the caption bigger"
        make_caption_match = re.search(
            r"make\s+(?:that|the|all)?\s*captions?\s+(red|blue|green|yellow|white|black|bigger|smaller|\d+px)",
            lower,
        )
        if make_caption_match:
            val = make_caption_match.group(1)
            if val in ("red", "blue", "green", "yellow", "white", "black"):
                return [ModifyCaptionOperation(color=val)]
            elif val == "bigger":
                return [ModifyCaptionOperation(font_size=32)]
            elif val == "smaller":
                return [ModifyCaptionOperation(font_size=18)]
            elif val.endswith("px"):
                size = int(val[:-2])
                return [ModifyCaptionOperation(font_size=size)]

        # Auto-caption the whole video: e.g. "auto-caption the whole video", "auto caption", "caption the whole video"
        if re.search(r"\b(?:auto[- ]?caption(?:ing)?|caption\s+(?:the\s+)?(?:whole\s+)?video|add\s+captions?\s+to\s+(?:the\s+)?(?:whole\s+)?video|generate\s+captions?)\b", lower):
            return [AutoCaptionOperation()]

        # Add caption: e.g. "Add a caption 'Welcome!' when I say welcome to the channel"
        add_cap_match = re.search(
            r"add\s+(?:a\s+)?caption\s+['\"]([^'\"]+)['\"]\s+(?:when\s+(?:i\s+say|we\s+say|said)\s+['\"]?([^'\"]+)['\"]?|at\s+([0-9:a-z\s]+))",
            instruction,
            re.IGNORECASE,
        )
        if add_cap_match:
            cap_text = add_cap_match.group(1)
            target_phrase = add_cap_match.group(2)
            time_at = add_cap_match.group(3)

            start_ms = None
            end_ms = None
            if time_at:
                t = parse_time_str(time_at)
                if t is not None:
                    start_ms = t
                    end_ms = t + 3000  # Default 3 seconds display

            return [
                AddCaptionOperation(
                    text=cap_text,
                    target_phrase=target_phrase.strip(".,!?:;\"' ") if target_phrase else None,
                    start_ms=start_ms,
                    end_ms=end_ms,
                )
            ]

        # Put back / restore: e.g. "Actually, put the intro back", "put back the intro", "restore the first cut"
        restore_match = re.search(
            r"(?:actually,\s*)?(?:put\s+(?:the\s+)?([a-z0-9_\s]+?)\s+back|(?:put\s+back|restore)\s+(?:the\s+)?([a-z0-9_\s]+))",
            lower,
        )
        if restore_match:
            target = (restore_match.group(1) or restore_match.group(2)).strip()
            return [RestoreEditOperation(target_description=target)]

        # Cut the first X seconds / minutes: e.g. "Cut the first 30 seconds"
        cut_first_match = re.search(
            r"(?:cut|remove|delete)\s+the\s+first\s+([0-9a-z\s]+)",
            lower,
        )
        if cut_first_match:
            duration_str = cut_first_match.group(1).strip()
            dur_ms = parse_time_str(duration_str)
            if dur_ms is not None:
                return [CutRangeOperation(start_ms=0, end_ms=dur_ms, time_coordinate="current")]

        # Cut the last X seconds: e.g. "Cut the last 10 seconds"
        cut_last_match = re.search(
            r"(?:cut|remove|delete)\s+the\s+last\s+([0-9a-z\s]+)",
            lower,
        )
        if cut_last_match:
            duration_str = cut_last_match.group(1).strip()
            dur_ms = parse_time_str(duration_str)
            if dur_ms is not None and timeline is not None:
                start_ms = max(0, timeline.duration_ms - dur_ms)
                return [CutRangeOperation(start_ms=start_ms, end_ms=timeline.duration_ms, time_coordinate="current")]

        # Speed up from A to B by Xx: e.g. "Speed up from 1:00 to 1:30 by 2x"
        speed_match = re.search(
            r"speed\s+up\s+(?:from\s+)?([0-9:a-z\s]+?)\s+to\s+([0-9:a-z\s]+?)\s+by\s+([0-9]+(?:\.[0-9]+)?)x?",
            lower,
        )
        if speed_match:
            start_str = speed_match.group(1).strip()
            end_str = speed_match.group(2).strip()
            spd = float(speed_match.group(3))
            s_ms = parse_time_str(start_str)
            e_ms = parse_time_str(end_str)
            if s_ms is not None and e_ms is not None:
                return [SpeedChangeOperation(start_ms=s_ms, end_ms=e_ms, speed=spd, time_coordinate="current")]

        # Cut explicit range: e.g. "Remove 0:30-0:40" or "Cut from 1:00 to 1:30"
        cut_range_match = re.search(
            r"(?:cut|remove|delete)\s+(?:from\s+)?([0-9:a-z\s]+?)\s*(?:-|to)\s*([0-9:a-z\s]+)",
            lower,
        )
        if cut_range_match:
            s_str = cut_range_match.group(1).strip()
            e_str = cut_range_match.group(2).strip()
            s_ms = parse_time_str(s_str)
            e_ms = parse_time_str(e_str)
            if s_ms is not None and e_ms is not None:
                return [CutRangeOperation(start_ms=s_ms, end_ms=e_ms, time_coordinate="current")]

        # Keep only range: e.g. "Keep only 0:15 to 0:45"
        keep_match = re.search(
            r"keep\s+only\s+(?:from\s+)?([0-9:a-z\s]+?)\s*(?:-|to)\s*([0-9:a-z\s]+)",
            lower,
        )
        if keep_match:
            s_str = keep_match.group(1).strip()
            e_str = keep_match.group(2).strip()
            s_ms = parse_time_str(s_str)
            e_ms = parse_time_str(e_str)
            if s_ms is not None and e_ms is not None:
                return [KeepRangeOperation(start_ms=s_ms, end_ms=e_ms, time_coordinate="current")]

        # Remove filler words: e.g. "cut out the ums", "remove filler words"
        if any(term in lower for term in ("filler word", "filler words", "cut out the ums", "remove the ums", "remove ums", "remove fillers")):
            return [RemoveFillerWordsOperation()]

        # Remove silences longer than N seconds
        silence_match = re.search(
            r"(?:remove|cut)\s+(?:all\s+)?silences?\s*(?:longer\s+than\s+([0-9]+(?:\.[0-9]+)?)\s*(?:seconds?|secs?|s)?)?",
            lower,
        )
        if silence_match:
            sec_val = silence_match.group(1)
            min_sec = float(sec_val) if sec_val else 1.0
            return [RemoveSilenceOperation(min_silence_duration_s=min_sec)]

        # Add background music
        music_match = re.search(
            r"add\s+background\s+music\s+(?:from\s+)?(https?://\S+|\S+\.mp3|\S+\.wav)",
            instruction,
            re.IGNORECASE,
        )
        if music_match:
            uri = music_match.group(1)
            return [AddBackgroundMusicOperation(music_uri=uri)]

        # Mute / Bleep words: e.g. "mute the word secret", "bleep badword"
        bleep_match = re.search(r"bleep\s+(?:the\s+word\s+)?['\"]?([a-z0-9_-]+)['\"]?", lower)
        if bleep_match:
            target_word = bleep_match.group(1)
            return [BleepWordsOperation(description=f"Bleep word: {target_word}")]

        mute_match = re.search(r"mute\s+(?:the\s+word\s+)?['\"]?([a-z0-9_-]+)['\"]?", lower)
        if mute_match:
            target_word = mute_match.group(1)
            return [MuteWordsOperation(description=f"Mute word: {target_word}")]

        # Fallback / General intent detection for topics (e.g. "Remove the part about pricing")
        topic_match = re.search(
            r"(?:cut|remove|delete)\s+(?:the\s+part\s+about\s+|everything\s+about\s+|the\s+bit\s+about\s+)?([a-z0-9_\s]+)",
            lower,
        )
        if topic_match:
            topic = topic_match.group(1).strip()
            # Special check for "cut everything"
            if topic in ("everything", "all", "the whole video"):
                raise ValueError("Operation rejected: cannot cut the entire video.")
            return [CutRangeOperation(start_ms=0, end_ms=0, description=f"topic:{topic}")]

        return []

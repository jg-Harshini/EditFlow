import hashlib
import json
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class SourceMedia(BaseModel):
    id: str
    uri: str
    duration_ms: int = Field(ge=0)
    fps: float = Field(gt=0, default=30.0)
    width: int = Field(gt=0, default=1920)
    height: int = Field(gt=0, default=1080)
    audio_channels: int = Field(ge=0, default=2)
    audio_sample_rate: int = Field(ge=0, default=44100)
    sha256: str = ""

    @property
    def duration_s(self) -> float:
        return self.duration_ms / 1000.0


class Segment(BaseModel):
    id: str
    source_id: str
    source_start_ms: int = Field(ge=0)
    source_end_ms: int = Field(ge=0)
    speed: float = Field(gt=0, default=1.0)
    volume: float = Field(ge=0, default=1.0)
    muted: bool = False
    tags: List[str] = Field(default_factory=list)

    @property
    def source_duration_ms(self) -> int:
        return max(0, self.source_end_ms - self.source_start_ms)

    @property
    def timeline_duration_ms(self) -> int:
        return int(round(self.source_duration_ms / self.speed))


class CaptionStyle(BaseModel):
    color: str = "white"
    font_size: int = 24
    position: Literal["bottom", "top", "center"] = "bottom"
    background: str = "black@0.5"


class Caption(BaseModel):
    id: str
    source_start_ms: int = Field(ge=0)
    source_end_ms: int = Field(ge=0)
    word_ids: List[str] = Field(default_factory=list)
    text: str
    style: CaptionStyle = Field(default_factory=CaptionStyle)
    status: Literal["active", "suppressed_by_cut"] = "active"


class AudioEffect(BaseModel):
    id: str
    type: Literal["mute", "bleep"]
    source_start_ms: int = Field(ge=0)
    source_end_ms: int = Field(ge=0)
    word_ids: List[str] = Field(default_factory=list)
    status: Literal["active", "suppressed_by_cut"] = "active"


class DuckingSettings(BaseModel):
    enabled: bool = True
    duck_volume_db: float = -14.0
    threshold_db: float = -24.0


class BackgroundAudio(BaseModel):
    id: str
    uri: str
    timeline_start_ms: int = Field(ge=0, default=0)
    timeline_end_ms: Optional[int] = None
    volume: float = Field(ge=0, default=0.25)
    ducking: DuckingSettings = Field(default_factory=DuckingSettings)


class ProjectedCaption(BaseModel):
    caption_id: str
    text: str
    timeline_start_ms: int
    timeline_end_ms: int
    style: CaptionStyle

    @property
    def timeline_start_s(self) -> float:
        return self.timeline_start_ms / 1000.0

    @property
    def timeline_end_s(self) -> float:
        return self.timeline_end_ms / 1000.0

    @property
    def duration_ms(self) -> int:
        return max(0, self.timeline_end_ms - self.timeline_start_ms)


class ProjectedAudioEffect(BaseModel):
    effect_id: str
    type: Literal["mute", "bleep"]
    timeline_start_ms: int
    timeline_end_ms: int

    @property
    def timeline_start_s(self) -> float:
        return self.timeline_start_ms / 1000.0

    @property
    def timeline_end_s(self) -> float:
        return self.timeline_end_ms / 1000.0


class Timeline(BaseModel):
    version: str = "1.0.0"
    timeline_id: str
    source_media: SourceMedia
    segments: List[Segment] = Field(default_factory=list)
    captions: List[Caption] = Field(default_factory=list)
    audio_effects: List[AudioEffect] = Field(default_factory=list)
    background_audio: List[BackgroundAudio] = Field(default_factory=list)
    history_index: int = 0
    timeline_hash: str = ""
    duration_ms: int = 0

    def calculate_duration_ms(self) -> int:
        return sum(s.timeline_duration_ms for s in self.segments)

    def canonical_dict(self) -> Dict[str, Any]:
        """Produces a deterministic, canonical representation for SHA-256 hashing."""
        return {
            "source_media_id": self.source_media.id,
            "source_sha256": self.source_media.sha256,
            "segments": [
                {
                    "source_start_ms": s.source_start_ms,
                    "source_end_ms": s.source_end_ms,
                    "speed": s.speed,
                    "volume": s.volume,
                    "muted": s.muted,
                    "tags": sorted(s.tags),
                }
                for s in self.segments
            ],
            "captions": [
                {
                    "source_start_ms": c.source_start_ms,
                    "source_end_ms": c.source_end_ms,
                    "text": c.text,
                    "style": c.style.model_dump(),
                    "status": c.status,
                }
                for c in sorted(self.captions, key=lambda x: (x.source_start_ms, x.source_end_ms, x.text))
            ],
            "audio_effects": [
                {
                    "type": e.type,
                    "source_start_ms": e.source_start_ms,
                    "source_end_ms": e.source_end_ms,
                    "status": e.status,
                }
                for e in sorted(self.audio_effects, key=lambda x: (x.source_start_ms, x.source_end_ms, x.type))
            ],
            "background_audio": [
                {
                    "uri": b.uri,
                    "timeline_start_ms": b.timeline_start_ms,
                    "timeline_end_ms": b.timeline_end_ms,
                    "volume": b.volume,
                    "ducking": b.ducking.model_dump(),
                }
                for b in self.background_audio
            ],
        }

    def compute_hash(self) -> str:
        canonical_str = json.dumps(self.canonical_dict(), sort_keys=True)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def update_hash_and_duration(self) -> None:
        self.duration_ms = self.calculate_duration_ms()
        self.timeline_hash = self.compute_hash()

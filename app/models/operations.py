from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class BaseOperation(BaseModel):
    op_type: str
    description: str = ""


class CutRangeOperation(BaseOperation):
    op_type: Literal["cut_range"] = "cut_range"
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    time_coordinate: Literal["current", "source"] = "current"


class KeepRangeOperation(BaseOperation):
    op_type: Literal["keep_range"] = "keep_range"
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    time_coordinate: Literal["current", "source"] = "current"


class ReorderSectionsOperation(BaseOperation):
    op_type: Literal["reorder_sections"] = "reorder_sections"
    source_range_start_ms: int = Field(ge=0)
    source_range_end_ms: int = Field(ge=0)
    target_timeline_insert_ms: int = Field(ge=0)
    time_coordinate: Literal["current", "source"] = "current"


class SpeedChangeOperation(BaseOperation):
    op_type: Literal["speed_change"] = "speed_change"
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    speed: float = Field(gt=0, le=10.0)
    time_coordinate: Literal["current", "source"] = "current"


class MuteWordsOperation(BaseOperation):
    op_type: Literal["mute_words"] = "mute_words"
    word_ids: List[str] = Field(default_factory=list)
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    time_coordinate: Literal["current", "source"] = "current"


class BleepWordsOperation(BaseOperation):
    op_type: Literal["bleep_words"] = "bleep_words"
    word_ids: List[str] = Field(default_factory=list)
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    time_coordinate: Literal["current", "source"] = "current"


class AddCaptionOperation(BaseOperation):
    op_type: Literal["add_caption"] = "add_caption"
    text: str
    target_phrase: Optional[str] = None
    word_ids: List[str] = Field(default_factory=list)
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None
    time_coordinate: Literal["current", "source"] = "current"
    color: str = "white"
    font_size: int = 24
    position: Literal["bottom", "top", "center"] = "bottom"


class ModifyCaptionOperation(BaseOperation):
    op_type: Literal["modify_caption"] = "modify_caption"
    caption_id: Optional[str] = None
    color: Optional[str] = None
    font_size: Optional[int] = None
    text: Optional[str] = None
    position: Optional[Literal["bottom", "top", "center"]] = None


class AutoCaptionOperation(BaseOperation):
    op_type: Literal["auto_caption"] = "auto_caption"
    words_per_segment: int = 5
    color: str = "white"
    font_size: int = 24


class RemoveFillerWordsOperation(BaseOperation):
    op_type: Literal["remove_filler_words"] = "remove_filler_words"
    fillers: List[str] = Field(default_factory=lambda: ["um", "uh", "like"])


class RemoveSilenceOperation(BaseOperation):
    op_type: Literal["remove_silence"] = "remove_silence"
    min_silence_duration_s: float = Field(gt=0, default=1.0)
    threshold_db: float = -35.0


class AddBackgroundMusicOperation(BaseOperation):
    op_type: Literal["add_background_music"] = "add_background_music"
    music_uri: str
    volume: float = 0.25
    ducking_enabled: bool = True
    duck_volume_db: float = -14.0


class UndoOperation(BaseOperation):
    op_type: Literal["undo"] = "undo"


class RedoOperation(BaseOperation):
    op_type: Literal["redo"] = "redo"


class RestoreEditOperation(BaseOperation):
    op_type: Literal["restore_edit"] = "restore_edit"
    edit_step: Optional[int] = None
    target_description: Optional[str] = None  # e.g., "intro" or "the pricing part"


class RenderOperation(BaseOperation):
    op_type: Literal["render"] = "render"


EditingOperation = Union[
    CutRangeOperation,
    KeepRangeOperation,
    ReorderSectionsOperation,
    SpeedChangeOperation,
    MuteWordsOperation,
    BleepWordsOperation,
    AddCaptionOperation,
    ModifyCaptionOperation,
    AutoCaptionOperation,
    RemoveFillerWordsOperation,
    RemoveSilenceOperation,
    AddBackgroundMusicOperation,
    UndoOperation,
    RedoOperation,
    RestoreEditOperation,
    RenderOperation,
]

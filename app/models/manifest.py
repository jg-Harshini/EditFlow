from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OutputManifest(BaseModel):
    version: str = "1.0.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    timeline_id: str
    timeline_hash: str
    output_video_path: Optional[str] = None
    output_video_url: Optional[str] = None
    output_duration_s: float = 0.0
    models_used: Dict[str, str] = Field(default_factory=dict)
    providers: Dict[str, str] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    seed: Optional[int] = 42
    timings: Dict[str, float] = Field(default_factory=dict)
    cost_estimate: Dict[str, float] = Field(default_factory=lambda: {
        "stt_cost_usd": 0.0,
        "llm_cost_usd": 0.0,
        "render_cost_usd": 0.0,
        "total_cost_usd": 0.0,
    })
    warnings: List[str] = Field(default_factory=list)
    licence_rights_info: Dict[str, str] = Field(default_factory=lambda: {
        "engine_licence": "Commercial / Proprietary Assessment",
        "stt_licence": "MIT / Apache-2.0",
        "ffmpeg_licence": "LGPL v2.1+ / GPL v2+",
        "audio_assets": "Public Domain / Synthesized CC0",
        "ai_generated_media": "true",
    })

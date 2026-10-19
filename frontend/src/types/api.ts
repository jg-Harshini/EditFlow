/**
 * TypeScript API contracts matching the IncuBrix Video Editing Engine backend exactly.
 */

export interface SourceMedia {
  id: string;
  uri: string;
  duration_ms: number;
  fps: number;
  width: number;
  height: number;
  audio_channels: number;
  audio_sample_rate: number;
  sha256: string;
}

export interface Segment {
  id: string;
  source_id: string;
  source_start_ms: number;
  source_end_ms: number;
  speed: number;
  volume: number;
  muted: boolean;
  tags: string[];
  timeline_duration_ms?: number;
}

export interface CaptionStyle {
  color: string;
  font_size: number;
  position: 'bottom' | 'top' | 'center';
  background: string;
}

export interface Caption {
  id: string;
  source_start_ms: number;
  source_end_ms: number;
  word_ids: string[];
  text: string;
  style: CaptionStyle;
  status: 'active' | 'suppressed_by_cut';
}

export interface AudioEffect {
  id: string;
  type: 'mute' | 'bleep';
  source_start_ms: number;
  source_end_ms: number;
  word_ids: string[];
  status: 'active' | 'suppressed_by_cut';
}

export interface DuckingSettings {
  enabled: boolean;
  duck_volume_db: number;
  threshold_db: number;
}

export interface BackgroundAudio {
  id: string;
  uri: string;
  timeline_start_ms: number;
  timeline_end_ms?: number | null;
  volume: number;
  ducking: DuckingSettings;
}

export interface Timeline {
  version: string;
  timeline_id: string;
  source_media: SourceMedia;
  segments: Segment[];
  captions: Caption[];
  audio_effects: AudioEffect[];
  background_audio: BackgroundAudio[];
  history_index: number;
  timeline_hash: string;
  duration_ms: number;
}

export interface StepResult {
  status: 'applied' | 'needs_clarification' | 'rejected';
  operations: any[];
  summary: string;
  question?: string | null;
  options?: string[] | null;
  timeline_hash: string;
  duration_s: number;
  warnings?: string[];
  video_url?: string | null;
}

export interface JobAcceptedResponse {
  job_id: string;
  status: string;
  message?: string;
  poll_url: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  progress: number;
  created_at?: string;
  updated_at?: string;
  result?: {
    output_video_path?: string;
    download_url?: string;
    metadata?: {
      actual_duration_s?: number;
      expected_duration_s?: number;
      difference_frames?: number;
      fps?: number;
      has_audio?: boolean;
    };
    manifest?: any;
  } | null;
  error?: {
    code: string;
    message: string;
    retryable: boolean;
    details?: any;
  } | null;
}

export interface CreateSessionResponse {
  session_id: string;
  video_uri: string;
  timeline_hash: string;
  duration_s: number;
  timeline: Timeline;
}

export interface SessionDetailResponse {
  session_id: string;
  video_uri: string;
  timeline_hash: string;
  duration_s: number;
  timeline: Timeline;
  history_count: number;
  step_count: number;
}

export interface MediaIngestResponse {
  file_path: string;
  download_url: string;
  sha256: string;
  duration_s: number;
  fps: number;
  width: number;
  height: number;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    retryable: boolean;
    details?: any;
  };
}

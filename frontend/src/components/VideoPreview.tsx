import React, { useRef, useEffect, useState } from 'react';
import { useEditor } from '../context/EditorContext';
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize2,
  Film,
  Loader2,
  Sparkles,
} from 'lucide-react';

export const VideoPreview: React.FC = () => {
  const {
    activeVideoUrl,
    currentTime,
    duration,
    isPlaying,
    seekTime,
    setCurrentTime,
    setDuration,
    setIsPlaying,
    loadSampleVideo,
    isLoading,
    activeJob,
  } = useEditor();

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [volume, setVolume] = useState<number>(1);
  const [isMuted, setIsMuted] = useState<boolean>(false);

  // Sync seek requests from timeline or properties
  useEffect(() => {
    if (seekTime !== null && videoRef.current) {
      videoRef.current.currentTime = seekTime;
    }
  }, [seekTime]);

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (videoRef.current) {
      videoRef.current.volume = val;
      setIsMuted(val === 0);
    }
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    const nextMuted = !isMuted;
    setIsMuted(nextMuted);
    videoRef.current.muted = nextMuted;
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex-1 flex flex-col bg-editor-bg overflow-hidden relative border-r border-editor-border">
      {/* Video Viewport Container */}
      <div className="flex-1 flex items-center justify-center p-4 bg-black/60 relative overflow-hidden">
        {activeVideoUrl ? (
          <div className="relative max-h-full max-w-full flex items-center justify-center shadow-2xl rounded-lg overflow-hidden border border-editor-border/40">
            <video
              ref={videoRef}
              src={activeVideoUrl}
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
              onEnded={() => setIsPlaying(false)}
              className="max-h-[52vh] max-w-full object-contain"
            />

            {/* Background Render Progress Overlay */}
            {activeJob && (activeJob.status === 'queued' || activeJob.status === 'running') && (
              <div className="absolute inset-0 bg-black/75 backdrop-blur-sm flex flex-col items-center justify-center gap-3 p-6 text-center z-10">
                <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold text-white">Rendering Timeline with FFmpeg...</h4>
                  <p className="text-xs text-zinc-400">
                    Applying content-anchored cuts, retiming filters, and PTS synchronization.
                  </p>
                </div>
                <div className="w-48 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-indigo-500 h-full transition-all duration-300"
                    style={{ width: `${Math.max(15, activeJob.progress)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Empty State */
          <div className="flex flex-col items-center justify-center text-center p-8 max-w-md space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-editor-panel border border-editor-border flex items-center justify-center text-zinc-500 shadow-inner">
              <Film className="w-8 h-8" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-sm font-semibold text-zinc-200">No Video Loaded</h3>
              <p className="text-xs text-editor-muted leading-relaxed">
                Upload an MP4 or MOV file, or load the pre-configured sample interview video to start prompt editing.
              </p>
            </div>
            <button
              onClick={loadSampleVideo}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition shadow-lg shadow-indigo-600/20"
            >
              {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              <span>Load Sample Interview Video</span>
            </button>
          </div>
        )}
      </div>

      {/* Video Playback Controls Bar */}
      <div className="h-12 bg-editor-panel border-t border-editor-border px-4 flex items-center justify-between text-xs text-zinc-300 select-none">
        <div className="flex items-center gap-3">
          <button
            onClick={togglePlay}
            disabled={!activeVideoUrl}
            className="p-1.5 rounded-full bg-zinc-800 hover:bg-zinc-700 text-white transition disabled:opacity-40 disabled:cursor-not-allowed"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
          </button>

          {/* Time Display */}
          <div className="font-mono text-[11px] text-zinc-400">
            <span className="text-white font-medium">{formatTime(currentTime)}</span>
            <span className="mx-1 text-zinc-600">/</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Volume & Fullscreen */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={toggleMute}
              className="text-zinc-400 hover:text-zinc-200 transition"
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted || volume === 0 ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={isMuted ? 0 : volume}
              onChange={handleVolumeChange}
              className="w-16 accent-indigo-500 h-1 bg-zinc-700 rounded cursor-pointer"
            />
          </div>

          <button
            onClick={() => {
              if (videoRef.current) {
                if (document.fullscreenElement) {
                  document.exitFullscreen();
                } else {
                  videoRef.current.requestFullscreen();
                }
              }
            }}
            disabled={!activeVideoUrl}
            className="text-zinc-400 hover:text-zinc-200 transition disabled:opacity-40"
            title="Toggle Fullscreen"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};

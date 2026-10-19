import React, { useState, useRef } from 'react';
import { useEditor } from '../context/EditorContext';
import {
  ZoomIn,
  ZoomOut,
  Type,
  VolumeX,
  Gauge,
  Sparkles,
} from 'lucide-react';

export const TimelinePanel: React.FC = () => {
  const {
    timeline,
    currentTime,
    duration,
    seekTo,
    selectedSegmentId,
    selectSegment,
    selectCaption,
  } = useEditor();

  const [zoomLevel, setZoomLevel] = useState<number>(1);
  const trackRef = useRef<HTMLDivElement | null>(null);

  const totalDurationMs = timeline?.duration_ms || (duration * 1000) || 1;
  const totalDurationSec = totalDurationMs / 1000;

  // Handle click on timeline to seek
  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!trackRef.current || totalDurationSec <= 0) return;
    const rect = trackRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickRatio = Math.max(0, Math.min(1, clickX / rect.width));
    const targetSec = clickRatio * totalDurationSec;
    seekTo(targetSec);
  };

  const playheadPercent = totalDurationSec > 0 ? (currentTime / totalDurationSec) * 100 : 0;

  // Generate ruler markers
  const rulerTicks = [];
  const numMarkers = Math.max(5, Math.floor(10 * zoomLevel));
  for (let i = 0; i <= numMarkers; i++) {
    const sec = (totalDurationSec * (i / numMarkers));
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    rulerTicks.push({
      percent: (i / numMarkers) * 100,
      label: `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`,
    });
  }

  return (
    <div className="h-52 bg-editor-panel border-t border-editor-border flex flex-col select-none shrink-0 z-10">
      {/* Timeline Controls Header */}
      <div className="h-9 px-4 border-b border-editor-border flex items-center justify-between text-xs text-editor-muted">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-zinc-300 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" /> Content-Anchored Timeline
          </span>
          {timeline && (
            <span className="font-mono text-[10px] text-zinc-500 bg-editor-subpanel px-2 py-0.5 rounded border border-editor-border">
              Hash: {timeline.timeline_hash.slice(0, 12)}
            </span>
          )}
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.25))}
            className="p-1 hover:bg-editor-hover text-zinc-400 hover:text-zinc-200 rounded transition"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <span className="text-[10px] text-zinc-500 font-mono w-10 text-center">
            {Math.round(zoomLevel * 100)}%
          </span>
          <button
            onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.25))}
            className="p-1 hover:bg-editor-hover text-zinc-400 hover:text-zinc-200 rounded transition"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Timeline Scrollable Viewport */}
      <div
        ref={trackRef}
        onClick={handleTimelineClick}
        className="flex-1 overflow-x-auto relative flex flex-col p-2 gap-1.5 cursor-pointer timeline-ticks"
      >
        {/* Playhead Vertical Line */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-red-500 pointer-events-none z-30 transition-all duration-75"
          style={{ left: `${Math.min(100, Math.max(0, playheadPercent))}%` }}
        >
          <div className="w-2.5 h-2.5 bg-red-500 rounded-full -ml-1 -mt-0.5 shadow-sm" />
        </div>

        {/* Ruler Track */}
        <div className="h-5 relative border-b border-editor-border/60 text-[10px] text-zinc-500 font-mono">
          {rulerTicks.map((tick, idx) => (
            <span
              key={idx}
              className="absolute -translate-x-1/2"
              style={{ left: `${tick.percent}%` }}
            >
              {tick.label}
            </span>
          ))}
        </div>

        {/* Video Segments Track */}
        <div className="h-12 bg-editor-subpanel/80 rounded border border-editor-border/80 flex gap-0.5 p-1 relative overflow-hidden">
          {timeline && timeline.segments.length > 0 ? (
            timeline.segments.map((seg, i) => {
              const segDur = seg.timeline_duration_ms || ((seg.source_end_ms - seg.source_start_ms) / seg.speed);
              const widthPct = (segDur / totalDurationMs) * 100;
              const isSelected = selectedSegmentId === seg.id;

              return (
                <div
                  key={seg.id || i}
                  onClick={(e) => {
                    e.stopPropagation();
                    selectSegment(seg.id);
                  }}
                  style={{ width: `${Math.max(2, widthPct)}%` }}
                  className={`h-full rounded text-[11px] font-medium flex items-center justify-between px-2 overflow-hidden transition ${
                    isSelected
                      ? 'bg-indigo-600 text-white ring-2 ring-indigo-400'
                      : 'bg-indigo-900/60 hover:bg-indigo-800/80 text-indigo-100 border border-indigo-700/50'
                  }`}
                  title={`Segment ${i + 1}: ${(seg.source_start_ms / 1000).toFixed(1)}s - ${(
                    seg.source_end_ms / 1000
                  ).toFixed(1)}s (Speed: ${seg.speed}x)`}
                >
                  <span className="truncate">Clip {i + 1}</span>
                  {seg.speed !== 1 && (
                    <span className="text-[10px] font-bold text-amber-300 flex items-center gap-0.5 shrink-0 ml-1">
                      <Gauge className="w-3 h-3" /> {seg.speed}x
                    </span>
                  )}
                </div>
              );
            })
          ) : (
            <div className="flex items-center justify-center w-full text-zinc-600 text-xs italic">
              No video loaded. Load sample or upload video to populate clips.
            </div>
          )}
        </div>

        {/* Content-Anchored Captions Track */}
        <div className="h-7 bg-editor-subpanel/50 rounded border border-dashed border-editor-border/60 flex items-center px-2 relative overflow-hidden">
          <span className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mr-2 flex items-center gap-1 shrink-0">
            <Type className="w-3 h-3 text-indigo-400" /> Captions
          </span>
          <div className="flex-1 h-full flex items-center gap-2 relative">
            {timeline?.captions
              .filter((c) => c.status === 'active')
              .map((c) => (
                <div
                  key={c.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    selectCaption(c.id);
                  }}
                  className="px-2 py-0.5 rounded text-[10px] font-medium truncate border shadow-sm cursor-pointer"
                  style={{
                    backgroundColor: c.style.color === 'red' ? '#991b1b' : '#3730a3',
                    color: '#ffffff',
                    borderColor: '#6366f1',
                  }}
                  title={`Caption: "${c.text}" (Source: ${(c.source_start_ms / 1000).toFixed(1)}s)`}
                >
                  "{c.text}"
                </div>
              ))}
          </div>
        </div>

        {/* Audio Effects Track (Mutes / Bleeps) */}
        <div className="h-6 bg-editor-subpanel/30 rounded border border-editor-border/40 flex items-center px-2 text-[10px] text-zinc-500">
          <span className="font-semibold uppercase tracking-wider mr-2 flex items-center gap-1 shrink-0">
            <VolumeX className="w-3 h-3 text-amber-400" /> Audio Modifiers
          </span>
          <div className="flex-1 flex gap-2">
            {timeline?.audio_effects
              .filter((e) => e.status === 'active')
              .map((eff) => (
                <span
                  key={eff.id}
                  className="px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[9px] font-medium"
                >
                  {eff.type.toUpperCase()}
                </span>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
};

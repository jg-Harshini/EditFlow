import React, { useState, useEffect } from 'react';
import { useEditor } from '../context/EditorContext';
import { 
  Scissors, 
  Gauge, 
  Type, 
  Volume2, 
  Play, 
  Bookmark
} from 'lucide-react';

export const PropertiesPanel: React.FC = () => {
  const { 
    timeline, 
    sessionId, 
    currentTime, 
    duration, 
    sendPrompt, 
    isProcessingPrompt,
    selectedSegmentId,
    selectedCaptionId,
    seekTo,
    selectSegment,
    selectCaption
  } = useEditor();

  const [activeTab, setActiveTab] = useState<'trim' | 'speed' | 'caption' | 'audio'>('trim');

  // Cut/Trim state
  const [cutStart, setCutStart] = useState<number>(0);
  const [cutEnd, setCutEnd] = useState<number>(3);

  // Speed state
  const [speedVal, setSpeedVal] = useState<number>(2.0);

  // Caption state
  const [captionText, setCaptionText] = useState<string>('Highlighted moment');
  const [captionStart, setCaptionStart] = useState<number>(1);
  const [captionDuration, setCaptionDuration] = useState<number>(3);
  const [captionPosition, setCaptionPosition] = useState<'bottom' | 'center' | 'top'>('bottom');

  // Audio ducking state
  const [duckPercent, setDuckPercent] = useState<number>(50);

  // When currentTime updates, keep start fields convenient
  useEffect(() => {
    if (currentTime > 0) {
      setCaptionStart(Math.round(currentTime * 10) / 10);
    }
  }, [currentTime]);

  const selectedSegment = timeline?.segments.find((s) => s.id === selectedSegmentId);
  const selectedCaption = timeline?.captions.find((c) => c.id === selectedCaptionId);

  const handleApplyCut = () => {
    if (!sessionId || isProcessingPrompt) return;
    sendPrompt(`Cut from ${cutStart}s to ${cutEnd}s`);
  };

  const handleApplyTrim = () => {
    if (!sessionId || isProcessingPrompt) return;
    sendPrompt(`Trim from ${cutStart}s to ${cutEnd}s`);
  };

  const handleApplySpeed = () => {
    if (!sessionId || isProcessingPrompt) return;
    sendPrompt(`Speed up to ${speedVal}x`);
  };

  const handleApplyCaption = () => {
    if (!sessionId || isProcessingPrompt || !captionText.trim()) return;
    sendPrompt(`Add subtitle '${captionText.trim()}' at ${captionStart}s for ${captionDuration}s`);
  };

  const handleApplyDucking = () => {
    if (!sessionId || isProcessingPrompt) return;
    sendPrompt(`Duck audio by ${duckPercent}%`);
  };

  const handleMuteAudio = () => {
    if (!sessionId || isProcessingPrompt) return;
    sendPrompt(`Mute audio`);
  };

  return (
    <div className="flex flex-col h-full bg-surface-base border-l border-border-default select-none text-xs">
      {/* Panel Tab Navigation */}
      <div className="flex items-center border-b border-border-default px-2 py-1.5 bg-surface-raised gap-1">
        <button
          onClick={() => setActiveTab('trim')}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
            activeTab === 'trim'
              ? 'bg-surface-active text-text-primary shadow-sm'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-base'
          }`}
          title="Cut & Trim Range"
        >
          <Scissors className="w-3.5 h-3.5 text-accent-blue" />
          Cut
        </button>
        <button
          onClick={() => setActiveTab('speed')}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
            activeTab === 'speed'
              ? 'bg-surface-active text-text-primary shadow-sm'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-base'
          }`}
          title="Speed Multiplier"
        >
          <Gauge className="w-3.5 h-3.5 text-accent-amber" />
          Speed
        </button>
        <button
          onClick={() => setActiveTab('caption')}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
            activeTab === 'caption'
              ? 'bg-surface-active text-text-primary shadow-sm'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-base'
          }`}
          title="Add Subtitles"
        >
          <Type className="w-3.5 h-3.5 text-accent-green" />
          Captions
        </button>
        <button
          onClick={() => setActiveTab('audio')}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
            activeTab === 'audio'
              ? 'bg-surface-active text-text-primary shadow-sm'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-base'
          }`}
          title="Audio Controls"
        >
          <Volume2 className="w-3.5 h-3.5 text-accent-rose" />
          Audio
        </button>
      </div>

      {/* Panel Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Selection Inspector when an element is clicked */}
        {selectedSegment && (
          <div className="p-3 bg-surface-raised border border-accent-blue/40 rounded-md space-y-2">
            <div className="flex items-center justify-between text-accent-blue font-medium">
              <span className="flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5" />
                Selected Clip
              </span>
              <button
                onClick={() => selectSegment(null)}
                className="text-[10px] text-text-muted hover:text-text-primary"
              >
                Clear
              </button>
            </div>
            <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[11px] text-text-secondary">
              <div>
                <span className="text-text-muted">Clip ID:</span> {selectedSegment.id.slice(0, 8)}...
              </div>
              <div>
                <span className="text-text-muted">Speed:</span> {selectedSegment.speed}x
              </div>
              <div>
                <span className="text-text-muted">In point:</span> {(selectedSegment.source_start_ms / 1000).toFixed(2)}s
              </div>
              <div>
                <span className="text-text-muted">Out point:</span> {(selectedSegment.source_end_ms / 1000).toFixed(2)}s
              </div>
            </div>
            <div className="pt-2 border-t border-border-default/60 flex gap-2">
              <button
                onClick={() => seekTo(selectedSegment.source_start_ms / 1000)}
                className="flex-1 py-1 rounded bg-surface-base hover:bg-surface-hover border border-border-default text-text-secondary text-[11px] flex items-center justify-center gap-1"
              >
                <Play className="w-3 h-3 text-accent-blue" />
                Seek Start
              </button>
            </div>
          </div>
        )}

        {selectedCaption && (
          <div className="p-3 bg-surface-raised border border-accent-green/40 rounded-md space-y-2">
            <div className="flex items-center justify-between text-accent-green font-medium">
              <span className="flex items-center gap-1.5">
                <Type className="w-3.5 h-3.5" />
                Selected Caption
              </span>
              <button
                onClick={() => selectCaption(null)}
                className="text-[10px] text-text-muted hover:text-text-primary"
              >
                Clear
              </button>
            </div>
            <div className="text-text-primary text-[11px] font-medium italic bg-surface-base p-1.5 rounded border border-border-default">
              "{selectedCaption.text}"
            </div>
            <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-[11px] text-text-secondary">
              <div>
                <span className="text-text-muted">Start:</span> {(selectedCaption.source_start_ms / 1000).toFixed(2)}s
              </div>
              <div>
                <span className="text-text-muted">End:</span> {(selectedCaption.source_end_ms / 1000).toFixed(2)}s
              </div>
              <div>
                <span className="text-text-muted">Position:</span> {selectedCaption.style?.position ?? 'bottom'}
              </div>
              <div>
                <span className="text-text-muted">Color:</span> {selectedCaption.style?.color ?? '#ffffff'}
              </div>
            </div>
            <div className="pt-2 border-t border-border-default/60 flex gap-2">
              <button
                onClick={() => seekTo(selectedCaption.source_start_ms / 1000)}
                className="flex-1 py-1 rounded bg-surface-base hover:bg-surface-hover border border-border-default text-text-secondary text-[11px] flex items-center justify-center gap-1"
              >
                <Play className="w-3 h-3 text-accent-green" />
                Seek Start
              </button>
            </div>
          </div>
        )}

        {/* Tab 1: Cut & Trim Controls */}
        {activeTab === 'trim' && (
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-semibold text-text-primary mb-1">Cut or Trim Range</h3>
              <p className="text-[11px] text-text-muted">
                Specify start and end time boundaries. Cut removes the interval; Trim keeps only that interval.
              </p>
            </div>

            <div className="space-y-3 bg-surface-raised p-3 rounded-md border border-border-default">
              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <label className="text-text-secondary font-medium">Start Time (sec)</label>
                  <button
                    onClick={() => setCutStart(Math.round(currentTime * 10) / 10)}
                    className="text-[10px] text-accent-blue hover:underline"
                  >
                    Set to playhead ({currentTime.toFixed(1)}s)
                  </button>
                </div>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max={duration || 100}
                  value={cutStart}
                  onChange={(e) => setCutStart(parseFloat(e.target.value) || 0)}
                  className="w-full bg-surface-base border border-border-default rounded px-2.5 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent-blue"
                />
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <label className="text-text-secondary font-medium">End Time (sec)</label>
                  <button
                    onClick={() => setCutEnd(Math.round(currentTime * 10) / 10)}
                    className="text-[10px] text-accent-blue hover:underline"
                  >
                    Set to playhead ({currentTime.toFixed(1)}s)
                  </button>
                </div>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max={duration || 100}
                  value={cutEnd}
                  onChange={(e) => setCutEnd(parseFloat(e.target.value) || 0)}
                  className="w-full bg-surface-base border border-border-default rounded px-2.5 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent-blue"
                />
              </div>

              <div className="pt-2 flex gap-2">
                <button
                  onClick={handleApplyCut}
                  disabled={!sessionId || isProcessingPrompt || cutStart >= cutEnd}
                  className="flex-1 py-1.5 bg-accent-rose/90 hover:bg-accent-rose text-white rounded font-medium text-xs transition-colors disabled:opacity-50 flex items-center justify-center gap-1 shadow-sm"
                >
                  <Scissors className="w-3.5 h-3.5" />
                  Cut Range
                </button>
                <button
                  onClick={handleApplyTrim}
                  disabled={!sessionId || isProcessingPrompt || cutStart >= cutEnd}
                  className="flex-1 py-1.5 bg-accent-blue hover:bg-accent-blue/90 text-white rounded font-medium text-xs transition-colors disabled:opacity-50 flex items-center justify-center gap-1 shadow-sm"
                >
                  Trim Range
                </button>
              </div>
            </div>

            <div className="text-[10px] text-text-muted bg-surface-raised/40 p-2.5 rounded border border-border-default/60">
              <span className="font-semibold text-text-secondary">Note:</span> Operations are timeline-anchored. Downstream elements shift left automatically when cuts are performed.
            </div>
          </div>
        )}

        {/* Tab 2: Speed Multipliers */}
        {activeTab === 'speed' && (
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-semibold text-text-primary mb-1">Playback Speed</h3>
              <p className="text-[11px] text-text-muted">
                Accelerate or slow down the sequence. Pitch correction is applied automatically.
              </p>
            </div>

            <div className="space-y-3 bg-surface-raised p-3 rounded-md border border-border-default">
              <div className="grid grid-cols-3 gap-2">
                {[0.5, 0.75, 1.0, 1.25, 1.5, 2.0].map((rate) => (
                  <button
                    key={rate}
                    onClick={() => setSpeedVal(rate)}
                    className={`py-1.5 rounded font-mono text-xs border transition-colors ${
                      speedVal === rate
                        ? 'bg-accent-amber/20 border-accent-amber text-accent-amber font-semibold'
                        : 'bg-surface-base border-border-default text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                    }`}
                  >
                    {rate}x
                  </button>
                ))}
              </div>

              <div className="space-y-1 pt-1">
                <div className="flex justify-between text-[11px] text-text-secondary">
                  <span>Custom Speed</span>
                  <span className="font-mono text-accent-amber">{speedVal}x</span>
                </div>
                <input
                  type="range"
                  min="0.25"
                  max="4.0"
                  step="0.25"
                  value={speedVal}
                  onChange={(e) => setSpeedVal(parseFloat(e.target.value))}
                  className="w-full accent-accent-amber cursor-pointer"
                />
              </div>

              <div className="pt-2">
                <button
                  onClick={handleApplySpeed}
                  disabled={!sessionId || isProcessingPrompt}
                  className="w-full py-1.5 bg-accent-amber text-surface-base hover:bg-accent-amber/90 rounded font-medium text-xs transition-colors disabled:opacity-50 flex items-center justify-center gap-1 shadow-sm font-semibold"
                >
                  <Gauge className="w-3.5 h-3.5" />
                  Apply Speed ({speedVal}x)
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Subtitles / Captions */}
        {activeTab === 'caption' && (
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-semibold text-text-primary mb-1">Add Subtitle Overlay</h3>
              <p className="text-[11px] text-text-muted">
                Render custom subtitles with configurable timing and placement.
              </p>
            </div>

            <div className="space-y-3 bg-surface-raised p-3 rounded-md border border-border-default">
              <div className="space-y-1">
                <label className="text-[11px] text-text-secondary font-medium">Text Content</label>
                <input
                  type="text"
                  value={captionText}
                  onChange={(e) => setCaptionText(e.target.value)}
                  placeholder="Enter caption text..."
                  className="w-full bg-surface-base border border-border-default rounded px-2.5 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent-green"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[11px] text-text-secondary font-medium">Start (sec)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    value={captionStart}
                    onChange={(e) => setCaptionStart(parseFloat(e.target.value) || 0)}
                    className="w-full bg-surface-base border border-border-default rounded px-2 py-1 text-xs text-text-primary focus:outline-none focus:border-accent-green"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] text-text-secondary font-medium">Duration (sec)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0.5"
                    value={captionDuration}
                    onChange={(e) => setCaptionDuration(parseFloat(e.target.value) || 1)}
                    className="w-full bg-surface-base border border-border-default rounded px-2 py-1 text-xs text-text-primary focus:outline-none focus:border-accent-green"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] text-text-secondary font-medium">Position</label>
                <div className="grid grid-cols-3 gap-1.5">
                  {(['bottom', 'center', 'top'] as const).map((pos) => (
                    <button
                      key={pos}
                      type="button"
                      onClick={() => setCaptionPosition(pos)}
                      className={`py-1 rounded text-[11px] capitalize border transition-colors ${
                        captionPosition === pos
                          ? 'bg-accent-green/20 border-accent-green text-accent-green font-medium'
                          : 'bg-surface-base border-border-default text-text-secondary hover:text-text-primary'
                      }`}
                    >
                      {pos}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-2">
                <button
                  onClick={handleApplyCaption}
                  disabled={!sessionId || isProcessingPrompt || !captionText.trim()}
                  className="w-full py-1.5 bg-accent-green hover:bg-accent-green/90 text-surface-base rounded font-semibold text-xs transition-colors disabled:opacity-50 flex items-center justify-center gap-1 shadow-sm"
                >
                  <Type className="w-3.5 h-3.5" />
                  Add Subtitle
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab 4: Audio Controls */}
        {activeTab === 'audio' && (
          <div className="space-y-4">
            <div>
              <h3 className="text-xs font-semibold text-text-primary mb-1">Audio Processing</h3>
              <p className="text-[11px] text-text-muted">
                Adjust ducking level for voice clarity or mute tracks entirely.
              </p>
            </div>

            <div className="space-y-3 bg-surface-raised p-3 rounded-md border border-border-default">
              <div className="space-y-1">
                <div className="flex justify-between text-[11px] text-text-secondary">
                  <span>Audio Ducking</span>
                  <span className="font-mono text-accent-rose">{duckPercent}%</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="90"
                  step="5"
                  value={duckPercent}
                  onChange={(e) => setDuckPercent(parseInt(e.target.value, 10))}
                  className="w-full accent-accent-rose cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-text-muted">
                  <span>Subtle (-10%)</span>
                  <span>Default (-50%)</span>
                  <span>Heavy (-90%)</span>
                </div>
              </div>

              <div className="pt-1">
                <button
                  onClick={handleApplyDucking}
                  disabled={!sessionId || isProcessingPrompt}
                  className="w-full py-1.5 bg-surface-base hover:bg-surface-hover border border-accent-rose/50 hover:border-accent-rose text-accent-rose rounded font-medium text-xs transition-colors disabled:opacity-50 flex items-center justify-center gap-1"
                >
                  <Volume2 className="w-3.5 h-3.5" />
                  Apply Ducking ({duckPercent}%)
                </button>
              </div>

              <div className="pt-2 border-t border-border-default">
                <button
                  onClick={handleMuteAudio}
                  disabled={!sessionId || isProcessingPrompt}
                  className="w-full py-1.5 bg-surface-base hover:bg-surface-hover border border-border-default text-text-secondary hover:text-text-primary rounded font-medium text-xs transition-colors disabled:opacity-50 flex items-center justify-center gap-1"
                >
                  <Volume2 className="w-3.5 h-3.5 text-text-muted" />
                  Mute Timeline Audio
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Global Timeline Properties summary */}
        {timeline && (
          <div className="pt-4 border-t border-border-default space-y-2">
            <h4 className="text-[10px] uppercase font-semibold tracking-wider text-text-muted">Timeline Summary</h4>
            <div className="space-y-1 text-[11px] text-text-secondary bg-surface-raised/40 p-2.5 rounded border border-border-default">
              <div className="flex justify-between">
                <span className="text-text-muted">Duration:</span>
                <span className="font-mono text-text-primary">{duration.toFixed(2)}s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Segments:</span>
                <span className="font-mono text-text-primary">{timeline.segments.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Captions:</span>
                <span className="font-mono text-text-primary">{timeline.captions.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted">Target Resolution:</span>
                <span className="font-mono text-text-primary">Source Original (CFR 30fps)</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

import React, { useState, useRef, useEffect } from 'react';
import { useEditor } from '../context/EditorContext';
import { 
  Send, 
  Sparkles, 
  HelpCircle, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Film, 
  History, 
  Clock, 
  Zap,
  Play
} from 'lucide-react';

export const AIAssistantPanel: React.FC = () => {
  const { 
    chatMessages, 
    sendPrompt, 
    isProcessingPrompt, 
    sessionId, 
    timeline,
    historyCount,
    loadSampleVideo,
  } = useEditor();

  const [promptText, setPromptText] = useState('');
  const [activeTab, setActiveTab] = useState<'chat' | 'media' | 'history'>('chat');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isProcessingPrompt]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptText.trim() || isProcessingPrompt || !sessionId) return;
    const text = promptText.trim();
    setPromptText('');
    await sendPrompt(text);
  };

  const handleQuickPrompt = (prompt: string) => {
    if (isProcessingPrompt || !sessionId) return;
    sendPrompt(prompt);
  };

  const handleOptionClick = (say: string, option: string) => {
    if (isProcessingPrompt || !sessionId) return;
    sendPrompt(say, option);
  };

  return (
    <div className="flex flex-col h-full bg-surface-base border-r border-border-default select-none">
      {/* Panel Tab Header */}
      <div className="flex items-center border-b border-border-default px-2 py-1.5 bg-surface-raised gap-1">
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
            activeTab === 'chat'
              ? 'bg-surface-active text-text-primary shadow-sm'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-base'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-accent-blue" />
          AI Prompts
        </button>
        <button
          onClick={() => setActiveTab('media')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
            activeTab === 'media'
              ? 'bg-surface-active text-text-primary shadow-sm'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-base'
          }`}
        >
          <Film className="w-3.5 h-3.5 text-accent-green" />
          Media
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition-colors ${
            activeTab === 'history'
              ? 'bg-surface-active text-text-primary shadow-sm'
              : 'text-text-secondary hover:text-text-primary hover:bg-surface-base'
          }`}
        >
          <History className="w-3.5 h-3.5 text-accent-amber" />
          History
          {historyCount > 0 && (
            <span className="text-[10px] bg-surface-border text-text-secondary px-1.5 py-0.2 rounded-full">
              {historyCount}
            </span>
          )}
        </button>
      </div>

      {/* Tab: Media Browser */}
      {activeTab === 'media' && (
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2">Project Media</h3>
            {timeline ? (
              <div className="bg-surface-raised border border-border-default rounded-md p-3 space-y-2">
                <div className="flex items-center gap-2">
                  <Film className="w-4 h-4 text-accent-blue shrink-0" />
                  <span className="text-xs font-medium text-text-primary truncate">
                    {timeline.source_media?.sha256 ? `Source (${timeline.source_media.sha256.slice(0, 10)}...)` : 'Imported Video'}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-text-secondary pt-1 border-t border-border-default/50">
                  <div>
                    <span className="text-text-muted">Segments:</span> {timeline.segments.length}
                  </div>
                  <div>
                    <span className="text-text-muted">Captions:</span> {timeline.captions.length}
                  </div>
                  <div>
                    <span className="text-text-muted">Audio tracks:</span> {timeline.background_audio?.length ?? 0}
                  </div>
                  <div>
                    <span className="text-text-muted">Ducking:</span> {timeline.background_audio?.some(b => b.ducking?.enabled) ? 'Active' : 'Off'}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-xs text-text-muted p-4 text-center border border-dashed border-border-default rounded-md">
                No active media session.
              </div>
            )}
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2">Quick Synthetic Demo Assets</h3>
            <div className="space-y-2">
              <button
                onClick={loadSampleVideo}
                className="w-full text-left p-2.5 rounded border border-border-default bg-surface-raised hover:bg-surface-hover hover:border-accent-blue/50 transition-colors text-xs flex items-center justify-between"
              >
                <div>
                  <div className="font-medium text-text-primary">interview.mp4</div>
                  <div className="text-[10px] text-text-muted">Synthetic 2-speaker talk with audio (10s)</div>
                </div>
                <Play className="w-3.5 h-3.5 text-accent-blue" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab: History Stack */}
      {activeTab === 'history' && (
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted">Session Edit Stack</h3>
            <span className="text-[11px] text-text-secondary">{historyCount} snapshots</span>
          </div>

          {timeline ? (
            <div className="space-y-2">
              <div className="p-2.5 rounded bg-surface-raised border border-accent-blue/30 text-xs">
                <div className="flex items-center justify-between font-medium text-accent-blue">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-accent-green" />
                    Current State
                  </span>
                  <span className="text-[10px] text-text-muted">Active</span>
                </div>
                <div className="text-[11px] text-text-secondary mt-1">
                  {timeline.segments.length} segment(s), {timeline.captions.length} caption(s)
                </div>
              </div>

              {historyCount > 1 && (
                <div className="p-2.5 rounded bg-surface-raised/50 border border-border-default text-xs text-text-secondary">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-text-muted" />
                      Prior Checkpoints
                    </span>
                    <span className="text-[10px] text-text-muted">{historyCount - 1} available</span>
                  </div>
                  <p className="text-[11px] text-text-muted mt-1">
                    Use the <strong>Undo</strong> button in the top bar or type "undo" to roll back changes idempotently.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-xs text-text-muted p-4 text-center border border-dashed border-border-default rounded-md">
              No session loaded.
            </div>
          )}
        </div>
      )}

      {/* Tab: Chat / AI Prompts */}
      {activeTab === 'chat' && (
        <>
          {/* Quick Prompt Chips */}
          <div className="px-3 py-2 border-b border-border-default bg-surface-base/80 overflow-x-auto">
            <div className="flex items-center gap-1.5 text-[11px] whitespace-nowrap">
              <span className="text-text-muted flex items-center gap-1 text-[10px] uppercase font-semibold">
                <Zap className="w-3 h-3 text-accent-amber" /> Try:
              </span>
              <button
                onClick={() => handleQuickPrompt("Cut from 0s to 3s")}
                disabled={isProcessingPrompt || !sessionId}
                className="px-2 py-0.5 rounded bg-surface-raised hover:bg-surface-hover text-text-secondary border border-border-default hover:border-accent-blue/40 transition-colors disabled:opacity-50"
              >
                Cut 0s-3s
              </button>
              <button
                onClick={() => handleQuickPrompt("Speed up to 2x")}
                disabled={isProcessingPrompt || !sessionId}
                className="px-2 py-0.5 rounded bg-surface-raised hover:bg-surface-hover text-text-secondary border border-border-default hover:border-accent-blue/40 transition-colors disabled:opacity-50"
              >
                Speed 2x
              </button>
              <button
                onClick={() => handleQuickPrompt("Add subtitle 'Welcome to EditFlow' at 1s for 3s")}
                disabled={isProcessingPrompt || !sessionId}
                className="px-2 py-0.5 rounded bg-surface-raised hover:bg-surface-hover text-text-secondary border border-border-default hover:border-accent-blue/40 transition-colors disabled:opacity-50"
              >
                Add Subtitle
              </button>
              <button
                onClick={() => handleQuickPrompt("Auto-caption the whole video")}
                disabled={isProcessingPrompt || !sessionId}
                className="px-2 py-0.5 rounded bg-surface-raised hover:bg-surface-hover text-text-secondary border border-border-default hover:border-accent-blue/40 transition-colors disabled:opacity-50"
              >
                Auto-Caption
              </button>
              <button
                onClick={() => handleQuickPrompt("Remove filler words")}
                disabled={isProcessingPrompt || !sessionId}
                className="px-2 py-0.5 rounded bg-surface-raised hover:bg-surface-hover text-text-secondary border border-border-default hover:border-accent-blue/40 transition-colors disabled:opacity-50"
              >
                Remove Fillers
              </button>
              <button
                onClick={() => handleQuickPrompt("Undo")}
                disabled={isProcessingPrompt || !sessionId}
                className="px-2 py-0.5 rounded bg-surface-raised hover:bg-surface-hover text-text-secondary border border-border-default hover:border-accent-blue/40 transition-colors disabled:opacity-50"
              >
                Undo
              </button>
            </div>
          </div>

          {/* Chat Messages Feed */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {chatMessages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 text-text-muted space-y-3">
                <div className="w-10 h-10 rounded-full bg-surface-raised flex items-center justify-center border border-border-default">
                  <Sparkles className="w-5 h-5 text-accent-blue" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-xs font-semibold text-text-primary">Natural Language Video Editing</h4>
                  <p className="text-[11px] max-w-[240px] text-text-secondary leading-relaxed">
                    Type editing instructions in English. The engine deterministically cuts, trims, adjusts speeds, places captions, and ducks audio.
                  </p>
                </div>
                {!sessionId && (
                  <button
                    onClick={loadSampleVideo}
                    className="px-3 py-1.5 bg-accent-blue hover:bg-accent-blue/90 text-white rounded text-xs font-medium transition-colors shadow-sm"
                  >
                    Load Sample Project
                  </button>
                )}
              </div>
            ) : (
              chatMessages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[92%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                      msg.sender === 'user'
                        ? 'bg-accent-blue text-white shadow-sm'
                        : 'bg-surface-raised border border-border-default text-text-primary shadow-sm'
                    }`}
                  >
                    {/* Assistant Status Badge */}
                    {msg.sender === 'assistant' && msg.status && (
                      <div className="flex items-center gap-1.5 mb-1.5 pb-1 border-b border-border-default/60">
                        {msg.status === 'applied' && (
                          <span className="flex items-center gap-1 text-[10px] font-medium text-accent-green">
                            <CheckCircle2 className="w-3 h-3" />
                            Applied
                          </span>
                        )}
                        {msg.status === 'needs_clarification' && (
                          <span className="flex items-center gap-1 text-[10px] font-medium text-accent-amber">
                            <HelpCircle className="w-3 h-3" />
                            Needs Clarification
                          </span>
                        )}
                        {msg.status === 'rejected' && (
                          <span className="flex items-center gap-1 text-[10px] font-medium text-accent-rose">
                            <XCircle className="w-3 h-3" />
                            Rejected
                          </span>
                        )}
                      </div>
                    )}

                    <div className="whitespace-pre-wrap">{msg.text}</div>

                    {/* Interactive Clarification Option Buttons */}
                    {msg.status === 'needs_clarification' && msg.options && msg.options.length > 0 && (
                      <div className="mt-2.5 pt-2 border-t border-border-default space-y-1.5">
                        <div className="text-[10px] font-medium text-text-secondary">Select an option:</div>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.options.map((option, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleOptionClick(msg.text, option)}
                              disabled={isProcessingPrompt}
                              className="px-2.5 py-1 text-xs bg-surface-base hover:bg-surface-hover border border-accent-amber/40 hover:border-accent-amber rounded text-text-primary transition-colors text-left"
                            >
                              {option}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Warnings Badge if Present */}
                    {msg.warnings && msg.warnings.length > 0 && (
                      <div className="mt-2 pt-1 border-t border-border-default/60 space-y-0.5">
                        {msg.warnings.map((w, idx) => (
                          <div key={idx} className="flex items-center gap-1 text-[10px] text-accent-amber">
                            <AlertTriangle className="w-2.5 h-2.5 shrink-0" />
                            <span>{w}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <span className="text-[9px] text-text-muted mt-1 px-1">
                    {msg.timestamp}
                  </span>
                </div>
              ))
            )}

            {/* In-Flight Processing Indicator */}
            {isProcessingPrompt && (
              <div className="flex items-center gap-2 text-xs text-text-secondary p-2 bg-surface-raised rounded-lg border border-border-default animate-pulse">
                <Sparkles className="w-3.5 h-3.5 text-accent-blue animate-spin" />
                <span>Processing instruction & updating timeline...</span>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Prompt Input Form */}
          <div className="p-3 border-t border-border-default bg-surface-raised">
            <form onSubmit={handleSubmit} className="relative">
              <textarea
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                disabled={!sessionId || isProcessingPrompt}
                placeholder={
                  sessionId
                    ? "Type prompt (e.g., 'Cut from 2s to 6s', 'Speed up 2x')..."
                    : "Load or upload a video to start editing..."
                }
                rows={2}
                className="w-full bg-surface-base border border-border-default rounded-md px-3 py-2 pr-10 text-xs text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue resize-none disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!promptText.trim() || isProcessingPrompt || !sessionId}
                aria-label="Send prompt"
                className="absolute right-2.5 bottom-3.5 p-1.5 bg-accent-blue hover:bg-accent-blue/90 disabled:bg-surface-border text-white rounded transition-colors disabled:text-text-muted"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
            <div className="flex items-center justify-between text-[10px] text-text-muted mt-1.5 px-0.5">
              <span>Press Enter to execute • Shift+Enter for newline</span>
              <span className="text-accent-blue font-mono">Time policy: Timeline</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

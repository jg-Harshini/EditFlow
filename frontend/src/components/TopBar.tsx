import React, { useState } from 'react';
import { useEditor } from '../context/EditorContext';
import {
  Undo2,
  Redo2,
  Download,
  Film,
  Sparkles,
  HelpCircle,
  FolderOpen,
  FileCode2,
  CheckCircle2,
  Clock,
} from 'lucide-react';

interface TopBarProps {
  onOpenUpload: () => void;
  onOpenExport: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({ onOpenUpload, onOpenExport }) => {
  const {
    sessionId,
    canUndo,
    canRedo,
    undo,
    redo,
    exportOTIO,
    loadSampleVideo,
    isLoading,
  } = useEditor();

  const [showHelp, setShowHelp] = useState(false);

  const handleExportOTIO = async () => {
    await exportOTIO();
  };

  return (
    <>
      <header className="h-14 bg-editor-panel border-b border-editor-border px-4 flex items-center justify-between shrink-0 select-none z-20">
        {/* Brand & Project Info */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <Film className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-sm tracking-tight text-white">EditFlow AI</span>
                <span className="text-[10px] font-medium text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-1.5 py-0.5 rounded">
                  Studio
                </span>
              </div>
              <p className="text-[11px] text-editor-muted">IncuBrix Prompt-Based Video Engine</p>
            </div>
          </div>

          <div className="h-4 w-px bg-editor-border mx-1" />

          {/* Project Status */}
          <div className="flex items-center gap-2">
            <button
              onClick={onOpenUpload}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs rounded bg-editor-subpanel hover:bg-editor-hover border border-editor-border text-zinc-300 transition"
              title="Upload new video or ingest from URL"
            >
              <FolderOpen className="w-3.5 h-3.5 text-zinc-400" />
              <span>Media</span>
            </button>

            {!sessionId && (
              <button
                onClick={loadSampleVideo}
                disabled={isLoading}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs rounded bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 transition"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Load Sample Video</span>
              </button>
            )}

            {sessionId && (
              <div className="flex items-center gap-2 text-xs bg-editor-subpanel/60 border border-editor-border/60 px-2.5 py-1 rounded">
                <span className="text-zinc-400">Session:</span>
                <code className="text-zinc-200 font-mono text-[11px]">{sessionId.slice(0, 8)}</code>
                <span className="text-zinc-600">•</span>
                <span className="flex items-center gap-1 text-emerald-400 text-[11px]">
                  <CheckCircle2 className="w-3 h-3" /> Locked Master
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Center: Undo / Redo & Timeline Time Policy */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-editor-subpanel border border-editor-border rounded p-0.5">
            <button
              onClick={undo}
              disabled={!canUndo || isLoading}
              className={`p-1.5 rounded transition ${
                canUndo && !isLoading
                  ? 'text-zinc-200 hover:bg-editor-hover hover:text-white'
                  : 'text-zinc-600 cursor-not-allowed'
              }`}
              title="Undo last instruction (Must-Have 6)"
            >
              <Undo2 className="w-4 h-4" />
            </button>
            <div className="h-3 w-px bg-editor-border mx-0.5" />
            <button
              onClick={redo}
              disabled={!canRedo || isLoading}
              className={`p-1.5 rounded transition ${
                canRedo && !isLoading
                  ? 'text-zinc-200 hover:bg-editor-hover hover:text-white'
                  : 'text-zinc-600 cursor-not-allowed'
              }`}
              title="Redo previously undone edit"
            >
              <Redo2 className="w-4 h-4" />
            </button>
          </div>

          <div className="hidden md:flex items-center gap-1.5 text-[11px] text-zinc-400 bg-editor-subpanel/40 border border-editor-border/40 px-2.5 py-1 rounded">
            <Clock className="w-3 h-3 text-indigo-400" />
            <span>Policy: <strong className="text-zinc-300">Current Timeline Time</strong></span>
          </div>
        </div>

        {/* Right: Export & Help */}
        <div className="flex items-center gap-2.5">
          {sessionId && (
            <button
              onClick={handleExportOTIO}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-editor-subpanel hover:bg-editor-hover text-zinc-300 border border-editor-border rounded transition"
              title="Export editorial timeline to OpenTimelineIO schema"
            >
              <FileCode2 className="w-3.5 h-3.5 text-zinc-400" />
              <span className="hidden sm:inline">Export OTIO</span>
            </button>
          )}

          <button
            onClick={onOpenExport}
            disabled={!sessionId || isLoading}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded shadow-md transition ${
              sessionId && !isLoading
                ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20'
                : 'bg-zinc-800 text-zinc-500 cursor-not-allowed border border-zinc-700/50'
            }`}
          >
            <Download className="w-3.5 h-3.5" />
            <span>Render Video</span>
          </button>

          <button
            onClick={() => setShowHelp(true)}
            className="p-1.5 text-zinc-400 hover:text-zinc-200 hover:bg-editor-hover rounded transition"
            title="Help and Assessment Guide"
          >
            <HelpCircle className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Help Modal */}
      {showHelp && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="bg-editor-panel border border-editor-border rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-editor-border pb-3">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" /> EditFlow AI — Quick Guide
              </h3>
              <button
                onClick={() => setShowHelp(false)}
                className="text-zinc-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>
            <div className="text-xs text-zinc-300 space-y-3 leading-relaxed">
              <p>
                <strong>IncuBrix Prompt-Based Video Editing Engine</strong> is a non-destructive, content-anchored editor.
              </p>
              <div className="bg-editor-subpanel p-3 rounded border border-editor-border space-y-1.5">
                <div className="font-medium text-white">How Edits Work:</div>
                <p>
                  1. Edits belong to <em>content</em> (spoken words and audio), not clock positions.
                </p>
                <p>
                  2. Captions and mutes follow words even after earlier clips are cut or sped up.
                </p>
                <p>
                  3. Destructive commands (e.g. "Remove pricing") ask for clarification when ambiguous instead of guessing.
                </p>
              </div>
              <div className="space-y-1">
                <span className="font-medium text-white">Sample Instructions:</span>
                <ul className="list-disc list-inside text-zinc-400 space-y-0.5">
                  <li>"Add a caption 'Welcome!' when I say welcome to the channel"</li>
                  <li>"Cut the first 30 seconds"</li>
                  <li>"Remove the part about pricing"</li>
                  <li>"Speed up from 1:00 to 1:30 by 2x"</li>
                  <li>"Actually, put the intro back"</li>
                  <li>"Make that caption red"</li>
                  <li>"render"</li>
                </ul>
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowHelp(false)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold transition"
              >
                Got it
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

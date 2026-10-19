import React, { useState, useEffect } from 'react';
import { useEditor } from './context/EditorContext';
import { TopBar } from './components/TopBar';
import { AIAssistantPanel } from './components/AIAssistantPanel';
import { VideoPreview } from './components/VideoPreview';
import { PropertiesPanel } from './components/PropertiesPanel';
import { TimelinePanel } from './components/TimelinePanel';
import { MediaUploadModal } from './components/MediaUploadModal';
import { ExportModal } from './components/ExportModal';
import { AlertCircle, X } from 'lucide-react';

export const App: React.FC = () => {
  const { 
    error, 
    clearError, 
    isPlaying, 
    setIsPlaying, 
    currentTime, 
    seekTo, 
    duration,
    canUndo,
    canRedo,
    undo,
    redo 
  } = useEditor();

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept shortcuts when typing in inputs or textareas
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea') return;

      // Space: Play / Pause
      if (e.code === 'Space') {
        e.preventDefault();
        setIsPlaying(!isPlaying);
      }

      // Left Arrow: Seek back
      if (e.code === 'ArrowLeft') {
        e.preventDefault();
        const step = e.shiftKey ? 5 : 1;
        seekTo(Math.max(currentTime - step, 0));
      }

      // Right Arrow: Seek forward
      if (e.code === 'ArrowRight') {
        e.preventDefault();
        const step = e.shiftKey ? 5 : 1;
        seekTo(Math.min(currentTime + step, duration));
      }

      // Ctrl+Z or Cmd+Z: Undo
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !e.shiftKey) {
        e.preventDefault();
        if (canUndo) undo();
      }

      // Ctrl+Y or Cmd+Shift+Z or Ctrl+Shift+Z: Redo
      if (
        ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y') ||
        ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'z')
      ) {
        e.preventDefault();
        if (canRedo) redo();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPlaying, setIsPlaying, currentTime, seekTo, duration, canUndo, canRedo, undo, redo]);

  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-surface-base text-text-primary select-none">
      {/* Top Application Bar */}
      <TopBar 
        onOpenUpload={() => setIsUploadOpen(true)}
        onOpenExport={() => setIsExportOpen(true)}
      />

      {/* Global Error Banner */}
      {error && (
        <div className="bg-accent-rose/15 border-b border-accent-rose/30 px-4 py-2 flex items-center justify-between text-xs text-accent-rose shrink-0 z-30">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="font-medium">{error}</span>
          </div>
          <button 
            onClick={clearError}
            className="p-1 hover:bg-accent-rose/20 rounded transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main 3-Column Studio Workspace */}
      <div className="flex-1 flex flex-row overflow-hidden min-h-0">
        {/* Left: AI Prompt & Asset Assistant */}
        <aside className="w-80 lg:w-[380px] shrink-0 h-full border-r border-border-default z-10 flex flex-col">
          <AIAssistantPanel />
        </aside>

        {/* Center: Video Preview Monitor & Transport Controls */}
        <main className="flex-1 h-full min-w-0 flex flex-col bg-surface-base">
          <VideoPreview />
        </main>

        {/* Right: Contextual Properties & Manual Overrides */}
        <aside className="w-72 lg:w-80 shrink-0 h-full border-l border-border-default hidden md:flex flex-col z-10">
          <PropertiesPanel />
        </aside>
      </div>

      {/* Bottom: Content-Anchored Timeline Panel */}
      <footer className="h-56 shrink-0 border-t border-border-default bg-surface-base z-20">
        <TimelinePanel />
      </footer>

      {/* Modal Overlays */}
      <MediaUploadModal 
        isOpen={isUploadOpen} 
        onClose={() => setIsUploadOpen(false)} 
      />

      <ExportModal 
        isOpen={isExportOpen} 
        onClose={() => setIsExportOpen(false)} 
      />
    </div>
  );
};
export default App;

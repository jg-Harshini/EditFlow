import React, { useState, useRef } from 'react';
import { useEditor } from '../context/EditorContext';
import { 
  X, 
  UploadCloud, 
  Link, 
  Film, 
  AlertCircle, 
  CheckCircle2, 
  Sparkles, 
  FileVideo,
  Play
} from 'lucide-react';

interface MediaUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MediaUploadModal: React.FC<MediaUploadModalProps> = ({ isOpen, onClose }) => {
  const { uploadVideo, ingestUrl, createSession, isLoading, error, clearError } = useEditor();

  const [activeTab, setActiveTab] = useState<'upload' | 'url' | 'synthetic'>('upload');
  const [urlInput, setUrlInput] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      handleFileSelected(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (file: File) => {
    setLocalError(null);
    clearError();
    const validExtensions = ['.mp4', '.mov', '.mkv', '.webm', '.avi'];
    const hasValidExt = validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext));

    if (!hasValidExt) {
      setLocalError(`Unsupported video format. Allowed formats: ${validExtensions.join(', ')}`);
      return;
    }

    if (file.size > 200 * 1024 * 1024) {
      setLocalError('File size exceeds the 200MB test limit.');
      return;
    }

    setSelectedFile(file);
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;
    try {
      await uploadVideo(selectedFile);
      onClose();
    } catch (err) {
      // Error is tracked in context
    }
  };

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;
    setLocalError(null);
    clearError();

    // Quick client-side check
    const trimmed = urlInput.trim();
    if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
      setLocalError('URL must begin with http:// or https://');
      return;
    }

    try {
      await ingestUrl(trimmed);
      onClose();
    } catch (err) {
      // Error is tracked in context
    }
  };

  const handleLoadSynthetic = async (path: string) => {
    setLocalError(null);
    clearError();
    try {
      await createSession(path);
      onClose();
    } catch (err) {
      // Error handled in context
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div 
        className="w-full max-w-lg bg-surface-base border border-border-default rounded-xl shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border-default bg-surface-raised">
          <div className="flex items-center gap-2">
            <Film className="w-5 h-5 text-accent-blue" />
            <h2 className="text-sm font-semibold text-text-primary">Import Media Asset</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-text-muted hover:text-text-primary rounded-md hover:bg-surface-base transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-border-default bg-surface-raised/50 px-5 gap-2 pt-2">
          <button
            onClick={() => setActiveTab('upload')}
            className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
              activeTab === 'upload'
                ? 'border-accent-blue text-accent-blue'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" />
            Upload File
          </button>
          <button
            onClick={() => setActiveTab('url')}
            className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
              activeTab === 'url'
                ? 'border-accent-blue text-accent-blue'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <Link className="w-3.5 h-3.5" />
            Remote URL
          </button>
          <button
            onClick={() => setActiveTab('synthetic')}
            className={`pb-2.5 px-3 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
              activeTab === 'synthetic'
                ? 'border-accent-blue text-accent-blue'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-accent-amber" />
            Sample Assets
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-5 flex-1 space-y-4">
          {/* Error Alert */}
          {(localError || error) && (
            <div className="p-3 bg-accent-rose/10 border border-accent-rose/30 rounded-lg flex items-start gap-2.5 text-xs text-accent-rose">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div className="flex-1 font-medium">{localError || error}</div>
            </div>
          )}

          {/* Tab 1: File Upload */}
          {activeTab === 'upload' && (
            <div className="space-y-4">
              <input
                ref={fileInputRef}
                type="file"
                accept=".mp4,.mov,.mkv,.webm,.avi,video/*"
                onChange={handleFileChange}
                className="hidden"
              />

              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  dragActive
                    ? 'border-accent-blue bg-accent-blue/5'
                    : 'border-border-default hover:border-accent-blue/50 bg-surface-raised/40'
                }`}
              >
                <div className="w-12 h-12 rounded-full bg-surface-raised flex items-center justify-center mx-auto mb-3 border border-border-default">
                  <UploadCloud className="w-6 h-6 text-accent-blue" />
                </div>
                <div className="text-xs font-medium text-text-primary">
                  Click to browse or drag and drop video
                </div>
                <div className="text-[11px] text-text-muted mt-1">
                  MP4, MOV, MKV, WebM up to 200MB
                </div>
              </div>

              {selectedFile && (
                <div className="p-3 bg-surface-raised border border-border-default rounded-lg flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 truncate pr-2">
                    <FileVideo className="w-4 h-4 text-accent-blue shrink-0" />
                    <span className="font-medium text-text-primary truncate">{selectedFile.name}</span>
                    <span className="text-[10px] text-text-muted shrink-0">
                      ({(selectedFile.size / (1024 * 1024)).toFixed(1)} MB)
                    </span>
                  </div>
                  <span className="text-[10px] text-accent-green flex items-center gap-1 font-medium shrink-0">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Ready
                  </span>
                </div>
              )}

              <button
                onClick={handleUploadSubmit}
                disabled={!selectedFile || isLoading}
                className="w-full py-2 bg-accent-blue hover:bg-accent-blue/90 disabled:bg-surface-border text-white rounded-lg text-xs font-medium transition-colors disabled:text-text-muted flex items-center justify-center gap-2 shadow-sm"
              >
                {isLoading ? (
                  <>
                    <Sparkles className="w-3.5 h-3.5 animate-spin" />
                    Uploading & Ingesting Video...
                  </>
                ) : (
                  'Start Editing Video'
                )}
              </button>
            </div>
          )}

          {/* Tab 2: Remote URL Ingest */}
          {activeTab === 'url' && (
            <form onSubmit={handleUrlSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-text-secondary">Video URL</label>
                <input
                  type="url"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="https://example.com/sample-video.mp4"
                  className="w-full bg-surface-raised border border-border-default rounded-lg px-3 py-2 text-xs text-text-primary placeholder-text-muted focus:outline-none focus:border-accent-blue"
                />
                <p className="text-[10px] text-text-muted leading-relaxed">
                  EditFlow verifies remote URLs with strict SSRF protection (prohibiting RFC 1918 private IPs, AWS/GCP metadata endpoints, and non-HTTP protocols).
                </p>
              </div>

              <button
                type="submit"
                disabled={!urlInput.trim() || isLoading}
                className="w-full py-2 bg-accent-blue hover:bg-accent-blue/90 disabled:bg-surface-border text-white rounded-lg text-xs font-medium transition-colors disabled:text-text-muted flex items-center justify-center gap-2 shadow-sm"
              >
                {isLoading ? (
                  <>
                    <Sparkles className="w-3.5 h-3.5 animate-spin" />
                    Fetching & Inspecting URL...
                  </>
                ) : (
                  'Ingest & Open Project'
                )}
              </button>
            </form>
          )}

          {/* Tab 3: Synthetic Test Assets */}
          {activeTab === 'synthetic' && (
            <div className="space-y-3">
              <p className="text-xs text-text-muted">
                Pre-generated synthetic test assets matching Assessment 2 verification suites:
              </p>

              <div className="space-y-2">
                <button
                  onClick={() => handleLoadSynthetic('test_pack/assets/demo_speech.mp4')}
                  disabled={isLoading}
                  className="w-full p-3 rounded-lg border border-indigo-500/40 bg-indigo-950/20 hover:bg-indigo-900/30 hover:border-indigo-400 transition-colors text-left flex items-center justify-between group"
                >
                  <div>
                    <div className="text-xs font-semibold text-indigo-300 group-hover:text-indigo-200 flex items-center gap-1.5">
                      demo_speech.mp4
                      <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded font-mono">Dynamic Voice & Subtitles</span>
                    </div>
                    <div className="text-[11px] text-text-muted mt-0.5">
                      12s real voice video for demonstrating dynamic Faster-Whisper transcription & auto-subtitling
                    </div>
                  </div>
                  <Play className="w-4 h-4 text-indigo-400 shrink-0 ml-2" />
                </button>

                <button
                  onClick={() => handleLoadSynthetic('test_pack/assets/interview.mp4')}
                  disabled={isLoading}
                  className="w-full p-3 rounded-lg border border-border-default bg-surface-raised hover:bg-surface-hover hover:border-accent-blue/50 transition-colors text-left flex items-center justify-between group"
                >
                  <div>
                    <div className="text-xs font-medium text-text-primary group-hover:text-accent-blue">
                      interview.mp4
                    </div>
                    <div className="text-[11px] text-text-muted">
                      10s synthetic 2-speaker dialogue with visual color markers and speech tones
                    </div>
                  </div>
                  <Play className="w-4 h-4 text-accent-blue shrink-0 ml-2" />
                </button>

                <button
                  onClick={() => handleLoadSynthetic('test_pack/assets/multispeaker.mp4')}
                  disabled={isLoading}
                  className="w-full p-3 rounded-lg border border-border-default bg-surface-raised hover:bg-surface-hover hover:border-accent-blue/50 transition-colors text-left flex items-center justify-between group"
                >
                  <div>
                    <div className="text-xs font-medium text-text-primary group-hover:text-accent-blue">
                      multispeaker.mp4
                    </div>
                    <div className="text-[11px] text-text-muted">
                      Multi-speaker synthetic video for anchoring and transcript alignment testing
                    </div>
                  </div>
                  <Play className="w-4 h-4 text-accent-blue shrink-0 ml-2" />
                </button>

                <button
                  onClick={() => handleLoadSynthetic('test_pack/assets/short_test.mp4')}
                  disabled={isLoading}
                  className="w-full p-3 rounded-lg border border-border-default bg-surface-raised hover:bg-surface-hover hover:border-accent-blue/50 transition-colors text-left flex items-center justify-between group"
                >
                  <div>
                    <div className="text-xs font-medium text-text-primary group-hover:text-accent-blue">
                      short_test.mp4
                    </div>
                    <div className="text-[11px] text-text-muted">
                      5s rapid test video for fast smoke verification
                    </div>
                  </div>
                  <Play className="w-4 h-4 text-accent-blue shrink-0 ml-2" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

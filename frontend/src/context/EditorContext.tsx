import React, { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';
import { api } from '../api/client';
import { Timeline, JobStatusResponse, StepResult, JobAcceptedResponse } from '../types/api';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  status?: 'applied' | 'needs_clarification' | 'rejected';
  question?: string | null;
  options?: string[] | null;
  warnings?: string[];
  videoUrl?: string | null;
  timestamp: string;
}

interface EditorContextType {
  sessionId: string | null;
  timeline: Timeline | null;
  videoUri: string | null;
  activeVideoUrl: string | null;
  historyCount: number;
  canUndo: boolean;
  canRedo: boolean;
  isLoading: boolean;
  isProcessingPrompt: boolean;
  activeJob: JobStatusResponse | null;
  chatMessages: ChatMessage[];
  currentTime: number;
  duration: number;
  isPlaying: boolean;
  seekTime: number | null;
  selectedSegmentId: string | null;
  selectedCaptionId: string | null;
  error: string | null;

  // Actions
  createSession: (videoUri: string) => Promise<void>;
  loadSampleVideo: () => Promise<void>;
  uploadVideo: (file: File) => Promise<void>;
  ingestUrl: (url: string) => Promise<void>;
  sendPrompt: (say: string, answer?: string) => Promise<void>;
  undo: () => Promise<void>;
  redo: () => Promise<void>;
  triggerRender: () => Promise<void>;
  exportOTIO: () => Promise<string | null>;
  seekTo: (seconds: number) => void;
  setCurrentTime: (seconds: number) => void;
  setDuration: (seconds: number) => void;
  setIsPlaying: (playing: boolean) => void;
  selectSegment: (segmentId: string | null) => void;
  selectCaption: (captionId: string | null) => void;
  clearError: () => void;
}

const EditorContext = createContext<EditorContextType | undefined>(undefined);

export const EditorProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [videoUri, setVideoUri] = useState<string | null>(null);
  const [activeVideoUrl, setActiveVideoUrl] = useState<string | null>(null);
  const [historyCount, setHistoryCount] = useState<number>(0);
  const [canUndo, setCanUndo] = useState<boolean>(false);
  const [canRedo, setCanRedo] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isProcessingPrompt, setIsProcessingPrompt] = useState<boolean>(false);
  const [activeJob, setActiveJob] = useState<JobStatusResponse | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [seekTime, setSeekTime] = useState<number | null>(null);
  const [selectedSegmentId, setSelectedSegmentId] = useState<string | null>(null);
  const [selectedCaptionId, setSelectedCaptionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Poll active background jobs
  const hasFiredSuccessRef = useRef(false);

  useEffect(() => {
    if (!activeJob || activeJob.status === 'succeeded' || activeJob.status === 'failed') {
      hasFiredSuccessRef.current = false;
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await api.getJobStatus(activeJob.job_id);

        if (updated.status === 'succeeded') {
          clearInterval(interval);
          setActiveJob(updated);
          if (!hasFiredSuccessRef.current) {
            hasFiredSuccessRef.current = true;
            const downloadUrl = updated.result?.download_url;
            if (downloadUrl) {
              setActiveVideoUrl(downloadUrl);
            }
            addAssistantMessage(
              `Render finished successfully! Length: ${updated.result?.metadata?.actual_duration_s ?? 'N/A'}s (frame difference: ${updated.result?.metadata?.difference_frames ?? 0}).`,
              'applied',
              downloadUrl
            );
          }
        } else if (updated.status === 'failed') {
          clearInterval(interval);
          setActiveJob(updated);
          addAssistantMessage(`Render failed: ${updated.error?.message || 'Unknown render error'}`, 'rejected');
        } else {
          setActiveJob(updated);
        }
      } catch (err: any) {
        console.error('Job polling failed:', err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [activeJob?.job_id]);

  const addAssistantMessage = (
    text: string,
    status?: 'applied' | 'needs_clarification' | 'rejected',
    videoUrl?: string | null,
    question?: string | null,
    options?: string[] | null,
    warnings?: string[]
  ) => {
    const msg: ChatMessage = {
      id: Math.random().toString(36).substring(2, 9),
      sender: 'assistant',
      text,
      status,
      videoUrl,
      question,
      options,
      warnings,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setChatMessages((prev) => [...prev, msg]);
  };

  const addUserMessage = (text: string) => {
    const msg: ChatMessage = {
      id: Math.random().toString(36).substring(2, 9),
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setChatMessages((prev) => [...prev, msg]);
  };

  const refreshSessionState = useCallback(async (sid: string) => {
    try {
      const details = await api.getSession(sid);
      setTimeline(details.timeline);
      setHistoryCount(details.history_count);
      setCanUndo(details.history_count > 1);
      // Can redo is true if undo was previously called and redo stack is non-empty
      setDuration(details.duration_s);
    } catch (err) {
      console.error('Failed to refresh session state:', err);
    }
  }, []);

  const createSession = useCallback(async (uri: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.createSession(uri);
      setSessionId(res.session_id);
      setTimeline(res.timeline);
      setVideoUri(res.video_uri);
      setDuration(res.duration_s);
      setHistoryCount(1);
      setCanUndo(false);
      setCanRedo(false);

      // Determine streamable URL
      if (res.video_uri.startsWith('http://') || res.video_uri.startsWith('https://')) {
        setActiveVideoUrl(res.video_uri);
      } else {
        const filename = res.video_uri.split(/[\\/]/).pop() || '';
        setActiveVideoUrl(`/api/v1/media/${filename}`);
      }

      addAssistantMessage(
        `Session created! Video duration: ${res.duration_s.toFixed(1)}s (${res.timeline.segments.length} segment). Original file hash locked. You can now use AI commands or visual controls to edit.`,
        'applied'
      );
    } catch (err: any) {
      setError(err.message || 'Failed to initialize session');
      addAssistantMessage(`Failed to create session: ${err.message}`, 'rejected');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadSampleVideo = useCallback(async () => {
    await createSession('test_pack/assets/interview.mp4');
  }, [createSession]);

  const uploadVideo = useCallback(async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const ingested = await api.uploadMedia(file);
      await createSession(ingested.file_path);
    } catch (err: any) {
      setError(err.message || 'Video upload failed');
      addAssistantMessage(`Upload failed: ${err.message}`, 'rejected');
    } finally {
      setIsLoading(false);
    }
  }, [createSession]);

  const ingestUrl = useCallback(async (url: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const ingested = await api.ingestMediaUrl(url);
      await createSession(ingested.file_path);
    } catch (err: any) {
      setError(err.message || 'URL ingestion failed');
      addAssistantMessage(`Failed to ingest URL: ${err.message}`, 'rejected');
    } finally {
      setIsLoading(false);
    }
  }, [createSession]);

  const sendPrompt = useCallback(async (say: string, answer?: string) => {
    if (!sessionId) {
      setError('Please load or upload a video first.');
      return;
    }

    addUserMessage(answer ? `${say} (Choice: ${answer})` : say);
    setIsProcessingPrompt(true);
    setError(null);

    try {
      const result = await api.executeStep(sessionId, say, answer);

      // Check if response is background Job
      if ('poll_url' in result) {
        const jobAccept = result as JobAcceptedResponse;
        setActiveJob({
          job_id: jobAccept.job_id,
          status: 'queued',
          progress: 0,
        });
        addAssistantMessage(
          `Render task queued in background (Job ID: ${jobAccept.job_id.slice(0, 8)}). Processing...`,
          'applied'
        );
      } else {
        const stepRes = result as StepResult;
        if (stepRes.status === 'applied') {
          addAssistantMessage(stepRes.summary, 'applied', stepRes.video_url, null, null, stepRes.warnings);
          await refreshSessionState(sessionId);
        } else if (stepRes.status === 'needs_clarification') {
          addAssistantMessage(
            stepRes.question || 'Please clarify your instruction.',
            'needs_clarification',
            null,
            stepRes.question,
            stepRes.options
          );
        } else {
          addAssistantMessage(stepRes.summary || 'Instruction rejected.', 'rejected');
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute instruction');
      addAssistantMessage(`Operation error: ${err.message}`, 'rejected');
    } finally {
      setIsProcessingPrompt(false);
    }
  }, [sessionId, refreshSessionState]);

  const undo = useCallback(async () => {
    if (!canUndo) return;
    await sendPrompt('Undo');
  }, [canUndo, sendPrompt]);

  const redo = useCallback(async () => {
    await sendPrompt('Redo');
  }, [sendPrompt]);

  const triggerRender = useCallback(async () => {
    if (!sessionId) return;
    setIsLoading(true);
    try {
      const job = await api.triggerRender(sessionId);
      setActiveJob({
        job_id: job.job_id,
        status: 'queued',
        progress: 0,
      });
      addAssistantMessage(`Render requested. Processing background render job...`, 'applied');
    } catch (err: any) {
      setError(err.message || 'Render failed to start');
      addAssistantMessage(`Render trigger failed: ${err.message}`, 'rejected');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const exportOTIO = useCallback(async () => {
    if (!sessionId) return null;
    try {
      const res = await api.exportOTIO(sessionId);
      addAssistantMessage(`Timeline successfully exported to OpenTimelineIO: ${res.filename}`, 'applied');
      return res.filename;
    } catch (err: any) {
      setError(err.message || 'OTIO export failed');
      return null;
    }
  }, [sessionId]);

  const seekTo = (seconds: number) => {
    setSeekTime(seconds);
    setCurrentTime(seconds);
  };

  const selectSegment = (segmentId: string | null) => {
    setSelectedSegmentId(segmentId);
  };

  const selectCaption = (captionId: string | null) => {
    setSelectedCaptionId(captionId);
  };

  const clearError = () => setError(null);

  return (
    <EditorContext.Provider
      value={{
        sessionId,
        timeline,
        videoUri,
        activeVideoUrl,
        historyCount,
        canUndo,
        canRedo,
        isLoading,
        isProcessingPrompt,
        activeJob,
        chatMessages,
        currentTime,
        duration,
        isPlaying,
        seekTime,
        selectedSegmentId,
        selectedCaptionId,
        error,
        createSession,
        loadSampleVideo,
        uploadVideo,
        ingestUrl,
        sendPrompt,
        undo,
        redo,
        triggerRender,
        exportOTIO,
        seekTo,
        setCurrentTime,
        setDuration,
        setIsPlaying,
        selectSegment,
        selectCaption,
        clearError,
      }}
    >
      {children}
    </EditorContext.Provider>
  );
};

export const useEditor = () => {
  const context = useContext(EditorContext);
  if (!context) {
    throw new Error('useEditor must be used within an EditorProvider');
  }
  return context;
};

import { useEffect, useRef, useState } from 'react';
import { useStore } from '../store/useStore';
import type { CameraStreamSource, VideoSourceMode, WSStatus } from '../types';

const API_BASE = '/api';
const FILE_POSITION_PREFIX = 'korgen_file_position:';

function canPlayNativeHls(video: HTMLVideoElement) {
  return (
    video.canPlayType('application/vnd.apple.mpegurl') !== '' ||
    video.canPlayType('application/x-mpegURL') !== ''
  );
}

function waitForIceGatheringComplete(pc: RTCPeerConnection) {
  if (pc.iceGatheringState === 'complete') {
    return Promise.resolve();
  }

  return new Promise<void>((resolve) => {
    const onStateChange = () => {
      if (pc.iceGatheringState === 'complete') {
        pc.removeEventListener('icegatheringstatechange', onStateChange);
        resolve();
      }
    };
    pc.addEventListener('icegatheringstatechange', onStateChange);
  });
}

function getFilePositionKey(cameraId: number, url: string) {
  return `${FILE_POSITION_PREFIX}${cameraId}:${url}`;
}

function loadSavedFilePosition(cameraId: number, url: string) {
  try {
    const raw = localStorage.getItem(getFilePositionKey(cameraId, url));
    const parsed = raw ? Number(raw) : 0;
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0;
  } catch {
    return 0;
  }
}

function saveFilePosition(cameraId: number, url: string, currentTime: number) {
  try {
    localStorage.setItem(getFilePositionKey(cameraId, url), String(currentTime));
  } catch {
    // ignore storage errors
  }
}

export function useStream(cameraId: number, enabled: boolean = true) {
  const setStreamStatus = useStore((s) => s.setStreamStatus);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);
  const [status, setStatus] = useState<WSStatus>('disconnected');
  const [source, setSource] = useState<CameraStreamSource | null>(null);

  useEffect(() => {
    let cancelled = false;

    const updateStatus = (next: WSStatus) => {
      if (!cancelled) {
        setStatus(next);
        setStreamStatus(cameraId, next);
      }
    };

    const cleanup = () => {
      if (cleanupRef.current) {
        cleanupRef.current();
        cleanupRef.current = null;
      }
      const video = videoRef.current;
      if (video) {
        video.pause();
        video.removeAttribute('src');
        video.srcObject = null;
        video.load();
      }
    };

    const attachFileLike = (video: HTMLVideoElement, url: string, loop: boolean) =>
      new Promise<() => void>((resolve, reject) => {
        let settled = false;
        let readyTimer: ReturnType<typeof setTimeout> | null = null;
        let saveTimer: ReturnType<typeof setInterval> | null = null;
        let restored = false;
        const savedPosition = loadSavedFilePosition(cameraId, url);

        const finalize = () => {
          if (settled) {
            return;
          }
          settled = true;
          if (readyTimer) {
            clearTimeout(readyTimer);
            readyTimer = null;
          }
          if (!restored && savedPosition > 0 && Number.isFinite(video.duration)) {
            const maxSeek = Math.max(0, video.duration - 0.25);
            video.currentTime = Math.min(savedPosition, maxSeek);
            restored = true;
          }
          saveTimer = setInterval(() => {
            if (!video.paused && !video.ended) {
              saveFilePosition(cameraId, url, video.currentTime);
            }
          }, 1000);
          video.play().catch(() => undefined);
          resolve(() => {
            video.removeEventListener('loadedmetadata', handleReady);
            video.removeEventListener('canplay', handleReady);
            video.removeEventListener('loadeddata', handleReady);
            video.removeEventListener('error', handleError);
            video.removeEventListener('ended', handleEnded);
            if (readyTimer) {
              clearTimeout(readyTimer);
            }
            if (saveTimer) {
              clearInterval(saveTimer);
            }
            saveFilePosition(cameraId, url, video.currentTime);
            video.pause();
            video.removeAttribute('src');
            video.load();
          });
        };

        const handleReady = () => {
          finalize();
        };

        const handleError = () => {
          if (readyTimer) {
            clearTimeout(readyTimer);
            readyTimer = null;
          }
          if (saveTimer) {
            clearInterval(saveTimer);
            saveTimer = null;
          }
          reject(new Error('Video source load failed'));
        };

        const handleEnded = () => {
          saveFilePosition(cameraId, url, 0);
        };

        video.loop = loop;
        video.autoplay = true;
        video.muted = true;
        video.playsInline = true;
        video.preload = 'auto';
        video.addEventListener('loadedmetadata', handleReady, { once: true });
        video.addEventListener('canplay', handleReady, { once: true });
        video.addEventListener('loadeddata', handleReady, { once: true });
        video.addEventListener('error', handleError, { once: true });
        video.addEventListener('ended', handleEnded);
        video.srcObject = null;
        video.src = url;
        video.load();

        readyTimer = setTimeout(() => {
          if (video.readyState >= HTMLMediaElement.HAVE_METADATA) {
            finalize();
          }
        }, 3000);
      });

    const attachWhep = async (video: HTMLVideoElement, whepUrl: string) => {
      const pc = new RTCPeerConnection({ iceServers: [] });
      const stream = new MediaStream();
      let sessionUrl: string | null = null;

      pc.addTransceiver('video', { direction: 'recvonly' });
      pc.ontrack = (event) => {
        for (const track of event.streams[0]?.getTracks?.() ?? []) {
          stream.addTrack(track);
        }
        if (!video.srcObject) {
          video.srcObject = stream;
          video.play().catch(() => undefined);
        }
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      await waitForIceGatheringComplete(pc);

      const response = await fetch(whepUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/sdp' },
        body: pc.localDescription?.sdp ?? '',
      });

      if (!response.ok) {
        pc.close();
        throw new Error(`WHEP failed: ${response.status}`);
      }

      const location = response.headers.get('Location');
      if (location) {
        sessionUrl = new URL(location, whepUrl).toString();
      }

      const answerSdp = await response.text();
      await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp });
      video.autoplay = true;
      video.muted = true;
      video.playsInline = true;

      return async () => {
        try {
          stream.getTracks().forEach((track) => track.stop());
          pc.getSenders().forEach((sender) => sender.track?.stop());
          pc.close();
          if (sessionUrl) {
            await fetch(sessionUrl, { method: 'DELETE' }).catch(() => undefined);
          }
        } finally {
          video.srcObject = null;
        }
      };
    };

    const attachByMode = async (
      video: HTMLVideoElement,
      nextSource: CameraStreamSource,
      mode: VideoSourceMode | null
    ): Promise<(() => void) | null> => {
      if (!mode) {
        return null;
      }
      if (mode === 'file' && nextSource.file_url) {
        return attachFileLike(video, nextSource.file_url, true);
      }
      if (mode === 'hls' && nextSource.hls_url && canPlayNativeHls(video)) {
        return attachFileLike(video, nextSource.hls_url, false);
      }
      if (mode === 'webrtc' && nextSource.whep_url) {
        return attachWhep(video, nextSource.whep_url);
      }
      return null;
    };

    const start = async () => {
      if (!enabled) {
        cleanup();
        updateStatus('disconnected');
        return;
      }

      const video = videoRef.current;
      if (!video) {
        updateStatus('disconnected');
        return;
      }

      updateStatus('connecting');

      try {
        const res = await fetch(`${API_BASE}/stream/source/${cameraId}`);
        if (!res.ok) {
          throw new Error(`stream source failed: ${res.status}`);
        }

        const nextSource: CameraStreamSource = await res.json();
        if (cancelled) {
          return;
        }

        setSource(nextSource);
        cleanup();

        let attached = await attachByMode(video, nextSource, nextSource.mode);
        if (!attached && nextSource.fallback_mode) {
          attached = await attachByMode(video, nextSource, nextSource.fallback_mode);
        }
        if (!attached) {
          throw new Error('No compatible video mode available');
        }

        cleanupRef.current = () => {
          void attached?.();
        };
        updateStatus('connected');
      } catch {
        cleanup();
        updateStatus('disconnected');
      }
    };

    void start();

    return () => {
      cancelled = true;
      cleanup();
      setStreamStatus(cameraId, 'disconnected');
    };
  }, [cameraId, enabled, setStreamStatus]);

  return { status, source, videoRef };
}

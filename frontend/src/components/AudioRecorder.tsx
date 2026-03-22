import { useState, useRef } from 'react';
import ar from '../i18n/ar';

interface Props {
  onRecordingComplete: (blob: Blob) => void;
}

export default function AudioRecorder({ onRecordingComplete }: Props) {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm',
      });
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach(t => t.stop());
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
    } catch {
      alert('Unable to access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleSend = () => {
    if (audioBlob) {
      onRecordingComplete(audioBlob);
      setAudioBlob(null);
      setAudioUrl(null);
    }
  };

  const handleDiscard = () => {
    setAudioBlob(null);
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioUrl(null);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '12px',
      padding: '16px',
      background: 'var(--bg-secondary)',
      borderRadius: '12px',
      border: '1px solid var(--border-color)',
    }}>
      {!audioBlob ? (
        <button
          onClick={isRecording ? stopRecording : startRecording}
          style={{
            background: isRecording ? 'var(--accent-red)' : 'var(--accent-blue)',
            color: '#fff',
            padding: '14px 28px',
            fontSize: '1rem',
            width: '100%',
          }}
        >
          {isRecording ? (
            <span>
              <span style={{
                display: 'inline-block',
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: '#fff',
                marginLeft: '8px',
                animation: 'pulse 1s infinite',
              }} />
              {ar.stopRecording}
            </span>
          ) : ar.startRecording}
        </button>
      ) : (
        <>
          {audioUrl && <audio controls src={audioUrl} style={{ width: '100%' }} />}
          <div style={{ display: 'flex', gap: '8px', width: '100%' }}>
            <button
              onClick={handleSend}
              style={{
                background: 'var(--accent-green)',
                color: '#fff',
                flex: 1,
              }}
            >
              {ar.sendRecording}
            </button>
            <button
              onClick={handleDiscard}
              style={{
                background: 'var(--border-color)',
                color: 'var(--text-secondary)',
                flex: 1,
              }}
            >
              {ar.discardRecording}
            </button>
          </div>
        </>
      )}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
}

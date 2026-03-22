import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubmitStatement, useSubmitAudioStatement } from '../api/hooks';
import { useToast } from '../components/Toast';
import AudioRecorder from '../components/AudioRecorder';
import ar from '../i18n/ar';

export default function SubmitStatement() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const participantId = localStorage.getItem('participantId');
  const [text, setText] = useState('');
  const [mode, setMode] = useState<'text' | 'audio'>('text');
  const [lastResult, setLastResult] = useState<{ text: string; sentiment: string } | null>(null);

  const submitText = useSubmitStatement();
  const submitAudio = useSubmitAudioStatement();

  if (!participantId) {
    navigate('/');
    return null;
  }

  const handleTextSubmit = () => {
    if (!text.trim()) return;
    submitText.mutate({ author_id: participantId, text: text.trim() }, {
      onSuccess: (data) => {
        setLastResult({ text: data.text, sentiment: data.sentiment });
        setText('');
        toast(ar.submitSuccess, 'success');
      },
      onError: () => {
        toast(ar.error, 'error');
      },
    });
  };

  const handleAudioSubmit = (blob: Blob) => {
    submitAudio.mutate({ author_id: participantId, audio: blob }, {
      onSuccess: (data) => {
        setLastResult({ text: data.text, sentiment: data.sentiment });
        toast(ar.submitSuccess, 'success');
      },
      onError: () => {
        toast(ar.error, 'error');
      },
    });
  };

  const charsRemaining = 140 - text.length;
  const isOverLimit = charsRemaining < 0;
  const charColor = isOverLimit ? 'var(--accent-red)' : charsRemaining < 20 ? 'var(--accent-orange)' : 'var(--text-muted)';

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
          {ar.submitTitle}
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          {ar.submitDesc}
        </p>
      </div>

      {/* Mode toggle */}
      <div style={{
        display: 'flex',
        gap: '4px',
        background: 'var(--bg-secondary)',
        borderRadius: '12px',
        padding: '4px',
        border: '1px solid var(--border-color)',
      }}>
        <button
          onClick={() => setMode('text')}
          style={{
            background: mode === 'text' ? 'var(--accent-blue)' : 'transparent',
            color: mode === 'text' ? 'var(--bg-primary)' : 'var(--text-secondary)',
            border: 'none',
            padding: '10px 20px',
            flex: 1,
            borderRadius: '10px',
          }}
        >
          {ar.submitTitle}
        </button>
        <button
          onClick={() => setMode('audio')}
          style={{
            background: mode === 'audio' ? 'var(--accent-blue)' : 'transparent',
            color: mode === 'audio' ? 'var(--bg-primary)' : 'var(--text-secondary)',
            border: 'none',
            padding: '10px 20px',
            flex: 1,
            borderRadius: '10px',
          }}
        >
          {ar.submitAudioButton}
        </button>
      </div>

      {/* Text input mode */}
      {mode === 'text' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ position: 'relative' }}>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={ar.submitTextPlaceholder}
              maxLength={160}
              rows={4}
              style={{
                resize: 'vertical',
                borderColor: isOverLimit ? 'var(--accent-red)' : undefined,
                paddingBottom: '32px',
              }}
            />
            <span style={{
              position: 'absolute',
              bottom: '10px',
              left: '14px',
              fontSize: '0.8rem',
              color: charColor,
              fontWeight: charsRemaining < 20 ? 600 : 400,
              transition: 'color 0.2s ease',
            }}>
              {charsRemaining}
            </span>
          </div>
          <button
            onClick={handleTextSubmit}
            disabled={!text.trim() || isOverLimit || submitText.isPending}
            style={{
              background: 'var(--accent-green)',
              color: '#fff',
              padding: '12px 28px',
              fontSize: '1.05rem',
              fontWeight: 600,
              alignSelf: 'flex-start',
            }}
          >
            {submitText.isPending ? ar.loading : ar.submitButton}
          </button>
        </div>
      )}

      {/* Audio input mode */}
      {mode === 'audio' && (
        <div>
          {submitAudio.isPending ? (
            <div style={{
              textAlign: 'center',
              padding: '32px',
              color: 'var(--text-secondary)',
              background: 'var(--bg-secondary)',
              borderRadius: '12px',
              border: '1px solid var(--border-color)',
            }}>
              <div className="skeleton" style={{ width: '160px', height: '20px', margin: '0 auto 12px' }} />
              {ar.loading}
            </div>
          ) : (
            <AudioRecorder onRecordingComplete={handleAudioSubmit} />
          )}
        </div>
      )}

      {/* Success feedback */}
      {lastResult && (
        <div className="fade-in" style={{
          background: 'var(--bg-card)',
          borderRadius: '14px',
          padding: '18px',
          border: '1px solid var(--accent-green)',
          borderRightWidth: '4px',
        }}>
          <div style={{ color: 'var(--accent-green)', fontWeight: 600, marginBottom: '8px', fontSize: '0.95rem' }}>
            {ar.submitSuccess}
          </div>
          <p style={{ color: 'var(--text-primary)', fontSize: '1.1rem', marginBottom: '8px', lineHeight: 1.7 }}>
            &ldquo;{lastResult.text}&rdquo;
          </p>
          <span style={{
            display: 'inline-block',
            padding: '3px 12px',
            borderRadius: '20px',
            fontSize: '0.8rem',
            fontWeight: 500,
            background: 'var(--bg-secondary)',
            color: 'var(--text-muted)',
            border: '1px solid var(--border-color)',
          }}>
            {ar.sentimentLabel}: {lastResult.sentiment}
          </span>
        </div>
      )}
    </div>
  );
}

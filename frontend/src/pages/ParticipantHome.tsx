import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useStatus, useCreateParticipant } from '../api/hooks';
import { useToast } from '../components/Toast';
import { StatusSkeleton } from '../components/Skeleton';
import ar from '../i18n/ar';

export default function ParticipantHome() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [participantId, setParticipantId] = useState<string | null>(
    localStorage.getItem('participantId')
  );
  const { data: status, isLoading: statusLoading } = useStatus();
  const createParticipant = useCreateParticipant();

  const handleJoin = () => {
    createParticipant.mutate('', {
      onSuccess: (data) => {
        localStorage.setItem('participantId', data.id);
        setParticipantId(data.id);
        toast(ar.joinSuccess, 'success');
      },
      onError: () => {
        toast(ar.error, 'error');
      },
    });
  };

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', paddingTop: '24px' }}>
        <h2 style={{
          fontSize: '1.8rem',
          fontWeight: 700,
          color: 'var(--accent-blue)',
          marginBottom: '8px',
        }}>
          {ar.welcomeTitle}
        </h2>
        <p style={{
          color: 'var(--text-secondary)',
          fontSize: '1.05rem',
          maxWidth: '500px',
          margin: '0 auto',
          lineHeight: 1.8,
        }}>
          {ar.welcomeDesc}
        </p>
      </div>

      {/* Status Cards */}
      {statusLoading ? (
        <StatusSkeleton />
      ) : status ? (
        <div className="stagger-children" style={{
          display: 'flex',
          gap: '12px',
          justifyContent: 'center',
          flexWrap: 'wrap',
        }}>
          {[
            { label: ar.statusParticipants, value: status.participants, color: 'var(--accent-blue)' },
            { label: ar.statusStatements, value: status.statements, color: 'var(--accent-green)' },
            { label: ar.statusVotes, value: status.votes, color: 'var(--accent-orange)' },
            { label: ar.statusCoverage, value: `${status.vote_coverage_pct}%`, color: 'var(--accent-purple)' },
          ].map((item) => (
            <div key={item.label} style={{
              background: 'var(--bg-card)',
              borderRadius: '12px',
              padding: '18px 24px',
              textAlign: 'center',
              border: '1px solid var(--border-color)',
              minWidth: '100px',
              flex: '1 1 100px',
              maxWidth: '160px',
            }}>
              <div style={{
                fontSize: '1.6rem',
                fontWeight: 700,
                color: item.color,
                lineHeight: 1.2,
              }}>
                {item.value}
              </div>
              <div style={{
                fontSize: '0.8rem',
                color: 'var(--text-muted)',
                marginTop: '6px',
              }}>
                {item.label}
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {/* Join or Navigation */}
      {!participantId ? (
        <div style={{ textAlign: 'center' }}>
          <button
            onClick={handleJoin}
            disabled={createParticipant.isPending}
            style={{
              background: 'var(--accent-blue)',
              color: 'var(--bg-primary)',
              padding: '16px 52px',
              fontSize: '1.2rem',
              fontWeight: 600,
              borderRadius: '12px',
            }}
          >
            {createParticipant.isPending ? ar.loading : ar.joinButton}
          </button>
        </div>
      ) : (
        <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
          <div style={{
            background: 'var(--bg-card)',
            borderRadius: '12px',
            padding: '12px 20px',
            border: '1px solid var(--border-color)',
            textAlign: 'center',
          }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{ar.joinedAs}: </span>
            <span style={{
              color: 'var(--accent-blue)',
              fontFamily: 'monospace',
              fontSize: '0.85rem',
              direction: 'ltr',
              unicodeBidi: 'isolate',
            }}>
              {participantId}
            </span>
          </div>

          <div style={{
            display: 'flex',
            gap: '12px',
            flexWrap: 'wrap',
            justifyContent: 'center',
            width: '100%',
            maxWidth: '500px',
          }}>
            <button
              onClick={() => navigate('/submit')}
              style={{
                background: 'var(--accent-green)',
                color: '#fff',
                padding: '14px 28px',
                fontSize: '1.05rem',
                flex: '1 1 140px',
              }}
            >
              {ar.goToSubmit}
            </button>
            <button
              onClick={() => navigate('/vote')}
              style={{
                background: 'var(--accent-blue)',
                color: 'var(--bg-primary)',
                padding: '14px 28px',
                fontSize: '1.05rem',
                flex: '1 1 140px',
              }}
            >
              {ar.goToVote}
            </button>
            <button
              onClick={() => navigate('/progress')}
              style={{
                background: 'var(--accent-purple)',
                color: '#fff',
                padding: '14px 28px',
                fontSize: '1.05rem',
                flex: '1 1 140px',
              }}
            >
              {ar.goToProgress}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

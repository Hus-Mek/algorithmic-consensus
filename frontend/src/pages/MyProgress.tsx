import { useNavigate } from 'react-router-dom';
import { useVoteHistory, useStatements, useStatus } from '../api/hooks';
import { CardSkeleton } from '../components/Skeleton';
import ar from '../i18n/ar';

const voteLabels: Record<number, { text: string; color: string }> = {
  1: { text: ar.agreed, color: 'var(--accent-green)' },
  '-1': { text: ar.disagreed, color: 'var(--accent-red)' },
  0: { text: ar.passed, color: 'var(--text-muted)' },
};

export default function MyProgress() {
  const navigate = useNavigate();
  const participantId = localStorage.getItem('participantId');
  const { data: votes, isLoading: votesLoading, isError, refetch } = useVoteHistory(participantId);
  const { data: statements } = useStatements();
  const { data: status } = useStatus();

  if (!participantId) {
    navigate('/');
    return null;
  }

  const stmtMap = new Map(statements?.map(s => [s.id, s.text]) || []);
  const totalStatements = status?.statements || 0;
  const votedCount = votes?.length || 0;
  const progressPct = totalStatements > 0 ? Math.round((votedCount / totalStatements) * 100) : 0;

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
        {ar.progressTitle}
      </h2>

      {/* Progress bar */}
      <div style={{
        background: 'var(--bg-card)',
        borderRadius: '14px',
        padding: '20px',
        border: '1px solid var(--border-color)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
          <span style={{ color: 'var(--text-secondary)' }}>
            {ar.progressVotedOn} {votedCount} {ar.progressOf} {totalStatements} {ar.progressStatements}
          </span>
          <span style={{ color: 'var(--accent-blue)', fontWeight: 600 }}>{progressPct}%</span>
        </div>
        <div style={{
          height: '8px',
          background: 'var(--bg-secondary)',
          borderRadius: '4px',
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${progressPct}%`,
            background: 'linear-gradient(90deg, var(--accent-blue), var(--accent-purple))',
            borderRadius: '4px',
            transition: 'width 0.5s ease',
            animation: 'progress-fill 0.8s ease-out',
          }} />
        </div>
      </div>

      {/* Error state */}
      {isError && (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <div style={{ color: 'var(--accent-red)', fontSize: '1.1rem', marginBottom: '12px' }}>
            {ar.error}
          </div>
          <button
            onClick={() => refetch()}
            style={{
              background: 'var(--accent-blue)',
              color: 'var(--bg-primary)',
              padding: '10px 24px',
            }}
          >
            {ar.retry}
          </button>
        </div>
      )}

      {/* Loading skeleton */}
      {votesLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {[1, 2, 3, 4].map(i => <CardSkeleton key={i} />)}
        </div>
      )}

      {/* Empty state */}
      {!votesLoading && !isError && votes && votes.length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '48px 20px',
          background: 'var(--bg-card)',
          borderRadius: '14px',
          border: '1px solid var(--border-color)',
        }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            background: 'rgba(79, 195, 247, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            fontSize: '1.5rem',
            color: 'var(--accent-blue)',
          }}>
            ?
          </div>
          <h3 style={{ color: 'var(--text-secondary)', marginBottom: '6px', fontSize: '1.1rem' }}>
            {ar.noVotesYet}
          </h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '16px' }}>
            {ar.noVotesYetDesc}
          </p>
          <button
            onClick={() => navigate('/vote')}
            style={{
              background: 'var(--accent-blue)',
              color: 'var(--bg-primary)',
              padding: '10px 28px',
            }}
          >
            {ar.goToVote}
          </button>
        </div>
      )}

      {/* Vote history */}
      {!votesLoading && votes && votes.length > 0 && (
        <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {votes.map((v) => {
            const voteInfo = voteLabels[v.value] || voteLabels[0];
            return (
              <div key={`${v.statement_id}`} style={{
                background: 'var(--bg-card)',
                borderRadius: '12px',
                padding: '14px 18px',
                border: '1px solid var(--border-color)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: '12px',
              }}>
                <span style={{
                  color: 'var(--text-primary)',
                  fontSize: '1rem',
                  flex: 1,
                  lineHeight: 1.6,
                }}>
                  {stmtMap.get(v.statement_id) || `#${v.statement_id}`}
                </span>
                <span style={{
                  padding: '4px 14px',
                  borderRadius: '20px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  background: v.value === 0 ? 'var(--bg-secondary)' : voteInfo.color,
                  color: v.value === 0 ? 'var(--text-secondary)' : '#fff',
                  whiteSpace: 'nowrap',
                  border: v.value === 0 ? '1px solid var(--border-color)' : 'none',
                }}>
                  {voteInfo.text}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

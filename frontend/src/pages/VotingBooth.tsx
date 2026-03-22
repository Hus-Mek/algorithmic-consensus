import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useNextStatement, useCastVote } from '../api/hooks';
import { useToast } from '../components/Toast';
import { CardSkeleton } from '../components/Skeleton';
import StatementCard from '../components/StatementCard';
import VoteButtons from '../components/VoteButtons';
import ar from '../i18n/ar';

export default function VotingBooth() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const participantId = localStorage.getItem('participantId');
  const { data: statement, isLoading, isError, refetch } = useNextStatement(participantId);
  const castVote = useCastVote();

  if (!participantId) {
    navigate('/');
    return null;
  }

  const handleVote = (value: number) => {
    if (!statement) return;
    castVote.mutate({
      participant_id: participantId,
      statement_id: statement.id,
      value,
    }, {
      onError: () => {
        toast(ar.error, 'error');
      },
    });
  };

  if (isLoading) {
    return (
      <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <div className="skeleton" style={{ width: '200px', height: '28px', marginBottom: '8px' }} />
          <div className="skeleton" style={{ width: '300px', height: '16px' }} />
        </div>
        <CardSkeleton />
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
          <div className="skeleton" style={{ width: '120px', height: '48px', borderRadius: '10px' }} />
          <div className="skeleton" style={{ width: '120px', height: '48px', borderRadius: '10px' }} />
          <div className="skeleton" style={{ width: '120px', height: '48px', borderRadius: '10px' }} />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="fade-in" style={{ textAlign: 'center', padding: '60px 0' }}>
        <div style={{ fontSize: '2.5rem', marginBottom: '16px', opacity: 0.4 }}>!</div>
        <h2 style={{ color: 'var(--accent-red)', fontSize: '1.3rem', marginBottom: '8px' }}>
          {ar.error}
        </h2>
        <button
          onClick={() => refetch()}
          style={{
            background: 'var(--accent-blue)',
            color: 'var(--bg-primary)',
            marginTop: '16px',
            padding: '10px 28px',
          }}
        >
          {ar.retry}
        </button>
      </div>
    );
  }

  if (!statement) {
    return (
      <div className="fade-in" style={{ textAlign: 'center', padding: '60px 0' }}>
        <div style={{
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          background: 'rgba(102, 187, 106, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 20px',
          fontSize: '1.8rem',
          color: 'var(--accent-green)',
        }}>
          &#10003;
        </div>
        <h2 style={{ color: 'var(--accent-green)', fontSize: '1.4rem', marginBottom: '8px' }}>
          {ar.voteComplete}
        </h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>{ar.voteCompleteDesc}</p>
        <button
          onClick={() => navigate('/')}
          style={{
            background: 'var(--accent-blue)',
            color: 'var(--bg-primary)',
            padding: '10px 28px',
          }}
        >
          {ar.back}
        </button>
      </div>
    );
  }

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px' }}>
          {ar.voteTitle}
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          {ar.voteDesc}
        </p>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={statement.id}
          initial={{ opacity: 0, x: 60, scale: 0.97 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: -60, scale: 0.97 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
        >
          <StatementCard text={statement.text} />
          <VoteButtons
            onVote={handleVote}
            disabled={castVote.isPending}
          />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

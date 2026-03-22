import ar from '../i18n/ar';

interface Props {
  onVote: (value: number) => void;
  disabled?: boolean;
}

export default function VoteButtons({ onVote, disabled }: Props) {
  return (
    <div style={{
      display: 'flex',
      gap: '10px',
      justifyContent: 'center',
      marginTop: '20px',
    }}>
      <button
        onClick={() => onVote(1)}
        disabled={disabled}
        style={{
          background: 'var(--accent-green)',
          color: '#fff',
          padding: '16px 24px',
          fontSize: '1.1rem',
          fontWeight: 600,
          flex: 1,
          maxWidth: '180px',
          minHeight: '56px',
          borderRadius: '12px',
        }}
      >
        {ar.voteAgree}
      </button>
      <button
        onClick={() => onVote(0)}
        disabled={disabled}
        style={{
          background: 'var(--bg-secondary)',
          color: 'var(--text-secondary)',
          padding: '16px 24px',
          fontSize: '1.1rem',
          fontWeight: 600,
          flex: 1,
          maxWidth: '180px',
          minHeight: '56px',
          borderRadius: '12px',
          border: '1px solid var(--border-color)',
        }}
      >
        {ar.votePass}
      </button>
      <button
        onClick={() => onVote(-1)}
        disabled={disabled}
        style={{
          background: 'var(--accent-red)',
          color: '#fff',
          padding: '16px 24px',
          fontSize: '1.1rem',
          fontWeight: 600,
          flex: 1,
          maxWidth: '180px',
          minHeight: '56px',
          borderRadius: '12px',
        }}
      >
        {ar.voteDisagree}
      </button>
    </div>
  );
}

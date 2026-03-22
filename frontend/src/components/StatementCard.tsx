interface Props {
  text: string;
  sentiment?: string;
}

const sentimentColors: Record<string, string> = {
  positive: 'var(--accent-green)',
  negative: 'var(--accent-red)',
  neutral: 'var(--accent-orange)',
};

const sentimentLabels: Record<string, string> = {
  positive: 'إيجابي',
  negative: 'سلبي',
  neutral: 'محايد',
};

export default function StatementCard({ text, sentiment }: Props) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: '16px',
      padding: '28px 24px',
      border: '1px solid var(--border-color)',
      boxShadow: 'var(--shadow)',
      borderRightWidth: '3px',
      borderRightColor: 'var(--accent-blue)',
    }}>
      <p style={{
        fontSize: '1.35rem',
        fontWeight: 500,
        lineHeight: 1.9,
        color: 'var(--text-primary)',
        marginBottom: sentiment ? '14px' : 0,
      }}>
        {text}
      </p>
      {sentiment && (
        <span style={{
          display: 'inline-block',
          padding: '4px 14px',
          borderRadius: '20px',
          fontSize: '0.8rem',
          fontWeight: 500,
          color: '#fff',
          background: sentimentColors[sentiment] || 'var(--text-muted)',
        }}>
          {sentimentLabels[sentiment] || sentiment}
        </span>
      )}
    </div>
  );
}

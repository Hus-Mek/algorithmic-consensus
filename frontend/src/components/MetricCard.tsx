interface Props {
  value: number;
  label: string;
  interpretation?: string;
  color?: string;
  suffix?: string;
}

export default function MetricCard({ value, label, interpretation, color, suffix }: Props) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: '14px',
      padding: '20px',
      border: '1px solid var(--border-color)',
      textAlign: 'center',
      flex: '1 1 140px',
      minWidth: '140px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Top accent line */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: '20%',
        right: '20%',
        height: '3px',
        background: color || 'var(--accent-blue)',
        borderRadius: '0 0 3px 3px',
      }} />

      <div style={{
        fontSize: '2.2rem',
        fontWeight: 700,
        color: color || 'var(--accent-blue)',
        lineHeight: 1.2,
        marginTop: '4px',
      }}>
        {typeof value === 'number' ? value.toFixed(value % 1 === 0 ? 0 : 2) : value}
        {suffix && <span style={{ fontSize: '1rem', fontWeight: 400 }}>{suffix}</span>}
      </div>
      <div style={{
        fontSize: '0.9rem',
        color: 'var(--text-secondary)',
        marginTop: '6px',
        fontWeight: 500,
      }}>
        {label}
      </div>
      {interpretation && (
        <div style={{
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          marginTop: '8px',
          lineHeight: 1.4,
        }}>
          {interpretation}
        </div>
      )}
    </div>
  );
}

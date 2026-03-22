import type { ClusterInfo } from '../api/hooks';
import ar from '../i18n/ar';

const COLORS = ['#ef5350', '#4fc3f7', '#66bb6a', '#ffa726', '#ab47bc'];

interface Props {
  clusters: ClusterInfo[];
}

export default function ClusterSummary({ clusters }: Props) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: '12px',
      padding: '20px',
      border: '1px solid var(--border-color)',
    }}>
      <h3 style={{ color: 'var(--text-primary)', marginBottom: '14px', fontSize: '1.1rem' }}>
        {ar.clusterSummary}
      </h3>
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        {clusters.map((c, i) => (
          <div key={c.label} style={{
            background: 'var(--bg-secondary)',
            borderRadius: '10px',
            padding: '14px 18px',
            border: '1px solid var(--border-color)',
            flex: '1 1 120px',
            textAlign: 'center',
          }}>
            <div style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              background: COLORS[i % COLORS.length],
              display: 'inline-block',
              marginLeft: '6px',
              verticalAlign: 'middle',
            }} />
            <span style={{
              color: 'var(--text-primary)',
              fontWeight: 600,
              fontSize: '1rem',
            }}>
              {c.label}
            </span>
            <div style={{
              color: 'var(--text-muted)',
              fontSize: '0.85rem',
              marginTop: '4px',
            }}>
              {c.size} {ar.participants}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

import type { BridgeStatement } from '../api/hooks';
import ar from '../i18n/ar';

interface Props {
  bridges: BridgeStatement[];
  clusterCount: number;
}

export default function BridgeStatementList({ bridges }: Props) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: '12px',
      padding: '20px',
      border: '1px solid var(--border-color)',
    }}>
      <h3 style={{ color: 'var(--text-primary)', marginBottom: '4px', fontSize: '1.1rem' }}>
        {ar.bridgeStatements}
      </h3>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '16px' }}>
        {ar.bridgeDesc}
      </p>

      {bridges.length === 0 ? (
        <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>
          No bridge statements found
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {bridges.map((b, idx) => (
            <div key={b.id} style={{
              background: 'var(--bg-secondary)',
              borderRadius: '10px',
              padding: '16px',
              border: '1px solid var(--border-color)',
            }}>
              {/* Statement text */}
              <p style={{
                fontSize: '1.15rem',
                fontWeight: 500,
                color: 'var(--text-primary)',
                marginBottom: '12px',
                lineHeight: 1.7,
              }}>
                {idx + 1}. "{b.text}"
              </p>

              {/* Bridge score bar */}
              <div style={{ marginBottom: '10px' }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '4px',
                }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {ar.bridgeScore}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--accent-green)', fontWeight: 600 }}>
                    {(b.bridge_score * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={{
                  height: '6px',
                  background: 'var(--bg-primary)',
                  borderRadius: '3px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%',
                    width: `${b.bridge_score * 100}%`,
                    background: 'var(--accent-green)',
                    borderRadius: '3px',
                  }} />
                </div>
              </div>

              {/* Per-cluster agreement */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {Object.entries(b.per_cluster_agreement).map(([clusterId, rate]) => {
                  const label = `Group ${String.fromCharCode(65 + parseInt(clusterId))}`;
                  const pct = (rate * 100).toFixed(0);
                  const isAboveThreshold = rate >= 0.6;
                  return (
                    <span key={clusterId} style={{
                      padding: '3px 10px',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      background: isAboveThreshold ? 'rgba(102,187,106,0.15)' : 'rgba(255,255,255,0.05)',
                      color: isAboveThreshold ? 'var(--accent-green)' : 'var(--text-muted)',
                      border: `1px solid ${isAboveThreshold ? 'rgba(102,187,106,0.3)' : 'var(--border-color)'}`,
                    }}>
                      {label}: {pct}%
                    </span>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

import type { HeatmapData } from '../api/hooks';
import ar from '../i18n/ar';

interface Props {
  data: HeatmapData;
}

export default function FearHeatmap({ data }: Props) {
  if (data.locations.length === 0) {
    return (
      <div style={{
        background: 'var(--bg-card)',
        borderRadius: '12px',
        padding: '40px 20px',
        border: '1px solid var(--border-color)',
        textAlign: 'center',
        color: 'var(--text-muted)',
      }}>
        No geographic fear data available
      </div>
    );
  }

  // Find max value for color scaling
  const maxVal = Math.max(1, ...data.values.flat());

  const getCellColor = (val: number) => {
    if (val === 0) return 'var(--bg-secondary)';
    const intensity = val / maxVal;
    const r = Math.round(239 + (255 - 239) * (1 - intensity));
    const g = Math.round(83 + (152 - 83) * (1 - intensity));
    const b = Math.round(80 + (56 - 80) * (1 - intensity));
    return `rgb(${r}, ${g}, ${b})`;
  };

  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: '12px',
      padding: '20px',
      border: '1px solid var(--border-color)',
    }}>
      <h3 style={{ color: 'var(--text-primary)', marginBottom: '16px', fontSize: '1.1rem' }}>
        {ar.fearHeatmap}
      </h3>
      <div style={{ overflowX: 'auto' }}>
        <table style={{
          borderCollapse: 'collapse',
          width: '100%',
          minWidth: '300px',
        }}>
          <thead>
            <tr>
              <th style={{
                padding: '10px',
                color: 'var(--text-muted)',
                fontSize: '0.85rem',
                textAlign: 'start',
              }} />
              {data.cluster_labels.map(label => (
                <th key={label} style={{
                  padding: '10px',
                  color: 'var(--text-secondary)',
                  fontSize: '0.85rem',
                  textAlign: 'center',
                  fontWeight: 500,
                }}>
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.locations.map((loc, i) => (
              <tr key={loc}>
                <td style={{
                  padding: '10px 14px',
                  color: 'var(--text-primary)',
                  fontSize: '0.95rem',
                  fontWeight: 500,
                  whiteSpace: 'nowrap',
                }}>
                  {loc}
                </td>
                {data.values[i].map((val, j) => (
                  <td key={j} style={{
                    padding: '10px',
                    textAlign: 'center',
                    background: getCellColor(val),
                    color: val > maxVal * 0.5 ? '#fff' : 'var(--text-primary)',
                    fontWeight: 600,
                    fontSize: '1.1rem',
                    borderRadius: '4px',
                  }}>
                    {val}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

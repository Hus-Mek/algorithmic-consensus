import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { ClusterVisualization } from '../api/hooks';
import ar from '../i18n/ar';

const COLORS = ['#ef5350', '#4fc3f7', '#66bb6a', '#ffa726', '#ab47bc'];

interface Props {
  data: ClusterVisualization;
}

export default function ClusterScatter({ data }: Props) {
  // Group participants by cluster
  const clusterGroups = new Map<string, { label: string; points: { x: number; y: number; id: string }[] }>();

  for (const p of data.participants) {
    if (!clusterGroups.has(p.cluster_label)) {
      clusterGroups.set(p.cluster_label, { label: p.cluster_label, points: [] });
    }
    clusterGroups.get(p.cluster_label)!.points.push({ x: p.x, y: p.y, id: p.id });
  }

  const groups = Array.from(clusterGroups.values());

  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: '12px',
      padding: '20px',
      border: '1px solid var(--border-color)',
    }}>
      <h3 style={{ color: 'var(--text-primary)', marginBottom: '16px', fontSize: '1.1rem' }}>
        {ar.clusterChart}
      </h3>
      <ResponsiveContainer width="100%" height={350}>
        <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis
            type="number"
            dataKey="x"
            name="PC1"
            tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
            stroke="var(--border-color)"
          />
          <YAxis
            type="number"
            dataKey="y"
            name="PC2"
            tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
            stroke="var(--border-color)"
          />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            contentStyle={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
              direction: 'rtl',
            }}
          />
          <Legend
            wrapperStyle={{ direction: 'rtl', paddingTop: '10px' }}
          />
          {groups.map((group, i) => (
            <Scatter
              key={group.label}
              name={group.label}
              data={group.points}
              fill={COLORS[i % COLORS.length]}
              opacity={0.8}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Reusable skeleton loading placeholder with shimmer animation. */

interface Props {
  width?: string;
  height?: string;
  borderRadius?: string;
  style?: React.CSSProperties;
}

export default function Skeleton({
  width = '100%',
  height = '20px',
  borderRadius = '8px',
  style,
}: Props) {
  return (
    <div
      className="skeleton"
      style={{ width, height, borderRadius, ...style }}
    />
  );
}

/** Card-shaped skeleton for statement/vote items. */
export function CardSkeleton() {
  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: '14px',
      padding: '24px',
      border: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
    }}>
      <Skeleton height="18px" width="80%" />
      <Skeleton height="18px" width="60%" />
      <Skeleton height="14px" width="30%" />
    </div>
  );
}

/** Metric card skeleton for dashboard. */
export function MetricSkeleton() {
  return (
    <div style={{
      background: 'var(--bg-card)',
      borderRadius: '14px',
      padding: '20px',
      border: '1px solid var(--border-color)',
      textAlign: 'center',
      flex: '1 1 140px',
      minWidth: '140px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '8px',
    }}>
      <Skeleton width="60px" height="36px" borderRadius="6px" />
      <Skeleton width="80px" height="14px" />
    </div>
  );
}

/** Status card skeleton for home page. */
export function StatusSkeleton() {
  return (
    <div style={{
      display: 'flex',
      gap: '12px',
      justifyContent: 'center',
      flexWrap: 'wrap',
    }}>
      {[1, 2, 3, 4].map(i => (
        <div key={i} style={{
          background: 'var(--bg-card)',
          borderRadius: '10px',
          padding: '16px 24px',
          textAlign: 'center',
          border: '1px solid var(--border-color)',
          minWidth: '100px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '8px',
        }}>
          <Skeleton width="40px" height="28px" />
          <Skeleton width="60px" height="12px" />
        </div>
      ))}
    </div>
  );
}

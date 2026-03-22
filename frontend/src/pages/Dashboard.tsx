import { useLatestAnalysis, useRunAnalysis, useClusterData, useHeatmapData } from '../api/hooks';
import { useToast } from '../components/Toast';
import { MetricSkeleton, CardSkeleton } from '../components/Skeleton';
import MetricCard from '../components/MetricCard';
import ClusterScatter from '../components/ClusterScatter';
import FearHeatmap from '../components/FearHeatmap';
import BridgeStatementList from '../components/BridgeStatementList';
import ClusterSummary from '../components/ClusterSummary';
import ar from '../i18n/ar';

function getUnityInterpretation(score: number): string {
  if (score < 0.10) return ar.unityDeep;
  if (score < 0.25) return ar.unitySome;
  if (score < 0.50) return ar.unityStrong;
  return ar.unityHigh;
}

export default function Dashboard() {
  const { toast } = useToast();
  const { data: analysis, isLoading, isError } = useLatestAnalysis();
  const runAnalysis = useRunAnalysis();
  const { data: clusterData } = useClusterData();
  const { data: heatmapData } = useHeatmapData();

  const handleRunAnalysis = () => {
    runAnalysis.mutate(undefined, {
      onSuccess: () => toast(ar.analysisSuccess, 'success'),
      onError: () => toast(ar.analysisError, 'error'),
    });
  };

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px',
      }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          {ar.dashboardTitle}
        </h2>
        <button
          onClick={handleRunAnalysis}
          disabled={runAnalysis.isPending}
          style={{
            background: 'var(--accent-blue)',
            color: 'var(--bg-primary)',
            padding: '10px 24px',
            fontSize: '0.95rem',
          }}
        >
          {runAnalysis.isPending ? ar.analysisRunning : ar.runAnalysis}
        </button>
      </div>

      {/* No data state */}
      {isError && !runAnalysis.data && (
        <div style={{
          textAlign: 'center',
          padding: '60px 20px',
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
            color: 'var(--text-muted)',
          }}>
            &#9776;
          </div>
          <h3 style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>
            {ar.noAnalysis}
          </h3>
          <p style={{ color: 'var(--text-muted)' }}>{ar.noAnalysisDesc}</p>
        </div>
      )}

      {/* Loading skeleton */}
      {isLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {[1, 2, 3, 4].map(i => <MetricSkeleton key={i} />)}
          </div>
          <CardSkeleton />
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 380px' }}><CardSkeleton /></div>
            <div style={{ flex: '1 1 280px' }}><CardSkeleton /></div>
          </div>
        </div>
      )}

      {/* Results display */}
      {(analysis || runAnalysis.data) && (() => {
        const data = runAnalysis.data || analysis!;
        return (
          <>
            {/* Metric cards row */}
            <div className="stagger-children" style={{
              display: 'flex',
              gap: '12px',
              flexWrap: 'wrap',
            }}>
              <MetricCard
                value={data.metrics.unity_score}
                label={ar.unityScore}
                interpretation={getUnityInterpretation(data.metrics.unity_score)}
                color="var(--accent-green)"
              />
              <MetricCard
                value={data.metrics.consensus_index}
                label={ar.consensusIndex}
                color="var(--accent-blue)"
              />
              <MetricCard
                value={data.metrics.cluster_count}
                label={ar.clusterCount}
                color="var(--accent-orange)"
              />
              <MetricCard
                value={data.meta.vote_coverage_pct}
                label={ar.voteCoverage}
                suffix="%"
                color="var(--accent-purple)"
              />
            </div>

            {/* Cluster summary */}
            <ClusterSummary clusters={data.clusters} />

            {/* Charts row - stacks on mobile */}
            <div style={{
              display: 'flex',
              gap: '16px',
              flexWrap: 'wrap',
            }}>
              <div style={{ flex: '1 1 380px', minWidth: 0 }}>
                {clusterData ? (
                  <ClusterScatter data={clusterData} />
                ) : (
                  <div style={{
                    background: 'var(--bg-card)',
                    borderRadius: '14px',
                    padding: '40px',
                    border: '1px solid var(--border-color)',
                  }}>
                    <div className="skeleton" style={{ width: '100%', height: '200px', borderRadius: '8px' }} />
                  </div>
                )}
              </div>
              <div style={{ flex: '1 1 280px', minWidth: 0 }}>
                {heatmapData ? (
                  <FearHeatmap data={heatmapData} />
                ) : (
                  <div style={{
                    background: 'var(--bg-card)',
                    borderRadius: '14px',
                    padding: '40px',
                    border: '1px solid var(--border-color)',
                  }}>
                    <div className="skeleton" style={{ width: '100%', height: '200px', borderRadius: '8px' }} />
                  </div>
                )}
              </div>
            </div>

            {/* Bridge statements */}
            <BridgeStatementList
              bridges={data.bridge_statements}
              clusterCount={data.metrics.cluster_count}
            />

            {/* Meta info */}
            <div style={{
              fontSize: '0.78rem',
              color: 'var(--text-muted)',
              textAlign: 'center',
              padding: '10px',
              borderTop: '1px solid var(--border-color)',
              marginTop: '8px',
            }}>
              {data.meta.system} | {data.meta.generated_at}
            </div>
          </>
        );
      })()}
    </div>
  );
}

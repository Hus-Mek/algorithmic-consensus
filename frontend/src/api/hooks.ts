import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from './client';

// --- Types ---

export interface Statement {
  id: number;
  text: string;
  sentiment: string;
  sentiment_score: number;
  created_at: string;
}

export interface VoteRecord {
  participant_id: string;
  statement_id: number;
  value: number;
  created_at: string;
}

export interface Status {
  participants: number;
  statements: number;
  votes: number;
  vote_coverage_pct: number;
}

export interface ClusterInfo {
  label: string;
  size: number;
  centroid: number[] | null;
}

export interface BridgeStatement {
  id: number;
  text: string;
  bridge_score: number;
  clusters_agreeing: number;
  per_cluster_agreement: Record<string, number>;
}

export interface AnalysisMetrics {
  unity_score: number;
  consensus_index: number;
  pca_explained_variance: number;
  silhouette_score: number;
  cluster_count: number;
}

export interface FullAnalysis {
  meta: {
    generated_at: string;
    system: string;
    total_participants: number;
    total_statements: number;
    vote_coverage_pct: number;
  };
  metrics: AnalysisMetrics;
  clusters: ClusterInfo[];
  bridge_statements: BridgeStatement[];
}

export interface ClusterParticipant {
  id: string;
  x: number;
  y: number;
  cluster_id: number;
  cluster_label: string;
}

export interface ClusterVisualization {
  participants: ClusterParticipant[];
  centroids: { label: string; x: number; y: number }[];
}

export interface HeatmapData {
  locations: string[];
  cluster_labels: string[];
  values: number[][];
}

// --- Hooks ---

export function useStatus() {
  return useQuery<Status>({
    queryKey: ['status'],
    queryFn: () => api.get('/api/status').then(r => r.data),
    refetchInterval: 8000,
  });
}

export function useStatements() {
  return useQuery<Statement[]>({
    queryKey: ['statements'],
    queryFn: () => api.get('/api/statements').then(r => r.data),
    refetchInterval: 15000,
  });
}

export function useNextStatement(participantId: string | null) {
  return useQuery<Statement | null>({
    queryKey: ['next-statement', participantId],
    queryFn: () => api.get(`/api/votes/next/${participantId}`).then(r => r.data),
    enabled: !!participantId,
  });
}

export function useVoteHistory(participantId: string | null) {
  return useQuery<VoteRecord[]>({
    queryKey: ['vote-history', participantId],
    queryFn: () => api.get(`/api/votes/history/${participantId}`).then(r => r.data),
    enabled: !!participantId,
    refetchInterval: 20000,
  });
}

export function useCreateParticipant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (location: string = '') =>
      api.post('/api/participants', { location }).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['status'] });
    },
  });
}

export function useSubmitStatement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { author_id: string; text: string }) =>
      api.post('/api/statements', data).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['statements'] });
      qc.invalidateQueries({ queryKey: ['status'] });
      qc.invalidateQueries({ queryKey: ['next-statement'] });
    },
  });
}

export function useSubmitAudioStatement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { author_id: string; audio: Blob }) => {
      const formData = new FormData();
      formData.append('author_id', data.author_id);
      formData.append('audio', data.audio, 'recording.webm');
      return api.post('/api/statements/audio', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(r => r.data);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['statements'] });
      qc.invalidateQueries({ queryKey: ['status'] });
      qc.invalidateQueries({ queryKey: ['next-statement'] });
    },
  });
}

export function useCastVote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { participant_id: string; statement_id: number; value: number }) =>
      api.post('/api/votes', data).then(r => r.data),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ['next-statement', variables.participant_id] });
      qc.invalidateQueries({ queryKey: ['vote-history', variables.participant_id] });
      qc.invalidateQueries({ queryKey: ['status'] });
    },
  });
}

export function useLatestAnalysis() {
  return useQuery<FullAnalysis>({
    queryKey: ['analysis'],
    queryFn: () => api.get('/api/analysis/latest').then(r => r.data),
    retry: false,
  });
}

export function useRunAnalysis() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post('/api/analysis').then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['analysis'] });
      qc.invalidateQueries({ queryKey: ['cluster-data'] });
      qc.invalidateQueries({ queryKey: ['heatmap-data'] });
    },
  });
}

export function useClusterData() {
  return useQuery<ClusterVisualization>({
    queryKey: ['cluster-data'],
    queryFn: () => api.get('/api/analysis/clusters').then(r => r.data),
    retry: false,
  });
}

export function useHeatmapData() {
  return useQuery<HeatmapData>({
    queryKey: ['heatmap-data'],
    queryFn: () => api.get('/api/analysis/heatmap').then(r => r.data),
    retry: false,
  });
}

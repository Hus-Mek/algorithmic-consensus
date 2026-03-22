"""
deliberation.py - Pillar 2: Processing Layer (Polis-style Deliberation Engine)

This is the algorithmic core. It takes the vote matrix (participants × statements)
and finds:
    1. Opinion clusters (groups of people who vote similarly)
    2. Bridge statements (ideas that unite opposing clusters)

Algorithm pipeline:
    Vote Matrix → Impute Missing → PCA to 2D → K-Means Clustering → Bridge Detection

ANTI-HALLUCINATION: This entire module operates on integers (vote values: -1, 0, 1)
and numpy arrays. No language model is called. No text is generated. The clustering
is unsupervised ML on numerical data. Bridge detection is pure arithmetic.

References:
    - Polis: https://compdemocracy.org/Polis/
    - vTaiwan: https://info.vtaiwan.tw/
"""

import os
import sqlite3

import numpy as np

# Suppress KMeans MKL memory leak warning on Windows
os.environ.setdefault("OMP_NUM_THREADS", "1")

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

import config
import models


class DeliberationEngine:
    """
    Runs the full Polis-style analysis pipeline on the vote database.

    Usage:
        conn = models.init_db()
        engine = DeliberationEngine(conn)
        result = engine.run_full_analysis()
        # result contains clusters, bridge statements, and metadata
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def build_vote_matrix(self) -> tuple:
        """
        Step 1: Extract the vote matrix from the database.

        Returns:
            matrix: np.ndarray shape (P, S) where P=participants, S=statements
                    Values: 1 (agree), -1 (disagree), 0 (pass), NaN (unvoted)
            participant_ids: list of str (row order)
            statement_ids: list of int (column order)

        Only statements with >= MIN_VOTES_PER_STATEMENT votes are included.
        This prevents statements with 1-2 votes from distorting the analysis.
        """
        matrix, pids, sids = models.get_vote_matrix(self.conn)
        return matrix, pids, sids

    def impute_missing_votes(self, matrix: np.ndarray) -> np.ndarray:
        """
        Step 2: Handle NaN (unvoted) entries in the vote matrix.

        Method: Column-mean imputation (same approach as Polis).

        For each statement (column), replace NaN values with the mean of
        all actual votes on that statement. This assumes that a participant
        who didn't vote on a statement would have voted similarly to the
        average of all voters on that statement.

        Why not zero? Zero means "pass" (an explicit choice). NaN means
        "never saw it" (no choice made). Treating them the same would
        conflate active neutrality with non-participation.

        Warning: If a column is >80% NaN, the imputed values are unreliable.
        The run_full_analysis method reports vote coverage percentage.
        """
        imputed = matrix.copy()
        for col in range(imputed.shape[1]):
            col_data = imputed[:, col]
            mask = ~np.isnan(col_data)
            if mask.any():
                col_mean = col_data[mask].mean()
                imputed[~mask, col] = col_mean
            else:
                # Entire column is NaN -- no votes at all (shouldn't happen
                # because we filter by MIN_VOTES_PER_STATEMENT, but defensive)
                imputed[:, col] = 0.0
        return imputed

    def reduce_dimensions(self, matrix: np.ndarray) -> tuple:
        """
        Step 3: PCA projection from S dimensions to 2D.

        PCA (Principal Component Analysis) finds the two axes along which
        participants' voting patterns vary the most.

        Intuition: If there are 10 statements, each participant is a point
        in 10-dimensional space. PCA finds the "best angle" to project this
        10D cloud down to 2D, preserving as much of the spread as possible.

        After PCA, participants who vote similarly cluster together in 2D.
        Participants with opposite voting patterns appear far apart.

        Returns:
            projections: np.ndarray shape (P, 2) -- 2D coordinates per participant
            pca: fitted PCA object (contains explained_variance_ratio_)
        """
        n_components = min(config.PCA_COMPONENTS, matrix.shape[1], matrix.shape[0])
        pca = PCA(n_components=n_components)
        projections = pca.fit_transform(matrix)
        return projections, pca

    def find_clusters(self, projections: np.ndarray) -> tuple:
        """
        Step 4: K-Means clustering with automatic k selection.

        Tries k = 2, 3, 4, 5 and picks the k with the best silhouette score.

        Silhouette score measures how well-separated the clusters are:
            +1.0 = perfect separation (clusters are tight and far apart)
             0.0 = clusters overlap (no clear grouping)
            -1.0 = wrong assignment (points closer to other cluster)

        K-Means itself works by:
            1. Place k random cluster centers (centroids) in 2D space
            2. Assign each participant to the nearest centroid
            3. Move each centroid to the mean of its assigned participants
            4. Repeat steps 2-3 until centroids stop moving

        Returns:
            labels: np.ndarray shape (P,) -- cluster ID (0, 1, 2, ...) per participant
            best_k: int -- optimal number of clusters
            best_score: float -- silhouette score for the chosen k
            centroids: np.ndarray shape (k, 2) -- cluster center coordinates
        """
        n_samples = projections.shape[0]

        # Need at least MIN_CLUSTERS + 1 samples to cluster
        if n_samples < config.MIN_CLUSTERS + 1:
            # Too few participants: assign everyone to one cluster
            return np.zeros(n_samples, dtype=int), 1, 0.0, projections.mean(axis=0, keepdims=True)

        max_k = min(config.MAX_CLUSTERS, n_samples - 1)
        min_k = config.MIN_CLUSTERS

        if max_k < min_k:
            return np.zeros(n_samples, dtype=int), 1, 0.0, projections.mean(axis=0, keepdims=True)

        best_k = min_k
        best_score = -1.0
        best_labels = None
        best_centroids = None

        for k in range(min_k, max_k + 1):
            km = KMeans(n_clusters=k, n_init=10, random_state=42)
            labels = km.fit_predict(projections)

            # Silhouette requires at least 2 distinct labels
            unique_labels = len(set(labels))
            if unique_labels < 2:
                continue

            score = silhouette_score(projections, labels)
            if score > best_score:
                best_k = k
                best_score = score
                best_labels = labels
                best_centroids = km.cluster_centers_

        if best_labels is None:
            return np.zeros(n_samples, dtype=int), 1, 0.0, projections.mean(axis=0, keepdims=True)

        return best_labels, best_k, best_score, best_centroids

    def detect_bridge_statements(
        self,
        matrix: np.ndarray,
        labels: np.ndarray,
        statement_ids: list,
    ) -> list:
        """
        Step 5: Find bridge statements -- ideas that unite opposing clusters.

        For each statement:
            1. Compute agreement rate in each cluster
               agreement_rate = (# agree votes) / (# total non-NaN votes in cluster)
            2. Count how many clusters have agreement >= BRIDGE_THRESHOLD (60%)
            3. If >= 2 clusters agree, it's a bridge statement

        Bridge statements are the core output of Polis-style deliberation.
        They represent the common ground that transcends group divisions.

        Example:
            "نحتاج مدارس أفضل لأطفالنا" (We need better schools)
            Cluster A: 78% agree  ✓ (above 60%)
            Cluster B: 65% agree  ✓ (above 60%)
            Cluster C: 82% agree  ✓ (above 60%)
            → BRIDGE STATEMENT, score = mean(0.78, 0.65, 0.82) = 0.75

            "يجب تغيير النظام بالكامل" (The entire system must change)
            Cluster A: 90% agree  ✓
            Cluster B: 12% agree  ✗
            Cluster C: 45% agree  ✗
            → NOT a bridge (only 1 cluster above threshold)
            → This is a DIVISIVE statement

        Returns:
            List of dicts, sorted by bridge_score descending:
            [{
                "statement_id": int,
                "bridge_score": float,
                "clusters_agreeing": int,
                "per_cluster_agreement": {cluster_id: rate, ...},
            }, ...]
        """
        n_clusters = len(set(labels))
        bridges = []

        for j, sid in enumerate(statement_ids):
            per_cluster = {}
            agreeing_clusters = 0

            for c in range(n_clusters):
                # Get votes from participants in this cluster
                cluster_mask = labels == c
                cluster_votes = matrix[cluster_mask, j]

                # Remove NaN (unvoted)
                actual_votes = cluster_votes[~np.isnan(cluster_votes)]

                if len(actual_votes) == 0:
                    per_cluster[c] = 0.0
                    continue

                # Agreement rate: fraction that voted "agree" (value == 1)
                agree_count = np.sum(actual_votes == 1)
                rate = agree_count / len(actual_votes)
                per_cluster[c] = round(rate, 3)

                if rate >= config.BRIDGE_THRESHOLD:
                    agreeing_clusters += 1

            if agreeing_clusters >= 2:
                # This is a bridge statement
                agreeing_rates = [
                    r for r in per_cluster.values()
                    if r >= config.BRIDGE_THRESHOLD
                ]
                bridge_score = np.mean(agreeing_rates)
                bridges.append({
                    "statement_id": sid,
                    "bridge_score": round(float(bridge_score), 3),
                    "clusters_agreeing": agreeing_clusters,
                    "per_cluster_agreement": per_cluster,
                })

        # Sort by bridge score descending (strongest bridges first)
        bridges.sort(key=lambda x: x["bridge_score"], reverse=True)
        return bridges

    def run_full_analysis(self) -> dict:
        """
        Execute the complete analysis pipeline: Steps 1-5.

        Returns a structured dict with everything needed for Pillar 3 (consensus.py):
        - clusters: list of ClusterInfo
        - bridge_statements: list of bridge dicts
        - metadata: vote matrix stats, PCA explained variance, silhouette score
        - vote_matrix: the raw matrix (for consensus.py to use)
        - labels: cluster labels per participant
        - participant_ids, statement_ids: index mappings

        Raises ValueError if insufficient data for analysis.
        """
        # Step 1: Build vote matrix
        matrix, pids, sids = self.build_vote_matrix()

        if matrix.size == 0:
            raise ValueError(
                "No vote data available. Need at least "
                f"{config.MIN_VOTES_PER_STATEMENT} votes per statement."
            )

        n_participants, n_statements = matrix.shape

        # Check minimum participant threshold
        if n_participants < config.MIN_PARTICIPANTS_FOR_ANALYSIS:
            print(
                f"Warning: Only {n_participants} participants "
                f"(recommended minimum: {config.MIN_PARTICIPANTS_FOR_ANALYSIS}). "
                "Clustering results may be unreliable."
            )

        # Vote coverage: what % of possible votes were actually cast?
        total_cells = n_participants * n_statements
        voted_cells = np.sum(~np.isnan(matrix))
        coverage = voted_cells / total_cells * 100

        if coverage < 30:
            print(
                f"Warning: Vote coverage is only {coverage:.1f}%. "
                "Column-mean imputation may be unreliable below 30%."
            )

        # Step 2: Impute missing votes
        imputed = self.impute_missing_votes(matrix)

        # Step 3: PCA to 2D
        projections, pca = self.reduce_dimensions(imputed)
        explained_var = sum(pca.explained_variance_ratio_)

        # Step 4: Cluster participants
        labels, best_k, silhouette, centroids = self.find_clusters(projections)

        # Build cluster info
        clusters = []
        for c in range(best_k):
            member_mask = labels == c
            member_ids = [pids[i] for i in range(len(pids)) if member_mask[i]]
            label_char = chr(65 + c)  # A, B, C, D, E
            clusters.append(models.ClusterInfo(
                id=c,
                label=f"Group {label_char}",
                member_ids=member_ids,
                centroid=centroids[c].tolist() if centroids is not None else None,
            ))

        # Step 5: Detect bridge statements
        bridges = self.detect_bridge_statements(matrix, labels, sids)

        return {
            "clusters": clusters,
            "bridge_statements": bridges,
            "metadata": {
                "n_participants": n_participants,
                "n_statements": n_statements,
                "vote_coverage_pct": round(coverage, 1),
                "pca_explained_variance": round(explained_var, 3),
                "silhouette_score": round(silhouette, 3),
                "cluster_count": best_k,
            },
            # Pass-through data for consensus.py
            "vote_matrix": matrix,
            "imputed_matrix": imputed,
            "labels": labels,
            "projections": projections,
            "participant_ids": pids,
            "statement_ids": sids,
        }

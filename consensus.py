"""
consensus.py - Pillar 3: Output Layer

Takes the deliberation analysis results and produces actionable outputs:
    1. Unity Score: ratio of bridge statements to total (0.0 to 1.0)
    2. Consensus Index: weighted cross-cluster agreement metric
    3. Fear Heatmap: geographic concern distribution (PNG visualization)
    4. Report: structured JSON + human-readable markdown

These outputs translate community opinions into numbers that policymakers
can act on. Instead of "people seem to want schools," the report says
"87% cross-cluster agreement on education as priority" with statistical
backing.

ANTI-HALLUCINATION: All text in the report comes directly from human
statements stored in the database. Metrics are pure arithmetic.
No generative AI produces any report content.
"""

import json
import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

import config
import models


class ConsensusAnalyzer:
    """
    Computes consensus metrics and generates reports from deliberation results.

    Usage:
        engine = DeliberationEngine(conn)
        delib_result = engine.run_full_analysis()
        analyzer = ConsensusAnalyzer(conn, delib_result)
        report = analyzer.generate_report()
    """

    def __init__(self, conn: sqlite3.Connection, deliberation_result: dict):
        self.conn = conn
        self.result = deliberation_result

    def compute_unity_score(self) -> float:
        """
        Unity Score = number of bridge statements / total statements

        Range: 0.0 (total polarization) to 1.0 (full consensus)

        Interpretation:
            < 0.10  Deep polarization. Clusters have almost no common ground.
            0.10-0.25  Some bridges exist. Deliberation is finding common ground.
            0.25-0.50  Strong consensus emerging. Good basis for policy.
            > 0.50  Possible red flag: may indicate insufficient diversity
                    in participants (everyone agrees on everything = echo chamber).

        This metric answers: "What fraction of all ideas are shared across groups?"
        """
        total = self.result["metadata"]["n_statements"]
        bridges = len(self.result["bridge_statements"])
        if total == 0:
            return 0.0
        return round(bridges / total, 3)

    def compute_consensus_index(self) -> float:
        """
        Consensus Index = weighted average of bridge scores.

        Weight = how many clusters each bridge statement spans.
        A statement bridging ALL clusters matters more than one bridging just 2.

        Formula:
            For each bridge b:
                weight_b = clusters_agreeing_b / total_clusters
                score_b = bridge_score_b
            consensus_index = sum(weight_b * score_b) / sum(weight_b)

        Range: 0.0 (no consensus) to 1.0 (strong cross-cluster agreement)

        This metric answers: "How STRONG is the agreement on shared ideas?"
        Unity Score tells you how MANY bridges exist; Consensus Index tells
        you how SOLID those bridges are.
        """
        bridges = self.result["bridge_statements"]
        total_clusters = self.result["metadata"]["cluster_count"]

        if not bridges or total_clusters == 0:
            return 0.0

        weighted_sum = 0.0
        weight_sum = 0.0

        for b in bridges:
            weight = b["clusters_agreeing"] / total_clusters
            weighted_sum += weight * b["bridge_score"]
            weight_sum += weight

        if weight_sum == 0:
            return 0.0
        return round(weighted_sum / weight_sum, 3)

    def generate_fear_heatmap(self, output_path: str = None) -> str:
        """
        Generate a geographic concern heatmap.

        Maps negative-sentiment statements by location and cluster,
        revealing which regions share which fears/concerns.

        The heatmap shows:
            X-axis: Opinion clusters (Group A, Group B, ...)
            Y-axis: Locations (Damascus, Aleppo, Idlib, ...)
            Color intensity: Count of negative-sentiment statements

        A policymaker can look at this and see:
        "Idlib and Aleppo both have high fear around security
         (concentrated in Cluster B), while Damascus fears are
         more economic (Cluster A)."

        Returns path to saved PNG file.
        """
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend (no GUI window)
        import matplotlib.pyplot as plt
        import seaborn as sns

        if output_path is None:
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            output_path = str(config.OUTPUT_DIR / "fear_heatmap.png")

        # Get participant locations
        locations = models.get_participant_locations(self.conn)

        # Map participant IDs to cluster labels
        pids = self.result["participant_ids"]
        labels = self.result["labels"]
        clusters = self.result["clusters"]
        pid_to_cluster = {}
        for i, pid in enumerate(pids):
            cluster_id = int(labels[i])
            pid_to_cluster[pid] = clusters[cluster_id].label

        # Get negative-sentiment statements grouped by author
        statements = models.get_all_statements(self.conn)
        negative_stmts = [s for s in statements if s.sentiment == config.FEAR_SENTIMENT_LABEL]

        # Build count matrix: location × cluster → count
        counts = defaultdict(lambda: defaultdict(int))
        for stmt in negative_stmts:
            author_loc = locations.get(stmt.author_id, "")
            author_cluster = pid_to_cluster.get(stmt.author_id, "")
            if author_loc and author_cluster:
                counts[author_loc][author_cluster] += 1

        if not counts:
            # No negative statements with location data
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.text(0.5, 0.5, "No geographic fear data available",
                    ha="center", va="center", fontsize=14)
            ax.set_axis_off()
            plt.savefig(output_path, dpi=150, bbox_inches="tight")
            plt.close()
            return output_path

        # Convert to matrix for seaborn
        all_locations = sorted(counts.keys())
        all_cluster_labels = sorted({c.label for c in clusters})

        heat_data = []
        for loc in all_locations:
            row = [counts[loc].get(cl, 0) for cl in all_cluster_labels]
            heat_data.append(row)

        heat_array = np.array(heat_data)

        # Plot
        fig, ax = plt.subplots(figsize=(max(8, len(all_cluster_labels) * 2), max(4, len(all_locations) * 1.2)))
        sns.heatmap(
            heat_array,
            annot=True,
            fmt="d",
            cmap="YlOrRd",
            xticklabels=all_cluster_labels,
            yticklabels=all_locations,
            ax=ax,
        )
        ax.set_title("Geographic Fear/Concern Distribution", fontsize=14, pad=15)
        ax.set_xlabel("Opinion Cluster", fontsize=11)
        ax.set_ylabel("Location", fontsize=11)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path

    def generate_cluster_visualization(self, output_path: str = None) -> str:
        """
        Generate a 2D scatter plot showing participant clusters in PCA space.

        Each dot is a participant, colored by cluster. This visualization
        helps understand how distinct the opinion groups are. Well-separated
        clusters mean clear opinion divides; overlapping clusters mean
        the groups are less distinct.

        Returns path to saved PNG file.
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        if output_path is None:
            os.makedirs(config.OUTPUT_DIR, exist_ok=True)
            output_path = str(config.OUTPUT_DIR / "clusters.png")

        projections = self.result["projections"]
        labels = self.result["labels"]
        clusters = self.result["clusters"]

        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]

        for c in range(len(clusters)):
            mask = labels == c
            ax.scatter(
                projections[mask, 0],
                projections[mask, 1],
                c=colors[c % len(colors)],
                label=clusters[c].label,
                s=80,
                alpha=0.7,
                edgecolors="white",
                linewidth=0.5,
            )
            if clusters[c].centroid:
                ax.scatter(
                    clusters[c].centroid[0],
                    clusters[c].centroid[1],
                    c=colors[c % len(colors)],
                    marker="X",
                    s=200,
                    edgecolors="black",
                    linewidth=1.5,
                )

        ax.set_title("Participant Opinion Clusters (PCA Projection)", fontsize=13, pad=15)
        ax.set_xlabel("PCA Component 1", fontsize=11)
        ax.set_ylabel("PCA Component 2", fontsize=11)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        return output_path

    def generate_report(self, output_dir: str = None) -> dict:
        """
        Generate the full consensus report: JSON structure + markdown text + visualizations.

        This is the main deliverable for policymakers. It answers:
        - How many opinion groups exist?
        - What do they agree on? (bridge statements)
        - How strong is the consensus? (unity score, consensus index)
        - Where are the geographic concerns? (fear heatmap)

        Returns the report as a dict (also saved as JSON and markdown files).
        """
        if output_dir is None:
            output_dir = str(config.OUTPUT_DIR)
        os.makedirs(output_dir, exist_ok=True)

        # Compute metrics
        unity = self.compute_unity_score()
        consensus_idx = self.compute_consensus_index()

        # Get bridge statement texts from database
        bridge_details = []
        for b in self.result["bridge_statements"]:
            stmt = models.get_statement_by_id(self.conn, b["statement_id"])
            if stmt:
                bridge_details.append({
                    "id": b["statement_id"],
                    "text": stmt.text,
                    "bridge_score": b["bridge_score"],
                    "clusters_agreeing": b["clusters_agreeing"],
                    "per_cluster_agreement": b["per_cluster_agreement"],
                })

        # Cluster summaries
        cluster_summaries = []
        for c in self.result["clusters"]:
            cluster_summaries.append({
                "label": c.label,
                "size": len(c.member_ids),
                "centroid": c.centroid,
            })

        # Build report structure
        report = {
            "meta": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "system": "Algorithmic Consensus v0.1",
                "total_participants": self.result["metadata"]["n_participants"],
                "total_statements": self.result["metadata"]["n_statements"],
                "vote_coverage_pct": self.result["metadata"]["vote_coverage_pct"],
            },
            "metrics": {
                "unity_score": unity,
                "consensus_index": consensus_idx,
                "pca_explained_variance": self.result["metadata"]["pca_explained_variance"],
                "silhouette_score": self.result["metadata"]["silhouette_score"],
                "cluster_count": self.result["metadata"]["cluster_count"],
            },
            "clusters": cluster_summaries,
            "bridge_statements": bridge_details,
        }

        # Generate visualizations (optional, skip if matplotlib unavailable)
        try:
            heatmap_path = self.generate_fear_heatmap(
                os.path.join(output_dir, "fear_heatmap.png")
            )
            cluster_path = self.generate_cluster_visualization(
                os.path.join(output_dir, "clusters.png")
            )
            report["visualizations"] = {
                "fear_heatmap": heatmap_path,
                "cluster_plot": cluster_path,
            }
        except ImportError:
            # matplotlib/seaborn not installed - skip PNG generation
            report["visualizations"] = {}

        # Save JSON report
        json_path = os.path.join(output_dir, "report.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        # Save markdown report
        md_path = os.path.join(output_dir, "report.md")
        self._write_markdown_report(report, md_path)

        # Save to database
        models.save_result(self.conn, "consensus", report)

        report["output_paths"] = {
            "json": json_path,
            "markdown": md_path,
            "heatmap": heatmap_path,
            "clusters": cluster_path,
        }

        return report

    def _write_markdown_report(self, report: dict, path: str) -> None:
        """Write a human-readable markdown version of the report."""
        lines = [
            "# Algorithmic Consensus - Deliberation Report",
            "",
            f"Generated: {report['meta']['generated_at']}",
            "",
            "## Summary",
            "",
            f"- **Participants:** {report['meta']['total_participants']}",
            f"- **Statements:** {report['meta']['total_statements']}",
            f"- **Vote Coverage:** {report['meta']['vote_coverage_pct']}%",
            f"- **Opinion Groups Found:** {report['metrics']['cluster_count']}",
            "",
            "## Consensus Metrics",
            "",
            f"- **Unity Score:** {report['metrics']['unity_score']}",
        ]

        # Interpret unity score
        us = report["metrics"]["unity_score"]
        if us < 0.10:
            lines.append("  - Interpretation: Deep polarization. Very little common ground.")
        elif us < 0.25:
            lines.append("  - Interpretation: Some common ground is emerging.")
        elif us < 0.50:
            lines.append("  - Interpretation: Strong consensus forming. Good basis for policy.")
        else:
            lines.append("  - Interpretation: Very high agreement. Verify participant diversity.")

        lines.extend([
            f"- **Consensus Index:** {report['metrics']['consensus_index']}",
            f"- **PCA Explained Variance:** {report['metrics']['pca_explained_variance']}",
            f"- **Cluster Separation (Silhouette):** {report['metrics']['silhouette_score']}",
            "",
            "## Opinion Groups",
            "",
        ])

        for c in report["clusters"]:
            lines.append(f"### {c['label']} ({c['size']} participants)")
            lines.append("")

        lines.extend([
            "## Bridge Statements (Cross-Group Consensus)",
            "",
            "These are ideas that received strong agreement (>60%) from multiple opposing groups.",
            "",
        ])

        if not report["bridge_statements"]:
            lines.append("*No bridge statements found. The groups have not yet found common ground.*")
        else:
            for i, b in enumerate(report["bridge_statements"], 1):
                lines.append(f"### {i}. \"{b['text']}\"")
                lines.append(f"- Bridge Score: {b['bridge_score']}")
                lines.append(f"- Agreed by {b['clusters_agreeing']} groups")
                per_cluster = b.get("per_cluster_agreement", {})
                for cid, rate in per_cluster.items():
                    cluster_label = f"Group {chr(65 + int(cid))}"
                    lines.append(f"  - {cluster_label}: {rate:.0%} agreement")
                lines.append("")

        lines.extend([
            "## Visualizations",
            "",
            f"- Cluster Map: {report.get('visualizations', {}).get('cluster_plot', 'N/A')}",
            f"- Fear Heatmap: {report.get('visualizations', {}).get('fear_heatmap', 'N/A')}",
            "",
            "---",
            "*Report generated by Algorithmic Consensus v0.1*",
            "*AI observes and measures; humans speak and decide.*",
        ])

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

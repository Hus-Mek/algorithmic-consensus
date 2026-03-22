"""Router: analysis pipeline and results."""

import os
import sqlite3
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api.deps import get_db
from api.schemas import (
    FullAnalysisResponse,
    AnalysisMetricsResponse,
    ClusterResponse,
    BridgeStatementResponse,
    ClusterVisualizationResponse,
    HeatmapDataResponse,
)
import config
import models

router = APIRouter()


def _make_conn() -> sqlite3.Connection:
    """Create a thread-safe SQLite connection for heavy analysis work."""
    conn = sqlite3.connect(str(config.DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _report_to_response(report: dict) -> FullAnalysisResponse:
    """Convert the report dict into the Pydantic response model."""
    return FullAnalysisResponse(
        meta=report["meta"],
        metrics=AnalysisMetricsResponse(**report["metrics"]),
        clusters=[ClusterResponse(**c) for c in report["clusters"]],
        bridge_statements=[BridgeStatementResponse(**b) for b in report["bridge_statements"]],
    )


@router.post("/analysis", response_model=FullAnalysisResponse)
def run_analysis():
    """Trigger full deliberation analysis pipeline. Returns computed report."""
    from deliberation import DeliberationEngine
    from consensus import ConsensusAnalyzer

    conn = _make_conn()
    try:
        engine = DeliberationEngine(conn)
        result = engine.run_full_analysis()
        analyzer = ConsensusAnalyzer(conn, result)
        report = analyzer.generate_report()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
    return _report_to_response(report)


@router.get("/analysis/latest", response_model=FullAnalysisResponse)
def get_latest_analysis(conn: sqlite3.Connection = Depends(get_db)):
    """Return the most recent cached analysis without recomputing."""
    result = models.get_latest_result(conn, "consensus")
    if not result:
        raise HTTPException(status_code=404, detail="No analysis results yet. Run POST /api/analysis first.")
    return _report_to_response(result)


@router.get("/analysis/clusters", response_model=ClusterVisualizationResponse)
def get_cluster_data():
    """Return raw scatter data for frontend cluster visualization."""
    from deliberation import DeliberationEngine

    conn = _make_conn()
    try:
        engine = DeliberationEngine(conn)
        result = engine.run_full_analysis()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

    projections = result["projections"]
    labels = result["labels"]
    pids = result["participant_ids"]
    clusters = result["clusters"]

    participants_data = []
    for i, pid in enumerate(pids):
        cluster_id = int(labels[i])
        participants_data.append({
            "id": pid,
            "x": float(projections[i, 0]),
            "y": float(projections[i, 1]),
            "cluster_id": cluster_id,
            "cluster_label": clusters[cluster_id].label,
        })

    centroids_data = [
        {"label": c.label, "x": c.centroid[0], "y": c.centroid[1]}
        for c in clusters if c.centroid
    ]

    return ClusterVisualizationResponse(
        participants=participants_data,
        centroids=centroids_data,
    )


@router.get("/analysis/heatmap", response_model=HeatmapDataResponse)
def get_heatmap_data():
    """Return raw heatmap grid data for frontend rendering."""
    from deliberation import DeliberationEngine

    conn = _make_conn()
    try:
        engine = DeliberationEngine(conn)
        result = engine.run_full_analysis()

        locations = models.get_participant_locations(conn)
        statements = models.get_all_statements(conn)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

    pids = result["participant_ids"]
    labels = result["labels"]
    clusters = result["clusters"]

    pid_to_cluster = {}
    for i, pid in enumerate(pids):
        pid_to_cluster[pid] = clusters[int(labels[i])].label

    negative_stmts = [s for s in statements if s.sentiment == config.FEAR_SENTIMENT_LABEL]

    counts = defaultdict(lambda: defaultdict(int))
    for stmt in negative_stmts:
        author_loc = locations.get(stmt.author_id, "")
        author_cluster = pid_to_cluster.get(stmt.author_id, "")
        if author_loc and author_cluster:
            counts[author_loc][author_cluster] += 1

    all_locations = sorted(counts.keys()) if counts else []
    all_cluster_labels = sorted({c.label for c in clusters})

    values = []
    for loc in all_locations:
        row = [counts[loc].get(cl, 0) for cl in all_cluster_labels]
        values.append(row)

    return HeatmapDataResponse(
        locations=all_locations,
        cluster_labels=all_cluster_labels,
        values=values,
    )


@router.get("/analysis/heatmap/image")
def get_heatmap_image():
    """Return the generated fear heatmap PNG."""
    path = os.path.join(str(config.OUTPUT_DIR), "fear_heatmap.png")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Heatmap not generated yet. Run POST /api/analysis first.")
    return FileResponse(path, media_type="image/png")


@router.get("/analysis/clusters/image")
def get_cluster_image():
    """Return the generated cluster visualization PNG."""
    path = os.path.join(str(config.OUTPUT_DIR), "clusters.png")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Cluster plot not generated yet. Run POST /api/analysis first.")
    return FileResponse(path, media_type="image/png")

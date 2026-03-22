"""
schemas.py - Pydantic request/response models for the API

Translates between JSON and the existing dataclasses in models.py.
"""

from pydantic import BaseModel, Field
from typing import Optional


# --- Requests ---

class CreateParticipantRequest(BaseModel):
    location: str = ""


class SubmitStatementRequest(BaseModel):
    author_id: str
    text: str = Field(..., max_length=140)


class CastVoteRequest(BaseModel):
    participant_id: str
    statement_id: int
    value: int = Field(..., ge=-1, le=1)


# --- Responses ---

class ParticipantResponse(BaseModel):
    id: str
    created_at: str
    location: str


class StatementResponse(BaseModel):
    id: int
    text: str
    sentiment: str
    sentiment_score: float
    created_at: str


class VoteResponse(BaseModel):
    participant_id: str
    statement_id: int
    value: int
    created_at: str


class StatusResponse(BaseModel):
    participants: int
    statements: int
    votes: int
    vote_coverage_pct: float


class ClusterResponse(BaseModel):
    label: str
    size: int
    centroid: Optional[list] = None


class BridgeStatementResponse(BaseModel):
    id: int
    text: str
    bridge_score: float
    clusters_agreeing: int
    per_cluster_agreement: dict


class AnalysisMetricsResponse(BaseModel):
    unity_score: float
    consensus_index: float
    pca_explained_variance: float
    silhouette_score: float
    cluster_count: int


class FullAnalysisResponse(BaseModel):
    meta: dict
    metrics: AnalysisMetricsResponse
    clusters: list[ClusterResponse]
    bridge_statements: list[BridgeStatementResponse]


class ClusterVisualizationResponse(BaseModel):
    participants: list[dict]
    centroids: list[dict]


class HeatmapDataResponse(BaseModel):
    locations: list[str]
    cluster_labels: list[str]
    values: list[list[int]]

from typing import List, Dict, Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str


class RiskScoreResponse(BaseModel):
    risk_score: float
    band: str
    top_contributors: List[Dict[str, Any]]
    lat: float
    lon: float


class ShelterResponse(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    distance_km: float
    capacity: int


class NearbySheltersResponse(BaseModel):
    shelters: List[ShelterResponse]
    lat: float
    lon: float


class ConfigResponse(BaseModel):
    mode: str
    version: str
    features: Dict[str, bool]
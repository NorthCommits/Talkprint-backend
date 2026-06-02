from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


# Auth
class SignUpRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    access_token: str
    user_id: str
    email: str


# Sessions
class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    filename: str
    duration_seconds: Optional[float]
    status: str
    created_at: datetime


# Speakers
class SpeakerResponse(BaseModel):
    id: UUID
    session_id: UUID
    label: str
    talk_time_seconds: float
    talk_time_percent: float


# Segments
class SegmentResponse(BaseModel):
    id: UUID
    session_id: UUID
    speaker_id: UUID
    start_time: float
    end_time: float
    transcript: str


# Analysis
class AnalysisResponse(BaseModel):
    id: UUID
    session_id: UUID
    dominance_ratio: dict
    interruption_count: int
    turn_taking_score: float
    topic_coherence_score: float
    overall_health_score: float
    created_at: datetime
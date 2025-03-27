# backend/models/hospital_model.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Hospital(BaseModel):
    id: int
    name: str
    address: str
    latitude: float
    longitude: float
    specializations: List[str]
    rating: float
    availability: float
    avg_wait_time: int
    success_rate: float
    beds: int

class Doctor(BaseModel):
    id: int
    name: str
    specialization: str
    experience: int
    success_rate: float
    hospital_id: int

class Review(BaseModel):
    review_id: int
    hospital_id: int
    doctor_id: Optional[int] = None
    patient_name: str
    rating: int = Field(..., ge=1, le=5)
    text: str
    timestamp: datetime
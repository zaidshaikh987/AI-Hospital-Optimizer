# backend/app.py
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import os
from pathlib import Path
from geopy.distance import geodesic
from typing import List, Dict, Optional

# Local imports - Assuming these are in 'backend/services' and 'backend/models'
from backend.models.hospital_model import Hospital, Doctor, Review  # Corrected import paths
from backend.services.geocoder import get_address_from_coords, get_coords_from_address # Corrected import paths
from backend.services.ranking import calculate_hospital_score # Corrected import paths
from backend.services.sentiment_analysis import analyze_sentiment # Corrected import paths
from backend.services.symptom_mapping import SYMPTOM_SPECIALIZATION_MAP, SYMPTOM_SEVERITY # Corrected import paths


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data loading
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = os.path.join(BASE_DIR, 'backend', 'dummy_data') # Ensure 'backend' is included
HOSPITALS_JSON = os.path.join(DATA_DIR, 'hospitals.json')
DOCTORS_JSON = os.path.join(DATA_DIR, 'doctors.json')
REVIEWS_JSON = os.path.join(DATA_DIR, 'reviews.json') # Assuming reviews are in JSON now

class DoctorRecommendation(BaseModel):
    recommended_doctor: Doctor

# Load hospitals, doctors, and reviews
with open(HOSPITALS_JSON) as f:
    hospitals_data = json.load(f)
    hospitals = [Hospital(**h) for h in hospitals_data]

with open(DOCTORS_JSON) as f:
    doctors = [Doctor(**d) for d in json.load(f)]

# Endpoints

@app.get("/", status_code=200)
async def health_check():
    return {"status": "OK"}

@app.get("/hospitals", response_model=List[Hospital])
async def get_hospitals(address: str = Query(None), lat: float = Query(None), lng: float = Query(None)):
    if address and not (lat or lng):
        lat, lng = get_coords_from_address(address)

    if lat and lng:
        # Return hospitals sorted by distance
        sorted_hospitals = sorted(
            hospitals,
            key=lambda h: geodesic((lat, lng), (h.latitude, h.longitude)).km
        )
        return sorted_hospitals[:50] # Limit to top 50 for performance

    return hospitals[:100] # Return top 100 if no location provided



@app.post("/analyze-sentiment")
async def analyze_review_sentiment(review: Review):
    result = analyze_sentiment(review.text)
    return {
        "sentiment": result['label'],
        "confidence": round(result['score'], 2),
        "rating": review.rating
    }

@app.get("/rank-hospitals")
async def rank_hospitals(lat: float, lng: float):
    ranked_hospitals = []
    for hospital in hospitals:
        score = calculate_hospital_score(hospital, lat, lng)
        ranked_hospitals.append({
            **hospital.dict(),
            "score": score,
            "distance": round(geodesic((lat, lng), (hospital.latitude, hospital.longitude)).km, 2)
        })

    return sorted(ranked_hospitals, key=lambda x: x['score'], reverse=True)

@app.get("/predict-wait-time/{hospital_id}")
async def predict_wait_time(hospital_id: int):
    hospital = next((h for h in hospitals if h.id == hospital_id), None)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    # Simple prediction based on historical average
    return {"predicted_wait": hospital.avg_wait_time}


@app.post("/recommend-doctor")
async def recommend_doctor(request_data: dict = Body(...)):
    try:
        symptoms = [s.strip().lower() for s in request_data.get("symptoms", [])]
        lat = request_data.get("lat")
        lng = request_data.get("lng")

        # Validate inputs
        if not symptoms or lat is None or lng is None: # Corrected validation for None
            raise HTTPException(status_code=400, detail="Missing required parameters: symptoms, lat, lng")

        # Get matching specializations
        specializations = set()
        for symptom in symptoms:
            specializations.update(SYMPTOM_SPECIALIZATION_MAP.get(symptom, []))

        # Find matching doctors in top 10 hospitals (using ranked hospitals)
        ranked_hospitals_data = await rank_hospitals(lat, lng) # Use await here
        hospital_ids = [h['id'] for h in ranked_hospitals_data[:10]]

        # Find matching doctors
        matched_doctors = [
            d for d in doctors
            if d.hospital_id in hospital_ids
            and any(spec.lower() in d.specialization.lower() for spec in specializations) # Case-insensitive matching
        ]

        # Sort by experience + success rate + severity (using SYMPTOM_SEVERITY)
        matched_doctors.sort(
            key=lambda d: (
                -max((SYMPTOM_SEVERITY.get(s, 1) for s in symptoms), default=1), # Higher severity first, default to 1 if symptom not found
                -d.experience, # More experience first
                -d.success_rate # Higher success rate first
            ),
        )

        if not matched_doctors:
            return { # Return empty list if no doctor is found, frontend can handle this
                "recommended_doctors": [],
                "matched_symptoms": symptoms
            }

        return {
            "recommended_doctors": matched_doctors[:5], # Return top 5 doctors
            "matched_symptoms": symptoms
        }

    except HTTPException as http_exc: # Catch HTTP Exceptions directly
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hospitals/{hospital_id}", response_model=Hospital)
async def get_hospital(hospital_id: int):
    hospital = next((h for h in hospitals if h.id == hospital_id), None)
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hospital


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True) # Corrected uvicorn run command
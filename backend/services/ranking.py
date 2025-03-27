from geopy.distance import geodesic
from backend.models.hospital_model import Hospital

def calculate_hospital_score(hospital: Hospital, user_lat: float, user_lng: float):
    # Weighted scoring system
    weights = {
        'distance': 0.35,
        'rating': 0.25,
        'availability': 0.20,
        'success_rate': 0.15,
        'wait_time': 0.05
    }
    
    # Calculate distance score
    hospital_coords = (hospital.latitude, hospital.longitude)
    user_coords = (user_lat, user_lng)
    distance_km = geodesic(user_coords, hospital_coords).km
    distance_score = max(0, 100 - (distance_km * 2)) * weights['distance']
    
    # Calculate rating score (normalized to 5-star scale)
    rating_score = (hospital.rating / 5) * 100 * weights['rating']
    
    # Availability score (percentage of available beds)
    availability_score = hospital.availability * 100 * weights['availability']
    
    # Success rate score
    success_score = hospital.success_rate * weights['success_rate']
    
    # Wait time penalty (lower wait times are better)
    wait_time_penalty = max(0, (60 - hospital.avg_wait_time) / 60 * 100) * weights['wait_time']
    
    total_score = sum([
        distance_score,
        rating_score,
        availability_score,
        success_score,
        wait_time_penalty
    ])
    
    return round(total_score, 2)
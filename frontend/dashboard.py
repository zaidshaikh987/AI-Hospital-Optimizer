# frontend/dashboard.py
import os
import logging
from typing import Dict, List, Optional
import requests
import pandas as pd
import pydeck as pdk
import streamlit as st
import googlemaps # Ensure googlemaps is installed
from geopy.distance import geodesic

# MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(layout="wide", page_title="AI Hospital Optimizer")

# Configuration - Direct assignments for development
GMAPS_API_KEY = "" # **Replace with your actual API key**
GMAPS_GEOCODING_API = "https://maps.googleapis.com/maps/api/geocode/json"
BACKEND_URL = "http://localhost:8000"
DEFAULT_LOCATION = {"lat": 40.7128, "lng": -74.0060, "address": "Nashik, N"}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state
if 'user_location' not in st.session_state:
    st.session_state.user_location = None
if 'location_update' not in st.session_state:
    st.session_state.location_update = None


# --- Location Services ---
def get_current_location() -> Dict[str, float]:
    """Get approximate location using IP and Google Maps API"""
    try:
        # Get IP-based location
        ip_response = requests.get('https://ipinfo.io/json', timeout=3)
        ip_data = ip_response.json()
        loc_str = ip_data.get('loc', '40.7128,-74.0060')

        # Reverse geocode with Google Maps
        params = {
            'latlng': loc_str,
            'key': GMAPS_API_KEY,
            'result_type': 'locality'
        }
        gmaps_response = requests.get(GMAPS_GEOCODING_API, params=params, timeout=5)
        gmaps_data = gmaps_response.json()

        if gmaps_data['status'] == 'OK':
            return {
                'lat': float(loc_str.split(',')[0]),
                'lng': float(loc_str.split(',')[1]),
                'address': gmaps_data['results'][0]['formatted_address']
            }
    except Exception as e:
        logger.error(f"Location error: {str(e)}")
    return DEFAULT_LOCATION

def update_location():
    """Update location from browser geolocation"""
    if st.session_state.location_update:
        try:
            coords = st.session_state.location_update['coords']
            params = {
                'latlng': f"{coords['latitude']},{coords['longitude']}",
                'key': GMAPS_API_KEY
            }
            response = requests.get(GMAPS_GEOCODING_API, params=params)
            data = response.json()
            st.session_state.user_location = {
                'lat': coords['latitude'],
                'lng': coords['longitude'],
                'address': data['results'][0]['formatted_address']
            }
        except Exception as e:
            logger.error(f"Precise location error: {str(e)}")

# --- Hospital Display Functions ---
def show_hospital_map(hospitals: List[Dict]) -> None:
    """Display hospitals on an interactive map"""
    if not hospitals:
        st.warning("No hospital data available for mapping")
        return

    try:
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=hospitals,
            get_position=["longitude", "latitude"],
            get_radius=200,
            get_fill_color=[255, 0, 0, 140],
            pickable=True
        )

        view_state = pdk.ViewState(
            latitude=hospitals[0]['latitude'] if hospitals else DEFAULT_LOCATION['lat'], # Handle empty hospitals list
            longitude=hospitals[0]['longitude'] if hospitals else DEFAULT_LOCATION['lng'], # Handle empty hospitals list
            zoom=11
        )

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "{name}\nRating: {rating}\nBeds: {beds}"}
        ))
    except Exception as e:
        st.error(f"Failed to render map: {str(e)}")


def get_hospitals_from_backend(address: str) -> Optional[List[Dict]]: # Renamed to avoid confusion
    """Fetch hospitals from backend API."""
    try:
        response = requests.get(
            f"{BACKEND_URL}/hospitals",
            params={"address": address},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching hospitals: {str(e)}")
        st.error(f"Failed to fetch hospitals: {str(e)}")
        return None


def display_doctor(doctor: Dict) -> None:
    """Display doctor information in a formatted way."""
    if not doctor:
        return

    st.success("## Recommended Doctor")
    cols = st.columns([1, 3])
    with cols[0]:
        st.image("https://img.icons8.com/color/96/000000/doctor-male.png", width=100)
    with cols[1]:
        st.markdown(f"**Name:** {doctor.get('name', 'N/A')}")
        st.markdown(f"**Specialization:** {doctor.get('specialization', 'N/A')}")
        st.markdown(f"**Experience:** {doctor.get('experience', 'N/A')} years")
        st.markdown(f"**Success Rate:** {doctor.get('success_rate', 'N/A')}%")
        if 'matched_symptoms' in doctor:
            st.info(f"Matched symptoms: {', '.join(doctor['matched_symptoms'])}")

def display_hospital_card(hospital):
    with st.container():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image("https://img.icons8.com/color/96/hospital.png", width=80)
        with col2:
            st.subheader(hospital['name'])
            st.caption(f"📍 {hospital['address']}")

            # Metrics
            cols = st.columns(4)
            cols[0].metric("Rating", f"{hospital['rating']}/5")
            cols[1].metric("Wait Time", f"{hospital['avg_wait_time']} mins")
            cols[2].metric("Success Rate", f"{hospital['success_rate']}%")
            cols[3].metric("Beds Available", hospital['beds'])

            # Specializations
            st.write("**Specializations:**")
            for spec in hospital['specializations']:
                st.button(spec, spec, disabled=True) # Added key to buttons

            # Expandable reviews
            with st.expander("View Reviews"):
                show_reviews(hospital['id'])
                if st.button("Add Review", key=f"review_{hospital['id']}"):
                    show_review_form(hospital['id'])

def show_review_form(hospital_id):
    with st.form(key=f"review_form_{hospital_id}"):
        rating = st.slider("Rating", 1, 5, 5)
        review_text = st.text_area("Your Experience")
        if st.form_submit_button("Submit Review"):
            if post_review(hospital_id, rating, review_text):
                st.success("Review submitted!")
            else:
                st.error("Failed to submit review.")

def post_review(hospital_id, rating, text):
    try:
        response = requests.post(
            f"{BACKEND_URL}/reviews",
            json={
                "hospital_id": hospital_id,
                "rating": rating,
                "text": text
            }
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error submitting review: {str(e)}")
        return False

def show_reviews(hospital_id):
    try:
        response = requests.get(f"{BACKEND_URL}/reviews", params={"hospital_id": hospital_id})
        if response.status_code == 200:
            reviews = response.json()
            if reviews:
                for review in reviews:
                    st.markdown(f"**Rating:** {review['rating']}/5")
                    st.write(f"_{review['text']}_")
                    st.write("---")
            else:
                st.info("No reviews yet for this hospital.")
        else:
            st.error("Failed to load reviews.")
    except Exception as e:
        st.error(f"Error loading reviews: {e}")


# --- Main App ---
st.title("🏥 AI-Powered Hospital Optimization System")

# Location JS Handler
st.components.v1.html("""
<script>
window.addEventListener('message', function(event) {
    if (event.data.type === 'locationUpdate') {
        window.parent.postMessage({
            type: 'setSessionState',
            key: 'location_update',
            value: event.data
        }, '*');
    }
});
</script>
""", height=0)

update_location()

# Get initial location
current_loc = st.session_state.user_location or get_current_location()

# --- Hospital Search Section ---
with st.container():
    st.header("Find Hospitals")
    search_col, filter_col = st.columns([2, 1])

    with search_col:
        address = st.text_input(
            "Enter Location",
            current_loc["address"],
            help="We've detected your approximate location"
        )
        if st.button("Use My Current Location"):
            with st.spinner("Detecting precise location..."):
                st.components.v1.html("""
                <script>
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        window.parent.postMessage({
                            type: 'locationUpdate',
                            coords: position.coords
                        }, '*');
                    },
                    function(error) {
                        window.parent.postMessage({
                            type: 'locationError',
                            message: error.message
                        }, '*');
                    }
                );
                </script>
                """, height=0)
                st.experimental_rerun()

    with filter_col:
        min_rating = st.slider("Minimum Rating", 1.0, 5.0, 3.0, 0.1) # Adjusted default min rating
        max_distance = st.slider("Max Distance (km)", 5, 100, 50)

    if st.button("Search Hospitals"):
        with st.spinner("Finding best hospitals..."):
            try:
                response = requests.get(
                    f"{BACKEND_URL}/hospitals",
                    params={
                        "address": address,
                        "lat": current_loc["lat"],
                        "lng": current_loc["lng"]
                    }
                )

                if response.status_code == 200:
                    hospitals_data = response.json()
                    filtered_hospitals = [
                        h for h in hospitals_data
                        if h['rating'] >= min_rating and
                        geodesic((current_loc["lat"], current_loc["lng"]), (h['latitude'], h['longitude'])).km <= max_distance
                    ]

                    st.subheader(f"Found {len(filtered_hospitals)} hospitals")
                    for hospital in filtered_hospitals:
                        display_hospital_card(hospital)

                    st.subheader("Hospital Map")
                    show_hospital_map(filtered_hospitals)
                else:
                    st.error("Failed to fetch hospitals")

            except Exception as e:
                st.error(f"Error: {str(e)}")

# --- Doctor Recommendation Section ---
with st.container():
    st.header("👨⚕️ Smart Doctor Matching")
    symptoms = st.multiselect(
        "Select Symptoms",
        ["Chest Pain", "Fever", "Headache", "Fracture", "Cough", "Fatigue", "Sore Throat", "Runny Nose", "Muscle Aches", "Nausea"], # Added more symptom examples
        key="symptoms"
    )

    if st.button("Find Best Doctor"):
        if not symptoms:
            st.warning("Please select at least one symptom")
        else:
            with st.spinner("Finding the best doctor..."):
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/recommend-doctor",
                        json={
                            "symptoms": symptoms,
                            "lat": current_loc["lat"],
                            "lng": current_loc["lng"]
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=5
                    )

                    if response.status_code == 200:
                        result = response.json()
                        doctors = result.get('recommended_doctors') # Expecting a list now
                        if doctors:
                            st.success(f"Top {len(doctors)} Recommended Doctors")
                            for doctor in doctors:
                                display_doctor({
                                    **doctor,
                                    'matched_symptoms': result.get('matched_symptoms', symptoms)
                                })
                        else:
                            st.warning("No doctors found matching your symptoms and location.")


                    elif response.status_code == 404:
                        error_data = response.json()
                        st.warning(error_data.get("detail", {}).get("message", "No matching doctors found"))
                        if "suggestions" in error_data.get("detail", {}):
                            st.info("Suggestions: " + ", ".join(error_data["detail"]["suggestions"]))

                    elif response.status_code == 400: # Handle bad request (missing params)
                        error_data = response.json()
                        st.error(f"Error: {error_data.get('detail', 'Bad Request')}")

                    else:
                        st.error(f"API Error: {response.status_code}")
                        st.json(response.json())

                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {str(e)}")

# --- Debug Section ---
with st.expander("Debug Information"):
    st.write("### API Status")
    try:
        health_response = requests.get(f"{BACKEND_URL}/", timeout=2)
        if health_response.status_code == 200:
            st.success("Backend API is running")
            st.json(health_response.json())

            # Test hospitals endpoint
            hospitals_response = requests.get(f"{BACKEND_URL}/hospitals", timeout=2)
            if hospitals_response.status_code == 200:
                st.success("Hospitals endpoint working")
                st.json(hospitals_response.json()[:1])
            else:
                st.error(f"Hospitals endpoint error: {hospitals_response.status_code}")
        else:
            st.error(f"API health check failed: {health_response.status_code}")
    except Exception as e:
        st.error(f"Connection failed: {str(e)}")

    st.write("### Current Location Data")
    st.json(current_loc)
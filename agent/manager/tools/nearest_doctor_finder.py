# ───────────────────────────────────────────────────────────────
# NearestDoctorFinder – Google-ADK functional tool
# Finds nearby doctors / hospitals via Google Maps Places API
# ───────────────────────────────────────────────────────────────
# pip install googlemaps
# Agents call:
#   {"tool": "NearestDoctorFinder",
#    "query": "cardiologist",
#    "location": {"lat": 26.1445, "lng": 91.7362},
#    "radius_m": 5000}
# The tool returns a JSON list of top results with distance, rating,
# address, and a Google-Maps link, optimized for medical recommendations.
# ───────────────────────────────────────────────────────────────

from __future__ import annotations
import os, json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import googlemaps
from geopy.distance import geodesic

# Get API key from environment
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not GOOGLE_MAPS_API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY environment variable is required")

ReturnType = List[Dict[str, Any]]

def nearest_doctor_finder(
    query: str,
    location: Optional[Dict[str, float]] = None,
    address_str: Optional[str] = None,
    radius_m: int = 5000,
    max_results: int = 5,
) -> ReturnType:
    """
    NearestDoctorFinder searches for medical professionals and facilities near the specified location.
    
    This tool is optimized for finding healthcare providers and returns the best recommendations
    based on proximity, ratings, and relevance to the medical query.
    
    Args:
        query: str -> Medical search term, e.g. 'cardiologist', 'hospital', 'nutritionist', 'dentist'
        location: Optional[Dict[str, float]] -> User location dict with 'lat' and 'lng' floats (WGS-84)
        address_str: Optional[str] -> City + state (or any address) to geocode if lat/lng not given
        radius_m: int -> Search radius in metres (max 50 000 per Google Maps API)
        max_results: int -> Limit number of places returned (default 5, max 20)
    
    Returns:
        List of nearby medical places with name, address, rating, distance, and Google Maps URL.
        Results are sorted by relevance and proximity for optimal medical recommendations.
    
    Raises:
        ValueError: If address cannot be geocoded or API key is missing
    """
    
    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    
    # ── Resolve coordinates ───────────────────────────────────
    if location:  # lat/lng already given
        lat, lng = location["lat"], location["lng"]
    else:  # need to geocode address_str
        if not address_str:
            raise ValueError("Either location or address_str must be provided")
        geo = gmaps.geocode(address_str)
        if not geo:
            raise ValueError(f"Could not geocode '{address_str}'. Please check the address.")
        lat = geo[0]["geometry"]["location"]["lat"]
        lng = geo[0]["geometry"]["location"]["lng"]

    # ── Search for medical facilities ─────────────────────────
    resp = gmaps.places(
        query=query,
        location=(lat, lng),
        radius="distance",  # Prioritize closer facilities
        type="health"  # Use 'health' type for better medical facility results
    )
    
    places = resp.get("results", [])
    
    # ── Enrich and filter results ─────────────────────────────
    enriched: ReturnType = []
    for p in places[:max_results]:
        place_loc = p["geometry"]["location"]
        dist_km = round(
            geodesic((lat, lng), (place_loc["lat"], place_loc["lng"])).km, 2
        )
        
        # Get additional details for better recommendations
        place_details = gmaps.place(p["place_id"], fields=["formatted_phone_number", "opening_hours", "website"])
        
        enriched.append({
            "name": p["name"],
            "address": p.get("formatted_address", "Address not available"),
            "rating": p.get("rating", "No rating"),
            "distance_km": dist_km,
            "maps_url": f"https://www.google.com/maps/place/?q=place_id:{p['place_id']}",
            "phone": place_details.get("result", {}).get("formatted_phone_number", "Phone not available"),
            "website": place_details.get("result", {}).get("website", "Website not available"),
            "open_now": place_details.get("result", {}).get("opening_hours", {}).get("open_now", "Hours not available"),
            "place_id": p["place_id"]
        })
    
    # Sort by distance and rating for best recommendations
    enriched.sort(key=lambda x: (x["distance_km"], -x["rating"] if isinstance(x["rating"], (int, float)) else 0))
    
    return enriched[:max_results]

# Alias for backward compatibility
map_finder_tool = nearest_doctor_finder

import os
import re
import json
import requests
import google.generativeai as genai
from django.conf import settings

# Configure Gemini
genai.configure(api_key=settings.GENAI_API_KEY)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

def analyze_civic_issue(image_path: str, user_text: str) -> dict:
    """
    Analyze civic issue: extract location info, compute road/POI metrics,
    and call Gemini with image + text + location.
    Returns structured JSON matching your updated schema.
    """

    # --- 1️⃣ Extract coordinates from filename ---
    lat, lon = 0.0, 0.0
    match = re.search(r'(\d+\.\d+)_(\d+\.\d+)_', os.path.basename(image_path))
    if match:
        lat = float(match.group(1))
        lon = float(match.group(2))

    # --- 2️⃣ Reverse geocoding with Nominatim ---
    address = "Unknown"
    try:
        resp = requests.get(NOMINATIM_URL, params={
            'lat': lat, 'lon': lon, 'format': 'json', 'addressdetails': 1
        }, timeout=10)
        if resp.ok:
            data = resp.json()
            display_name = data.get('display_name', '')
            address = display_name if display_name else "Unknown"
    except Exception as e:
        print(f"⚠️ Nominatim failed: {e}")

    # --- 3️⃣ Road type from Overpass API ---
    road_type = 'residential'
    road_count = 0
    try:
        road_query = f"""
        [out:json];
        way["highway"](around:50,{lat},{lon});
        out tags;
        """
        road_resp = requests.post(OVERPASS_URL, data=road_query, timeout=10)
        if road_resp.ok:
            road_data = road_resp.json()
            road_count = len(road_data.get('elements', []))
            road_types = [el.get('tags', {}).get('highway','') for el in road_data.get('elements',[])]
            if any(rt in ['motorway','trunk','primary'] for rt in road_types):
                road_type = 'main'
            elif any(rt in ['secondary','tertiary'] for rt in road_types):
                road_type = 'local'
            elif any(rt in ['residential','unclassified'] for rt in road_types):
                road_type = 'residential'
            elif any(rt in ['service','track'] for rt in road_types):
                road_type = 'service'
    except Exception as e:
        print(f"⚠️ Overpass road query failed: {e}")

    # --- 4️⃣ POI analysis ---
    area_type = 'residential'
    poi_count = 0
    population_density = 0.5
    try:
        poi_query = f"""
        [out:json];
        (
          node["amenity"](around:200,{lat},{lon});
          node["shop"](around:200,{lat},{lon});
          node["tourism"](around:200,{lat},{lon});
          node["leisure"](around:200,{lat},{lon});
          node["healthcare"](around:200,{lat},{lon});
          node["education"](around:200,{lat},{lon});
        );
        out;
        """
        poi_resp = requests.post(OVERPASS_URL, data=poi_query, timeout=10)
        if poi_resp.ok:
            poi_data = poi_resp.json()
            poi_count = len(poi_data.get('elements', []))
            amenities = [el.get('tags', {}).get('amenity','') for el in poi_data.get('elements',[])]
            if any(a in ['hospital','clinic'] for a in amenities):
                area_type = 'hospital_zone'
            elif any(a in ['school','university'] for a in amenities):
                area_type = 'school_zone'
            elif any(a in ['restaurant','shop'] for a in amenities):
                area_type = 'market'
            elif any(a in ['park','leisure'] for a in amenities):
                area_type = 'park'
            else:
                area_type = 'residential'
            population_density = min(1.0, 0.2 + 0.3 * (poi_count/20))
    except Exception as e:
        print(f"⚠️ Overpass POI query failed: {e}")

    # --- 5️⃣ Compute location weight ---
    road_weights = {'main':0.95, 'local':0.9, 'residential':0.6, 'service':0.3}
    area_weights = {'hospital_zone':1.0, 'school_zone':1.0, 'market':0.85, 'residential':0.6, 'park':0.3, 'industrial':0.4}
    location_weight = min(1.0, 0.4*road_weights.get(road_type,0.6) + 0.4*area_weights.get(area_type,0.6) + 0.2*population_density)

    # --- 6️⃣ Build location_info block ---
    location_info = {
        'coordinates': {'lat': lat, 'lon': lon},
        'address': address,
        'road_type': road_type,
        'area_type': area_type,
        'population_density': population_density
    }

    # --- 7️⃣ Gemini prompt ---
    prompt_template = f"""
You are an AI civic issue analyzer.  
Task: Take image + text + location info and output JSON exactly in the updated schema:

- Include problem_type probabilities (all 15 types)
- Include each detailed issue block (pothole, flooding, trash, sewage, etc.)
- Include severity_weight, sensitivity_weight, location_weight, priority_score
- Include location_info
- Include Reports summary

Additional context:
- User text: "{user_text}"
- Location details: {json.dumps(location_info)}
- Image path: "{image_path}"

Return only JSON.
"""

    # --- 8️⃣ Call Gemini ---
    try:
        response = genai.generate(
            model="gemini-1.5-pro",
            messages=[{"role": "user", "content": [prompt_template, user_text, image_path]}]
        )
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e), "raw_response": getattr(response,'text', None)}

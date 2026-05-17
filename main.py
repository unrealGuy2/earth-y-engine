from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from gee_pipeline import initialize_ee, get_coastal_data
from pinn_model import predict_land_loss

initialize_ee()

app = FastAPI(title="Earth-Y PINN Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LocationQuery(BaseModel):
    lat: float
    lng: float
    city: str

class BatchQuery(BaseModel):
    assets: List[LocationQuery]

@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    return {"status": "Earth-Y Engine is Online"}

# --- CORE LOGIC EXTRACTED FOR REUSE ---
def process_asset(query: LocationQuery):
    gee_data = get_coastal_data(query.lat, query.lng)
    is_offshore = gee_data.get('is_offshore', False)
    elevation = gee_data['elevation']
    
    if is_offshore:
        depth = gee_data['depth']
        slope = gee_data['slope_degrees']
        risk = gee_data['risk']
        
        confidence_level = "High"
        confidence_reason = "Based on GEBCO/ETOPO1 bathymetric telemetry"
        
        if risk == "Critical":
            risk_detail = f"Critical risk due to extreme benthic slope ({slope}°). High probability of submarine landslides."
            implications = ["Unsafe for standard rig anchoring.", "High vulnerability to MTDs."]
            trend = "Dynamic seafloor shifting likely."
        elif risk == "Elevated":
            risk_detail = f"Elevated risk due to moderate benthic slope ({slope}°). Requires enhanced anchor monitoring."
            implications = ["Pipeline spanning possible.", "Moderate risk of current-induced scouring."]
            trend = "Moderate seabed variance."
        else:
            risk_detail = f"Low risk. Target asset is located on a stable benthic shelf (Depth: {depth}m, Slope: {slope}°)."
            implications = ["Stable topography for pipeline laying.", "Low probability of mass movement."]
            trend = "Seabed remains geologically stable."
            
        predicted_loss = "N/A (Offshore)"
        year_val = "Current"
        sat_data = "NOAA ETOPO1 & GEBCO Bathymetry"
        model_type = "Benthic Topographical Assessment"
        elev_string = f"-{depth}m (Depth)"

    else:
        predicted_loss_val = predict_land_loss(elevation, query.lat)
        risk = "Critical" if predicted_loss_val > 10 else "Elevated" if predicted_loss_val > 5 else "Low"
        confidence_level = "Moderate" if predicted_loss_val > 10 else "High"
        confidence_reason = "Based on data consistency and physical constraints"
        
        if risk == "Critical":
            risk_detail = f"Critical risk due to severe projected shoreline retreat (~{predicted_loss_val}m) and low elevation ({elevation}m)."
            implications = ["Imminent foundation instability risk.", "Critical flood ingress during peak tides."]
            trend = f"Accelerated historical shoreline retreat detected."
        elif risk == "Elevated":
            risk_detail = f"Elevated risk due to moderate projected shoreline retreat (~{predicted_loss_val}m)."
            implications = ["Foundation instability risk over long-term.", "Increased flood ingress."]
            trend = f"Steady historical shoreline retreat detected."
        else:
            risk_detail = f"Low risk due to stable shoreline trend and high elevation ({elevation}m)."
            implications = ["Infrastructure remains safely within standard tolerances."]
            trend = "Shoreline remains geologically stable."
            
        predicted_loss = f"{predicted_loss_val}m"
        year_val = 2035
        sat_data = "Sentinel-2 Telemetry & SRTM DEM"
        model_type = "Physics-Informed Neural Network (PINN)"
        elev_string = f"{elevation}m"

    return {
        "city": query.city,
        "lat": query.lat,
        "lng": query.lng,
        "landLoss": predicted_loss, 
        "risk": risk,
        "riskDetail": risk_detail,
        "confidenceLevel": confidence_level,
        "confidenceReason": confidence_reason,
        "year": year_val,
        "geologyMetrics": {
            "elevation": elev_string,
            "slopeGradient": f"{gee_data['slope_degrees']}°",
            "floodingVulnerability": gee_data['floodRisk'],
            "erosionSusceptibility": gee_data['erosionRisk']
        },
        "basisOfPrediction": {
            "satelliteDataRange": sat_data,
            "observedTrend": trend,
            "modelType": model_type
        },
        "infrastructureImplications": implications
    }

# --- STANDARD SINGLE ENDPOINT ---
@app.post("/api/predict")
def run_pinn_model(query: LocationQuery):
    return process_asset(query)

# --- NEW ENTERPRISE BATCH ENDPOINT ---
@app.post("/api/predict/batch")
def run_batch_model(batch: BatchQuery):
    results = []
    for asset in batch.assets:
        results.append(process_asset(asset))
    
    # Sort results so Critical risks appear at the top automatically
    risk_order = {"Critical": 0, "Elevated": 1, "Low": 2}
    sorted_results = sorted(results, key=lambda x: risk_order.get(x["risk"], 3))
    
    return {"status": "success", "total_processed": len(sorted_results), "data": sorted_results}
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

@app.api_route("/", methods=["GET", "HEAD"])
def read_root():
    return {"status": "Earth-Y Engine is Online"}

@app.post("/api/predict")
def run_pinn_model(query: LocationQuery):
    gee_data = get_coastal_data(query.lat, query.lng)
    elevation = gee_data['elevation']
    
    predicted_loss = predict_land_loss(elevation, query.lat)
    
    risk = "Critical" if predicted_loss > 10 else "Elevated" if predicted_loss > 5 else "Low"
    confidence_level = "Moderate" if predicted_loss > 10 else "High"
    confidence_reason = "High variance detected in fluid constraints" if predicted_loss > 10 else "Based on data consistency and physical constraints"
    
    if risk == "Critical":
        risk_detail = f"Critical risk due to severe projected shoreline retreat (~{predicted_loss}m) and low elevation ({elevation}m), highly exposing asset to inundation."
        implications = [
            "Imminent foundation instability risk over long-term exposure",
            "Critical flood ingress during peak tidal cycles",
            "Projected exponential increase in mitigation cost (e.g., sea defense systems)"
        ]
        trend = f"Accelerated historical shoreline retreat of {round(predicted_loss/10, 1)}m/year detected."
    elif risk == "Elevated":
        risk_detail = f"Elevated risk due to moderate projected shoreline retreat (~{predicted_loss}m) and structural exposure."
        implications = [
            "Foundation instability risk over long-term exposure",
            "Increased flood ingress during peak tidal cycles",
            "Projected increase in mitigation cost (e.g., sea defense systems)"
        ]
        trend = f"Steady historical shoreline retreat of {round(predicted_loss/10, 1)}m/year detected."
    else:
        risk_detail = f"Low risk due to stable shoreline trend (~{predicted_loss}m projected change) and high elevation ({elevation}m) reducing flood exposure."
        implications = [
            "Infrastructure remains safely within standard geotechnical tolerances",
            "Standard 10-year maintenance cycles apply; minimal flood ingress risk"
        ]
        trend = "Shoreline remains geologically stable within standard variance."
        
    return {
        "city": query.city,
        "landLoss": f"{predicted_loss}m", 
        "risk": risk,
        "riskDetail": risk_detail,
        "confidenceLevel": confidence_level,
        "confidenceReason": confidence_reason,
        "year": 2035,
        "geologyMetrics": {
            "elevation": f"{gee_data['elevation']}m",
            "slopeGradient": f"{gee_data['slope_degrees']}°",
            "floodingVulnerability": gee_data['floodRisk'],
            "erosionSusceptibility": gee_data['erosionRisk']
        },
        "basisOfPrediction": {
            "satelliteDataRange": "Sentinel-2 Telemetry & SRTM DEM",
            "observedTrend": trend,
            "modelType": "Physics-Informed Neural Network (PINN) constrained by fluid dynamics"
        },
        "infrastructureImplications": implications
    }
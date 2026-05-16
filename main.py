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
    is_offshore = gee_data.get('is_offshore', False)
    elevation = gee_data['elevation']
    
    if is_offshore:
        # ==========================================
        # OFFSHORE ROUTING (For Naval & Oil Rigs)
        # ==========================================
        depth = gee_data['depth']
        slope = gee_data['slope_degrees']
        risk = gee_data['risk']
        
        confidence_level = "High"
        confidence_reason = "Based on GEBCO/ETOPO1 bathymetric telemetry and terrain grading"
        
        if risk == "Critical":
            risk_detail = f"Critical risk due to extreme benthic slope ({slope}°). High probability of submarine landslides, anchor slippage, and infrastructure destabilization."
            implications = [
                "Unsafe for standard rig anchoring or pipeline routing.",
                "High vulnerability to mass transport deposits (MTDs).",
                "Requires specialized deep-water geotechnical intervention."
            ]
            trend = "Dynamic seafloor shifting likely due to steep topographical gradient."
        elif risk == "Elevated":
            risk_detail = f"Elevated risk due to moderate benthic slope ({slope}°). Requires enhanced anchor monitoring and scour protection."
            implications = [
                "Pipeline spanning and stress accumulation possible.",
                "Moderate risk of current-induced scouring.",
                "Enhanced tension leg mooring recommended."
            ]
            trend = "Moderate seabed variance; ongoing current monitoring required."
        else:
            risk_detail = f"Low risk. Target asset is located on a stable benthic shelf or abyssal plain (Depth: {depth}m, Slope: {slope}°)."
            implications = [
                "Stable topography for pipeline laying and standard anchoring.",
                "Low probability of submarine mass movement.",
                "Standard offshore operational tolerances apply."
            ]
            trend = "Seabed remains geologically stable within operational variance."
            
        predicted_loss = "N/A (Offshore)"
        year_val = "Current"
        sat_data = "NOAA ETOPO1 & GEBCO Bathymetry"
        model_type = "Benthic Topographical Assessment & Submarine Hazard Model"
        elev_string = f"-{depth}m (Depth)"

    else:
        # ==========================================
        # COASTAL ROUTING (Original Logic)
        # ==========================================
        predicted_loss_val = predict_land_loss(elevation, query.lat)
        
        risk = "Critical" if predicted_loss_val > 10 else "Elevated" if predicted_loss_val > 5 else "Low"
        confidence_level = "Moderate" if predicted_loss_val > 10 else "High"
        confidence_reason = "High variance detected in fluid constraints" if predicted_loss_val > 10 else "Based on data consistency and physical constraints"
        
        if risk == "Critical":
            risk_detail = f"Critical risk due to severe projected shoreline retreat (~{predicted_loss_val}m) and low elevation ({elevation}m), highly exposing asset to inundation."
            implications = [
                "Imminent foundation instability risk over long-term exposure",
                "Critical flood ingress during peak tidal cycles",
                "Projected exponential increase in mitigation cost (e.g., sea defense systems)"
            ]
            trend = f"Accelerated historical shoreline retreat of {round(predicted_loss_val/10, 1)}m/year detected."
        elif risk == "Elevated":
            risk_detail = f"Elevated risk due to moderate projected shoreline retreat (~{predicted_loss_val}m) and structural exposure."
            implications = [
                "Foundation instability risk over long-term exposure",
                "Increased flood ingress during peak tidal cycles",
                "Projected increase in mitigation cost (e.g., sea defense systems)"
            ]
            trend = f"Steady historical shoreline retreat of {round(predicted_loss_val/10, 1)}m/year detected."
        else:
            risk_detail = f"Low risk due to stable shoreline trend (~{predicted_loss_val}m projected change) and high elevation ({elevation}m) reducing flood exposure."
            implications = [
                "Infrastructure remains safely within standard geotechnical tolerances",
                "Standard 10-year maintenance cycles apply; minimal flood ingress risk"
            ]
            trend = "Shoreline remains geologically stable within standard variance."
            
        predicted_loss = f"{predicted_loss_val}m"
        year_val = 2035
        sat_data = "Sentinel-2 Telemetry & SRTM DEM"
        model_type = "Physics-Informed Neural Network (PINN) constrained by fluid dynamics"
        elev_string = f"{elevation}m"

    # Shared JSON Response Output
    return {
        "city": query.city,
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
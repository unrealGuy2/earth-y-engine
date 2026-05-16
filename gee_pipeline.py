import ee
from google.oauth2 import service_account

def initialize_ee():
    SCOPES = ['https://www.googleapis.com/auth/earthengine']
    credentials = service_account.Credentials.from_service_account_file(
        'gee-credentials.json', scopes=SCOPES
    )
    ee.Initialize(credentials)

def get_coastal_data(lat: float, lng: float):
    point = ee.Geometry.Point([lng, lat])
    
    # 1. Load the Ocean Data (NOAA ETOPO1 / GEBCO Bathymetry)
    etopo = ee.Image('NOAA/NGDC/ETOPO1').select('bedrock').rename('elevation')
    
    # 2. Load the Land Data (SRTM)
    srtm = ee.Image('USGS/SRTMGL1_003').rename('elevation')
    
    # 3. Fuse them together (SRTM overlays ETOPO where land exists)
    dem = ee.ImageCollection([etopo, srtm]).mosaic()
    
    slope = ee.Terrain.slope(dem)
    dem_with_slope = dem.addBands(slope)
    
    # Scale increased to 1000m to ensure we catch coarse ocean pixels
    sampled = dem_with_slope.sample(point, scale=1000)
    size = sampled.size().getInfo()
    
    if size > 0:
        first_feature = sampled.first()
        elevation = first_feature.get('elevation').getInfo()
        slope_val = first_feature.get('slope').getInfo()
    else:
        elevation = 0.0
        slope_val = 0.0
        
    is_offshore = elevation < 0

    if is_offshore:
        # --- OFFSHORE / NAVAL METRICS ---
        depth = abs(elevation)
        hazard_risk = "Severe (Submarine Landslide/Trench Risk)" if slope_val > 15 else "Moderate (Uneven Benthic Terrain)" if slope_val > 5 else "Low (Stable Abyssal/Shelf Plain)"
        benthic_risk = "High (Scouring/Current Erosion)" if slope_val > 10 else "Low (Stable Benthic Floor)"
        risk = "Critical" if slope_val > 15 else "Elevated" if slope_val > 5 else "Low"
        
        return {
            "is_offshore": True,
            "elevation": round(elevation, 1),
            "depth": round(depth, 1),
            "slope_degrees": round(slope_val, 1),
            "floodRisk": hazard_risk, 
            "erosionRisk": benthic_risk, 
            "risk": risk
        }
    else:
        # --- COASTAL / LAND METRICS ---
        flood_risk = "Severe (Inundation Likely)" if elevation < 3 else "Moderate (Storm Surge Vulnerable)" if elevation < 8 else "Low (Topographically Shielded)"
        erosion_risk = "High (Scarping/Undercutting)" if slope_val > 10 else "Moderate (Surface Erosion Processes)" if slope_val > 3 else "Low (Stable Gradient)"
        risk = "Critical" if elevation < 5 else "Elevated" if elevation < 15 else "Low"
        
        return {
            "is_offshore": False,
            "elevation": round(elevation, 1),
            "slope_degrees": round(slope_val, 1),
            "floodRisk": flood_risk,
            "erosionRisk": erosion_risk,
            "risk": risk
        }
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
    dem = ee.Image('USGS/SRTMGL1_003')
    slope = ee.Terrain.slope(dem)
    dem_with_slope = dem.addBands(slope)
    sampled = dem_with_slope.sample(point, 30)
    size = sampled.size().getInfo()
    
    if size > 0:
        first_feature = sampled.first()
        elevation = first_feature.get('elevation').getInfo()
        slope_val = first_feature.get('slope').getInfo()
    else:
        elevation = 0.0
        slope_val = 0.0
        
    flood_risk = "Severe (Inundation Likely)" if elevation < 3 else "Moderate (Storm Surge Vulnerable)" if elevation < 8 else "Low (Topographically Shielded)"
    erosion_risk = "High (Scarping/Undercutting)" if slope_val > 10 else "Moderate (Surface Wash)" if slope_val > 3 else "Low (Stable Gradient)"
    risk = "Critical" if elevation < 5 else "Elevated" if elevation < 15 else "Low"
    
    return {
        "elevation": round(elevation, 1),
        "slope_degrees": round(slope_val, 1),
        "floodRisk": flood_risk,
        "erosionRisk": erosion_risk,
        "risk": risk
    }
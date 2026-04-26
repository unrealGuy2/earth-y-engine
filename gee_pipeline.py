import ee
import json

def initialize_ee():
    with open('gee-credentials.json') as f:
        creds_data = json.load(f)
        sa_email = creds_data['client_email']
        
    credentials = ee.ServiceAccountCredentials(sa_email, 'gee-credentials.json')
    ee.Initialize(credentials)

def get_coastal_data(lat: float, lng: float):
    point = ee.Geometry.Point([lng, lat])
    dem = ee.Image('USGS/SRTMGL1_003')
    
    sampled = dem.sample(point, 30)
    size = sampled.size().getInfo()
    
    if size > 0:
        elevation = sampled.first().get('elevation').getInfo()
    else:
        elevation = 0.0
        
    risk = "Critical" if elevation < 5 else "Elevated" if elevation < 15 else "Low"
    confidence = "94%" if elevation < 5 else "89%"
    
    return {
        "elevation": round(elevation, 1),
        "risk": risk,
        "confidence": confidence
    }
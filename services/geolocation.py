from math import radians, sin, cos, sqrt, atan2

def valid_coordinates(latitude, longitude):
    try:
        lat, lon = float(latitude), float(longitude)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except (TypeError, ValueError):
        return False

def haversine_meters(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return 6371000 * 2 * atan2(sqrt(a), sqrt(max(0, 1-a)))

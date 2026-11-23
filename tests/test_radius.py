from services.geolocation import haversine_meters, valid_coordinates

def test_haversine_known_distance():
    distance = haversine_meters(12.9716, 77.5946, 12.9730, 77.5960)
    assert 180 < distance < 230

def test_coordinates_validation():
    assert valid_coordinates(12.9716, 77.5946)
    assert not valid_coordinates(91, 77)

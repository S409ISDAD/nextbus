from geopy import distance
from backend.services.tracking_confidence import track_location_similarity

def test_track_location_similarity():
    track = [[51.5074, -0.1278], [51.5075, -0.1279]]
    locations = [[51.5074, -0.1278], [51.5075, -0.1279]]

    result = track_location_similarity(track, locations)

    assert isinstance(result, float)
    assert result == 1.0

    track = [[51.5075, -0.1278], [51.5075, -0.1279]]
    locations = [[21.5074, -0.1278], [51.5072, -5.279]]

    result = track_location_similarity(track, locations)

    assert isinstance(result, float)
    assert result == 0.0

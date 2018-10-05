"""
Fake the places service.

This is copying a bunch of code from:
* https://github.int.llabs.io/llabs/ring.places_service/blob/master/places/controllers/places.py
* https://github.int.llabs.io/llabs/ring.places_service/blob/master/places/service.py
modifying as needed.

We have a list of places from overview, but other than that, this
functionality of the places service isn't explose through the gateway.
"""

from geopy.distance import distance


def get_nearest_place_at_info(places, lat, lon, accuracy_meters):
    """
    Given a list of places and a location (lat, lon, accuracy), return a tuple
    of the name of the nearest place, the distance to it, and whether or not
    we are at the place.

    Return a None tuple if there are no places.

    """
    min_distance = None
    nearest_place = None

    for place in places:
        dist = _calculate_distance(place_lat=place.lat, place_lon=place.lon,
                                   location_lat=lat, location_lon=lon)
        if min_distance is None or dist < min_distance:
            min_distance = dist
            nearest_place = place

    if nearest_place:
        at_place = is_at_place(location_lat=lat, location_lon=lon,
                               location_accuracy_meters=accuracy_meters,
                               place=nearest_place,
                               distance_meters=min_distance)
    else:
        at_place = False

    if nearest_place:
        name = nearest_place.name
    else:
        name = None

    return (name, min_distance, at_place)


def get_nearest_place_and_distance(places, lat, lon):
    """
    Get the nearest place, and the distance to a location, for a given group
    id, given the location.

    Return a None tuple if there are no places.
    """
    if not places:
        return (None, None)

    min_distance = None
    nearest_place = None

    print(f"places: {places}")
    for place in places:
        dist = _calculate_distance(place_lat=place.lat, place_lon=place.lon,
                                   location_lat=lat, location_lon=lon)
        print(f"({lat},{lon}) is {dist} from {place.name}")
        if min_distance is None or dist < min_distance:
            min_distance = dist
            nearest_place = place

    return (nearest_place, round(min_distance))


def _calculate_distance(place_lat: float, place_lon: float,
                        location_lat: float, location_lon: float) -> float:
    """
    Calculate the distance between a place and location using lat and lon.

    Place radius and location accuracy are not used for the calculation.

    :return: The distance, in meters
    """
    return distance((place_lat, place_lon),
                    (location_lat, location_lon)).meters


def is_at_place(location_lat, location_lon,
                location_accuracy_meters,
                place,
                distance_meters=None):
    """
    Is the given location at the given place.

    If supplied, the given distance between the location and place centers is
    assumed to be correct. If not supplied, it is calculated.

    :return: A boolean indicating if the location is at the place. Trinary
    results ("at", "near", "not at") are not supported.
    """
    if not distance_meters:
        distance_meters = _calculate_distance(
            place_lat=place.lat, place_lon=place.lon,
            location_lat=location_lat, location_lon=location_lon)

    return _is_at_place_overlapping_circles(
        location_accuracy_meters=location_accuracy_meters,
        place=place,
        distance_meters=distance_meters)


def _is_at_place_overlapping_circles(
        location_accuracy_meters,
        place,
        distance_meters) -> bool:
    """
    A simple implementation for determining whether a location is at a place.

    The criteria is whether or not the accuracy circle for the location and
    the radius circle for the place overlap at all. While simple, this is not
    the best implementation. It can lead to undesirable effects. e.g. Simply
    getting a location with bad accuracy can be enough to cause a far away
    location to now be considered "at" a place.

    :return: A boolean indicating if the location is at the place. Trinary
    results ("at", "near", "not at") are not supported.
    """
    return distance_meters <= location_accuracy_meters + place.radiusMeters

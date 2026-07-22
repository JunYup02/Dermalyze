"""Finds nearby hospitals/clinics via the OpenStreetMap Overpass API.

No API key required and no billing -- a deliberate tradeoff to avoid Google
Places API costs. In exchange, data is community-sourced and inconsistent:
not every clinic is mapped, and fields like phone/opening_hours are only
present when someone tagged them in OSM. We never fabricate a rating,
open/closed status, or business hours we can't back with real data -- if a
field isn't in OSM for a given place, it's just omitted.
"""
from __future__ import annotations

import math

import httpx
from fastapi import HTTPException

from app.schemas.hospitals import Hospital

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# hospital/clinic/doctors amenities, plus the newer healthcare=* tagging scheme.
OVERPASS_QUERY = """
[out:json][timeout:20];
(
  node["amenity"~"^(hospital|clinic|doctors)$"](around:{radius},{lat},{lng});
  way["amenity"~"^(hospital|clinic|doctors)$"](around:{radius},{lat},{lng});
  node["healthcare"~"^(hospital|clinic|doctor)$"](around:{radius},{lat},{lng});
  way["healthcare"~"^(hospital|clinic|doctor)$"](around:{radius},{lat},{lng});
);
out center tags 30;
"""
EARTH_RADIUS_M = 6371000


def _distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in meters (haversine)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def _format_address(tags: dict) -> str:
    parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:city") or tags.get("addr:district"),
    ]
    return " ".join(p for p in parts if p)


async def find_nearby(lat: float, lng: float, radius_m: float) -> list[Hospital]:
    query = OVERPASS_QUERY.format(radius=int(radius_m), lat=lat, lng=lng)
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(
                OVERPASS_URL,
                data={"data": query},
                headers={"User-Agent": "Dermalyze/1.0 (skin-health assessment app)"},
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Nearby clinic lookup failed: {exc}") from exc

    hospitals = []
    for el in response.json().get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue  # unnamed entries aren't useful to show

        if el["type"] == "node":
            place_lat, place_lng = el.get("lat"), el.get("lon")
        else:
            center = el.get("center") or {}
            place_lat, place_lng = center.get("lat"), center.get("lon")
        if place_lat is None or place_lng is None:
            continue

        hospitals.append(
            Hospital(
                name=name,
                address=_format_address(tags),
                lat=place_lat,
                lng=place_lng,
                distance_m=_distance_m(lat, lng, place_lat, place_lng),
                google_maps_url=f"https://www.google.com/maps/search/?api=1&query={place_lat},{place_lng}",
                phone=tags.get("phone") or tags.get("contact:phone"),
                opening_hours=tags.get("opening_hours"),
            )
        )

    hospitals.sort(key=lambda h: h.distance_m)
    return hospitals

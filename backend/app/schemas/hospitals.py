from pydantic import BaseModel


class Hospital(BaseModel):
    name: str
    address: str
    lat: float
    lng: float
    distance_m: float
    google_maps_url: str
    phone: str | None = None
    opening_hours: str | None = None

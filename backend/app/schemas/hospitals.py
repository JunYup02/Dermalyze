from pydantic import BaseModel


class Hospital(BaseModel):
    name: str
    address: str
    lat: float
    lng: float
    distance_m: float
    business_status: str | None = None
    google_maps_url: str
    rating: float | None = None
    user_rating_count: int | None = None
    open_now: bool | None = None
    weekday_hours: list[str] | None = None
    phone: str | None = None

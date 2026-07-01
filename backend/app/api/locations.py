from fastapi import APIRouter, Depends, Query

from app.config import Settings, get_settings
from app.services.places import PlacesService

router = APIRouter(prefix="/api/locations", tags=["locations"])


def get_places_service(settings: Settings = Depends(get_settings)) -> PlacesService:
    return PlacesService(settings.GOOGLE_PLACES_API_KEY)


@router.get("/autocomplete")
async def autocomplete(
    input: str = Query(..., min_length=1),
    places: PlacesService = Depends(get_places_service),
):
    predictions = await places.autocomplete(input)
    return {"predictions": predictions}


@router.get("/{place_id}/nearby")
async def get_nearby(
    place_id: str,
    lat: float = Query(...),
    lng: float = Query(...),
    places: PlacesService = Depends(get_places_service),
):
    nearby = await places.get_nearby(lat, lng)
    return {"places": nearby}


@router.get("/{place_id}/details")
async def get_place_details(
    place_id: str,
    places: PlacesService = Depends(get_places_service),
):
    details = await places.get_place_details(place_id)
    if not details:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Place not found")
    return details

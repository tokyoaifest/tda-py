from fastapi import APIRouter, HTTPException, Query
from app.models.responses import NearbySheltersResponse, ShelterResponse
from app.services.shelter_service import ShelterService

router = APIRouter()
shelter_service = ShelterService()


@router.get("/nearby", response_model=NearbySheltersResponse)
async def get_nearby_shelters(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    limit: int = Query(3, description="Number of shelters to return", le=10)
):
    """
    Get nearby emergency shelters.
    """
    if not (-90 <= lat <= 90):
        raise HTTPException(status_code=400, detail="Invalid latitude")
    if not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Invalid longitude")
    
    try:
        shelters = await shelter_service.find_nearby_shelters(lat, lon, limit)
        return NearbySheltersResponse(
            shelters=shelters,
            lat=lat,
            lon=lon
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding shelters: {str(e)}")
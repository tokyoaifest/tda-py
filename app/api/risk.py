from fastapi import APIRouter, HTTPException, Query
from app.models.responses import RiskScoreResponse
from app.services.risk_engine import RiskEngine

router = APIRouter()
risk_engine = RiskEngine()


@router.get("/score", response_model=RiskScoreResponse)
async def get_risk_score(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude")
):
    """
    Get entrapment risk score for a specific location.
    """
    if not (-90 <= lat <= 90):
        raise HTTPException(status_code=400, detail="Invalid latitude")
    if not (-180 <= lon <= 180):
        raise HTTPException(status_code=400, detail="Invalid longitude")
    
    try:
        result = await risk_engine.calculate_risk_score(lat, lon)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating risk: {str(e)}")


@router.get("/heatmap/tiles/{z}/{x}/{y}.pbf")
async def get_risk_tile(z: int, x: int, y: int):
    """
    Get vector tile for risk heatmap.
    """
    from app.services.tiler import TileService
    
    tile_service = TileService()
    try:
        tile_data = await tile_service.get_tile(z, x, y)
        return tile_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Tile not found: {str(e)}")
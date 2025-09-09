from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

router = APIRouter()


@router.get("/{z}/{x}/{y}.pbf")
async def get_tile(z: int, x: int, y: int):
    """
    Generic tile endpoint for serving vector tiles.
    """
    from app.services.tiler import TileService
    
    tile_service = TileService()
    try:
        tile_data = await tile_service.get_tile(z, x, y)
        return Response(
            content=tile_data,
            media_type="application/x-protobuf",
            headers={
                "Content-Encoding": "gzip",
                "Access-Control-Allow-Origin": "*"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Tile not found: {str(e)}")
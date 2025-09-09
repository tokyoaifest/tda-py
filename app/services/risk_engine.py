import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional

import geopandas as gpd
import numpy as np
from shapely.geometry import Point
from shapely.ops import nearest_points

from app.core.config import settings
from app.models.responses import RiskScoreResponse


class RiskEngine:
    def __init__(self):
        self.weights = self._load_weights()
        self._grid_data = None
        self._buildings_data = None
        self._hazard_data = None
        self._shelters_data = None
    
    def _load_weights(self) -> Dict[str, Any]:
        """Load risk calculation weights from config."""
        weights_path = settings.config_dir / "weights.json"
        try:
            with open(weights_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "weights": {
                    "population_density": 0.25,
                    "residential_unit_count": 0.20,
                    "building_stories": 0.15,
                    "hazard_liquefaction_rank": 0.25,
                    "flood_depth": 0.10,
                    "proximity_to_shelter": -0.05
                },
                "bands": {
                    "low": [0, 0.33],
                    "medium": [0.33, 0.67], 
                    "high": [0.67, 1.0]
                }
            }
    
    async def _load_data(self):
        """Load mock data files if not already loaded."""
        if self._grid_data is None:
            grid_path = settings.mock_dir / "grid_500m.geojson"
            if grid_path.exists():
                self._grid_data = gpd.read_file(grid_path)
            else:
                self._grid_data = gpd.GeoDataFrame()
        
        if self._buildings_data is None:
            buildings_path = settings.mock_dir / "buildings.geojson"
            if buildings_path.exists():
                self._buildings_data = gpd.read_file(buildings_path)
            else:
                self._buildings_data = gpd.GeoDataFrame()
        
        if self._hazard_data is None:
            hazard_path = settings.mock_dir / "hazard_liq.geojson"
            if hazard_path.exists():
                self._hazard_data = gpd.read_file(hazard_path)
            else:
                self._hazard_data = gpd.GeoDataFrame()
    
    async def calculate_risk_score(self, lat: float, lon: float) -> RiskScoreResponse:
        """Calculate entrapment risk score for a given location."""
        await self._load_data()
        
        point = Point(lon, lat)
        
        # Initialize risk factors
        factors = {
            "population_density": 0.0,
            "residential_unit_count": 0.0,
            "building_stories": 0.0,
            "hazard_liquefaction_rank": 0.0,
            "flood_depth": 0.0,
            "proximity_to_shelter": 0.0
        }
        
        contributors = []
        
        # Get grid cell data
        if not self._grid_data.empty:
            grid_cell = self._find_containing_cell(point, self._grid_data)
            if grid_cell is not None:
                factors["population_density"] = grid_cell.get("pop_density", 0.0) / 1000.0  # Normalize
                contributors.append({
                    "factor": "population_density",
                    "value": factors["population_density"],
                    "description": f"Population density: {grid_cell.get('pop_density', 0)}/km²"
                })
        
        # Get building data
        if not self._buildings_data.empty:
            nearby_buildings = self._get_nearby_buildings(point, self._buildings_data, radius_m=100)
            if len(nearby_buildings) > 0:
                residential_count = len(nearby_buildings[nearby_buildings.get("use", "") == "residential"])
                avg_stories = nearby_buildings.get("levels", 1).mean()
                
                factors["residential_unit_count"] = min(residential_count / 10.0, 1.0)  # Normalize
                factors["building_stories"] = min(avg_stories / 20.0, 1.0)  # Normalize
                
                contributors.extend([
                    {
                        "factor": "residential_unit_count", 
                        "value": factors["residential_unit_count"],
                        "description": f"Residential buildings: {residential_count}"
                    },
                    {
                        "factor": "building_stories",
                        "value": factors["building_stories"], 
                        "description": f"Average stories: {avg_stories:.1f}"
                    }
                ])
        
        # Get hazard data
        if not self._hazard_data.empty:
            hazard = self._find_containing_cell(point, self._hazard_data)
            if hazard is not None:
                liq_rank = hazard.get("liq_rank", 1)
                factors["hazard_liquefaction_rank"] = liq_rank / 5.0  # Assuming rank 1-5
                contributors.append({
                    "factor": "hazard_liquefaction_rank",
                    "value": factors["hazard_liquefaction_rank"],
                    "description": f"Liquefaction risk: {liq_rank}/5"
                })
        
        # Calculate proximity to nearest shelter (mock)
        shelter_distance = 500.0  # Mock distance in meters
        factors["proximity_to_shelter"] = min(shelter_distance / 1000.0, 1.0)  # Normalize to km
        contributors.append({
            "factor": "proximity_to_shelter",
            "value": factors["proximity_to_shelter"],
            "description": f"Distance to shelter: {shelter_distance}m"
        })
        
        # Calculate weighted risk score
        risk_score = 0.0
        weights = self.weights["weights"]
        for factor, value in factors.items():
            if factor in weights:
                risk_score += weights[factor] * value
        
        # Normalize to 0-1 range
        risk_score = max(0.0, min(1.0, risk_score))
        
        # Determine risk band
        band = self._get_risk_band(risk_score)
        
        # Sort contributors by impact
        contributors.sort(key=lambda x: abs(x["value"] * weights.get(x["factor"], 0)), reverse=True)
        
        return RiskScoreResponse(
            risk_score=risk_score,
            band=band,
            top_contributors=contributors[:5],
            lat=lat,
            lon=lon
        )
    
    def _find_containing_cell(self, point: Point, gdf: gpd.GeoDataFrame) -> Optional[Dict]:
        """Find the cell that contains the given point."""
        if gdf.empty:
            return None
        
        try:
            # Ensure CRS compatibility
            if gdf.crs is None:
                gdf = gdf.set_crs("EPSG:4326")
            
            containing = gdf[gdf.contains(point)]
            if not containing.empty:
                return containing.iloc[0].to_dict()
        except Exception:
            pass
        
        return None
    
    def _get_nearby_buildings(self, point: Point, buildings_gdf: gpd.GeoDataFrame, radius_m: float = 100) -> gpd.GeoDataFrame:
        """Get buildings within radius of point."""
        if buildings_gdf.empty:
            return gpd.GeoDataFrame()
        
        try:
            # Simple distance filter (approximate)
            nearby = buildings_gdf[
                buildings_gdf.geometry.distance(point) < (radius_m / 111000.0)  # Rough meters to degrees
            ]
            return nearby
        except Exception:
            return gpd.GeoDataFrame()
    
    def _get_risk_band(self, risk_score: float) -> str:
        """Determine risk band based on score."""
        bands = self.weights.get("bands", {
            "low": [0, 0.33],
            "medium": [0.33, 0.67],
            "high": [0.67, 1.0]
        })
        
        for band, (low, high) in bands.items():
            if low <= risk_score < high:
                return band
        
        return "high"  # Default for score >= 1.0
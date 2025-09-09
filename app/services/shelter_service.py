import math
from typing import List
from shapely.geometry import Point

from app.models.responses import ShelterResponse


class ShelterService:
    def __init__(self):
        # Mock shelter data for Tokyo wards
        self.mock_shelters = [
            {
                "id": "shelter_001",
                "name": "Tokyo Metropolitan Gymnasium",
                "lat": 35.6762,
                "lon": 139.7116,
                "capacity": 5000
            },
            {
                "id": "shelter_002", 
                "name": "Shibuya City Community Center",
                "lat": 35.6598,
                "lon": 139.7006,
                "capacity": 2500
            },
            {
                "id": "shelter_003",
                "name": "Shinjuku Park Hyatt Emergency Center",
                "lat": 35.6935,
                "lon": 139.6917,
                "capacity": 3000
            },
            {
                "id": "shelter_004",
                "name": "Minato Ward Civic Center",
                "lat": 35.6584,
                "lon": 139.7519,
                "capacity": 1800
            },
            {
                "id": "shelter_005",
                "name": "Chiyoda Ward Emergency Facility",
                "lat": 35.6938,
                "lon": 139.7531,
                "capacity": 2200
            },
            {
                "id": "shelter_006",
                "name": "Taito Cultural Center",
                "lat": 35.7139,
                "lon": 139.7794,
                "capacity": 1500
            }
        ]
    
    async def find_nearby_shelters(self, lat: float, lon: float, limit: int = 3) -> List[ShelterResponse]:
        """Find nearby emergency shelters."""
        user_point = Point(lon, lat)
        
        # Calculate distances and create shelter responses
        shelters_with_distance = []
        for shelter in self.mock_shelters:
            shelter_point = Point(shelter["lon"], shelter["lat"])
            distance_km = self._calculate_distance(user_point, shelter_point)
            
            shelters_with_distance.append({
                **shelter,
                "distance_km": distance_km
            })
        
        # Sort by distance and limit results
        shelters_with_distance.sort(key=lambda x: x["distance_km"])
        nearest_shelters = shelters_with_distance[:limit]
        
        # Convert to response models
        return [
            ShelterResponse(
                id=shelter["id"],
                name=shelter["name"],
                lat=shelter["lat"],
                lon=shelter["lon"],
                distance_km=round(shelter["distance_km"], 2),
                capacity=shelter["capacity"]
            )
            for shelter in nearest_shelters
        ]
    
    def _calculate_distance(self, point1: Point, point2: Point) -> float:
        """Calculate distance between two points in kilometers using haversine formula."""
        lat1, lon1 = point1.y, point1.x
        lat2, lon2 = point2.y, point2.x
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        
        return r * c
# Tokyo Disaster Entrapment Anticipation (MVP)

A FastAPI backend and MapLibre web application for computing and visualizing tile-based "Entrapment Risk" scores for Tokyo wards. This MVP supports local mode with sample GeoJSON data and prebuilt PMTiles, with future support for PostGIS spatial joins.

## 🚀 Quick Start (Local Mode)

1. **Install Dependencies**
   ```bash
   pip install -e .
   ```

2. **Run the Application**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   Or using the Makefile:
   ```bash
   make dev
   ```

3. **Access the Application**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📡 API Endpoints

### Core Endpoints

- **`GET /health`** - Health check
  ```bash
  curl http://localhost:8000/health
  ```

- **`GET /config`** - Runtime configuration
  ```bash
  curl http://localhost:8000/config
  ```

### Risk Assessment

- **`GET /risk/score?lat={lat}&lon={lon}`** - Get entrapment risk score for location
  ```bash
  curl "http://localhost:8000/risk/score?lat=35.6598&lon=139.7006"
  ```
  
  Response:
  ```json
  {
    "risk_score": 0.67,
    "band": "medium",
    "top_contributors": [
      {
        "factor": "population_density",
        "value": 0.85,
        "description": "Population density: 12000/km²"
      }
    ],
    "lat": 35.6598,
    "lon": 139.7006
  }
  ```

- **`GET /risk/heatmap/tiles/{z}/{x}/{y}.pbf`** - Vector tiles for risk heatmap
  ```bash
  curl "http://localhost:8000/risk/heatmap/tiles/12/3638/1612.pbf"
  ```

### Shelters

- **`GET /shelters/nearby?lat={lat}&lon={lon}&limit={limit}`** - Find nearby shelters
  ```bash
  curl "http://localhost:8000/shelters/nearby?lat=35.6598&lon=139.7006&limit=3"
  ```

## 🗺️ Web Interface Features

- **Interactive Map**: MapLibre GL JS with OpenStreetMap tiles
- **Risk Visualization**: Color-coded grid cells showing entrapment risk levels
- **Click-to-Query**: Click anywhere on the map to get detailed risk assessment
- **Layer Controls**: Toggle buildings and hazard overlays
- **Mode Toggle**: Switch between Local and Database modes
- **PWA Support**: Offline-capable with service worker

## 🧮 Risk Calculation

The entrapment risk score is calculated using a weighted formula:

```
EntrapmentRisk = w1×pop_density + w2×residential_units + w3×building_stories + 
                 w4×hazard_liq_rank + w5×flood_depth - w6×proximity_to_shelter
```

### Default Weights (config/weights.json)
- Population density: 25%
- Residential unit count: 20%
- Building stories: 15%
- Hazard liquefaction rank: 25%
- Flood depth: 10%
- Proximity to shelter: -5% (closer is better)

### Risk Bands
- **Low Risk**: 0-33% (🟢)
- **Medium Risk**: 33-67% (🟠)
- **High Risk**: 67-100% (🔴)

## 📊 Data

### Mock Data Files
- `data/mock/grid_500m.geojson` - 500m grid cells with population data
- `data/mock/buildings.geojson` - Building footprints with attributes
- `data/mock/hazard_liq.geojson` - Liquefaction hazard zones

### Sample Coverage
- 5 grid cells covering parts of Shibuya, Shinjuku, Chiyoda, and Minato wards
- 7 building samples with varying heights and uses
- 4 hazard zones with different liquefaction risk levels

## 🔧 Scripts & Tools

### Compute Risk Scores
```bash
make compute
# or
python scripts/compute_risk.py
```
Performs spatial joins and computes risk scores, outputs to `data/computed/risk_grid.geojson`.

### Build Vector Tiles (requires tippecanoe)
```bash
make tiles
# or
python scripts/build_tiles.py
```

### Serve PMTiles
```bash
python scripts/serve_pmtiles.py
```

### Run Tests
```bash
make test
# or
pytest tests/ -v
```

## 🐳 Environment Configuration

Copy `.env.sample` to `.env` and modify as needed:

```bash
MODE=local
PORT=8000
DB_URL=postgresql://user:pass@host:5432/disaster
TILES_PATH=./data/tiles/risk.pmtiles
```

## 🔄 Switching to PostGIS Mode

To use with a PostGIS database in the future:

1. Set up PostGIS database with spatial data
2. Update `DB_URL` in `.env`
3. Set `MODE=postgis`
4. Modify `app/services/risk_engine.py` to use database queries instead of GeoJSON files

## 📁 Project Structure

```
.
├─ app/
│  ├─ main.py                  # FastAPI application
│  ├─ api/                     # API endpoints
│  │  ├─ risk.py              # Risk assessment endpoints  
│  │  ├─ tiles.py             # Tile serving
│  │  └─ shelters.py          # Shelter lookup
│  ├─ core/config.py          # Configuration management
│  ├─ services/               # Business logic
│  │  ├─ risk_engine.py       # Risk calculation
│  │  ├─ tiler.py            # Tile serving
│  │  └─ shelter_service.py   # Shelter lookup
│  └─ models/                 # Pydantic models
├─ web/
│  ├─ index.html              # Main web interface
│  ├─ manifest.json           # PWA manifest
│  └─ sw.js                   # Service worker
├─ data/
│  ├─ mock/                   # Sample GeoJSON data
│  ├─ tiles/                  # PMTiles output
│  └─ computed/               # Processed data
├─ config/
│  └─ weights.json            # Risk calculation weights
├─ scripts/
│  ├─ compute_risk.py         # Risk computation
│  ├─ build_tiles.py          # Tile generation
│  └─ serve_pmtiles.py        # PMTiles server
└─ tests/                     # Test suite
```

## 🧪 Development

### Install Development Dependencies
```bash
pip install -e ".[dev]"
```

### Code Quality
```bash
black .                       # Format code
flake8 .                     # Lint code  
mypy app/                    # Type checking
```

### Running on Replit
The project includes `.replit` and `replit.nix` configuration files for easy deployment on Replit. Simply import the repository and click "Run".

## 📝 API Examples

### Tokyo Locations to Test

| Location | Latitude | Longitude | Expected Risk |
|----------|----------|-----------|---------------|
| Shibuya Station | 35.6598 | 139.7006 | Medium-High |
| Shinjuku | 35.6895 | 139.6917 | Medium |
| Imperial Palace | 35.6938 | 139.7531 | Low-Medium |
| Tokyo Station | 35.6812 | 139.7671 | Medium |

### Sample API Call
```bash
# Get risk assessment for Shibuya
curl -X GET "http://localhost:8000/risk/score?lat=35.6598&lon=139.7006" \
     -H "accept: application/json"

# Find nearby shelters
curl -X GET "http://localhost:8000/shelters/nearby?lat=35.6598&lon=139.7006&limit=3" \
     -H "accept: application/json"
```

## 🚀 Deployment

### Local Development
```bash
make dev
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
```

## 📋 TODO: Future Enhancements

- [ ] PostGIS integration for real spatial data
- [ ] Real-time disaster data feeds
- [ ] ML-based risk prediction models
- [ ] Historical disaster correlation analysis
- [ ] Mobile app version
- [ ] Multi-language support
- [ ] Advanced caching strategies

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `make test`
5. Submit a pull request

---

**Note**: This is an MVP for demonstration purposes. For production use, integrate with real disaster data sources and conduct thorough validation of risk models.
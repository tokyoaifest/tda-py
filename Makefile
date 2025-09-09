.PHONY: dev compute tiles test install clean

dev:
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port ${PORT:-8000}

compute:
	python scripts/compute_risk.py

tiles:
	@if command -v tippecanoe >/dev/null 2>&1; then \
		python scripts/build_tiles.py; \
	else \
		echo "tippecanoe not found, skipping tile generation"; \
	fi

test:
	pytest tests/ -v

install:
	pip install -e .

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
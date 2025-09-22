# Airports API (Layered) — FastAPI + SQLAlchemy + Alembic

Capas:
- **api** (FastAPI routers)
- **services** (reglas de negocio)
- **repositories** (SQLAlchemy ORM/Core)
- **models** (tablas/entidades)
- **domain** (Pydantic DTOs)
- **ingest** (parseo/normalización de CSV)
- **core** (config/utilidades)
- **db** (engine/session + Alembic)
- **middleware** (timing/audit)

## Quickstart (Docker)
```bash
docker compose up --build -d
docker compose exec api alembic -c app/db/alembic.ini revision --autogenerate -m "init"
docker compose exec api alembic -c app/db/alembic.ini upgrade head
# Swagger: http://localhost:8000/docs
```

## Endpoints
- `POST /ingest/airlines` (CSV con: name,iata,icao,country)
- `POST /ingest/routes`   (CSV con: airline_iata,origin_iata,destination_iata,capacity,occupancy,flight_date)
- `GET  /analytics/average-occupancy?start=&end=`
- `GET  /analytics/domestic-altitude-percentage?min_occupancy=`
- `GET  /analytics/top-routes-by-country?country=Argentina&start=2023-01-01&end=2023-01-31`

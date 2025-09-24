# ✈️ Airport Analytics Challenge

Este proyecto es una API construida con **FastAPI** y **PostgreSQL**, pensada para trabajar con datos de aeropuertos, aerolíneas y rutas.  
La idea es poder **cargar información desde archivos** (CSV/JSON) y después exponer **consultas de análisis** como ocupación promedio, rutas más utilizadas o detección de vuelos con alta ocupación en días consecutivos.

---

## 🚀 Tecnologías que usé

- **Python 3.11**
- **FastAPI** para la API
- **SQLAlchemy 2.0** como ORM
- **Alembic** para manejar migraciones de base de datos
- **PostgreSQL 16** como motor de base
- **Docker y Docker Compose** para que sea fácil de levantar en cualquier máquina
- **Pytest** para tests automatizados(NTH)
- **Pandas** para procesar datos en la ingesta

---

## 📂 Estructura del proyecto

```
app/
├─ main.py                # entrada de la API
├─ api/routers/           # endpoints agrupados por tema (ingest, analytics)
├─ models/                # modelos SQLAlchemy
├─ schemas/               # validaciones con Pydantic
├─ repositories/          # consultas a la DB (AirportsRepo, Analytics, etc.)
├─ middleware/            # middlewares (ej. auditoría de requests)
└─ db/                    # alembic.ini y migraciones
tests/                    # suite de tests con pytest
docker-compose.yml        # definición de servicios
requirements.txt          # dependencias
```

---

## 🐳 Cómo levantarlo

1. Clonar el repo y levantar los contenedores:
   ```bash
   docker compose up --build
   ```

2. Esto arranca:
   - `db`: Postgres
   - `migrate`: corre `alembic upgrade head` para crear las tablas
   - `api`: la API en `http://localhost:8000`

3. La API ya queda lista para usar.

---

## 📖 Endpoints principales

### Ingesta de datos
- `POST /ingest/airports` → carga aeropuertos  
- `POST /ingest/airlines` → carga aerolíneas  
- `POST /ingest/routes` → carga rutas/vuelos  

### Analítica
- `GET /analytics/consecutive-high-occupancy`  
  Detecta rutas con ocupación ≥ umbral en días consecutivos.  
- `GET /analytics/top-routes-by-country`  
  Devuelve las rutas más voladas de un país (se puede filtrar por fechas y elegir si mirar origen, destino o ambos).  
- `GET /analytics/airline-occupancy`  
  Calcula el promedio de ocupación de cada aerolínea, ponderado por capacidad.  

### Otros
- `GET /healthz` → chequeo rápido  
- `GET /docs` → Swagger UI  
- `GET /redoc` → ReDoc  

---

## 🛢️ Migraciones de base de datos

El proyecto usa **Alembic**.  
Ya está todo configurado para que las migraciones se apliquen solas cuando corrés `docker compose up`.  

Si querés hacerlo manualmente:
```bash
# crear una nueva migración (si cambian los modelos)
docker compose exec api alembic -c app/db/alembic.ini revision --autogenerate -m "mensaje"

# aplicar la última versión
docker compose exec api alembic -c app/db/alembic.ini upgrade head
```

---

## 🧪 Tests

Los tests están hechos con **pytest**. Cubren:
- Validación de schemas Pydantic
- Repositorio de aeropuertos (upsert “último gana”)
- Endpoints de analítica (con datos de ejemplo)

### Cómo correrlos
Primero crear la base de datos de test:
```bash
docker compose exec db sh -lc 'psql -U app -d postgres -c "CREATE DATABASE airports_test;"'
```

Después:
```bash
docker compose exec api pytest -q
```

Con cobertura:
```bash
docker compose exec api pytest --maxfail=1 --disable-warnings --cov=app -q
```

---

## ⚙️ Middleware de auditoría

Agregué un middleware que mide el **tiempo de cada request** y lo guarda en la tabla `audit_logs`.  
Registra: método, path, status, timestamps, duración en ms, IP del cliente y user-agent.  

Sirve para tener trazabilidad y ver qué endpoints son más costosos.

---

## 📝 Notas finales

- Podés probar subiendo tus propios CSVs con aeropuertos, aerolíneas y rutas.  
- Los validadores de Pydantic normalizan valores raros como `"NaN"`, `"Inf"` o `"123,45"`.  
- El proyecto está organizado en capas (routers → repos → modelos) para que sea más fácil de mantener.  
- Con Docker Compose, cualquiera lo puede levantar en su máquina sin configuraciones extras.  

---

👨‍💻 Proyecto desarrollado como parte de un challenge técnico.

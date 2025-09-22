# from __future__ import annotations
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models import AuditLog

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0
        try:
            db: Session = SessionLocal()
            db.add(AuditLog(method=request.method, path=request.url.path, status_code=response.status_code, duration_ms=duration_ms))
            db.commit()
        except Exception:
            pass
        finally:
            try:
                db.close()
            except Exception:
                pass
        return response

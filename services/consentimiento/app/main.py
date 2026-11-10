"""Microservicio de Consentimiento Open Finance (FastAPI).

Base compartida: modelo de datos y /health. Es el unico dueño del estado del
consentimiento (database per service). Aqui NO estan los endpoints de otorgar,
revocar ni consultar, ni el audit_log: los agrega EXP-007 (revocacion efectiva).
"""
import os
import time
import uuid

from fastapi import FastAPI
from sqlalchemy import String, Uuid, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

SERVICE_NAME = os.getenv("SERVICE_NAME", "consentimiento")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/consentimiento_db"
)

ESTADO_ACTIVO = "activo"
ESTADO_REVOCADO = "revocado"

engine = create_engine(DATABASE_URL, pool_size=int(os.getenv("DB_POOL_MAX", "10")), pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class Consentimiento(Base):
    __tablename__ = "consentimientos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fuente: Mapped[str] = mapped_column(String)  # ej. Open Finance
    alcance: Mapped[str] = mapped_column(String)  # scope de datos autorizados
    estado: Mapped[str] = mapped_column(String, default=ESTADO_ACTIVO)  # activo | revocado
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid)


app = FastAPI(title="Solventa - Consentimiento Open Finance")


@app.on_event("startup")
def iniciar() -> None:
    # La BD puede tardar unos segundos en aceptar conexiones: se reintenta.
    for intento in range(20):
        try:
            Base.metadata.create_all(engine)
            break
        except OperationalError:
            if intento == 19:
                raise
            time.sleep(2)


@app.get("/health")
def health():
    # Liveness: no toca BD ni dependencias externas.
    return {"status": "ok", "servicio": SERVICE_NAME}

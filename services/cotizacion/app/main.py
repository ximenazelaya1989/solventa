"""Microservicio de Cotizacion (FastAPI).

Base compartida: calcula la prima = prima del producto ajustada por el score de
riesgo que devuelve Perfilamiento (REST). BD propia (cotizacion_db). Aqui NO hay
tacticas de resiliencia ni de seguridad: cada experimento agrega las suyas.
"""
import os
import time
import uuid

import httpx
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Float, Uuid, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

SERVICE_NAME = os.getenv("SERVICE_NAME", "cotizacion")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/cotizacion_db"
)
PERFILAMIENTO_URL = os.getenv("PERFILAMIENTO_URL", "http://localhost:8002")
PERFILAMIENTO_TIMEOUT_S = float(os.getenv("PERFILAMIENTO_TIMEOUT_S", "2.0"))

PRODUCTO_DEMO = uuid.UUID("22222222-2222-2222-2222-222222222222")

engine = create_engine(DATABASE_URL, pool_size=int(os.getenv("DB_POOL_MAX", "10")), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
http = httpx.Client(timeout=PERFILAMIENTO_TIMEOUT_S)


class Base(DeclarativeBase):
    pass


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    prima: Mapped[float] = mapped_column(Float)


class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    prima: Mapped[float] = mapped_column(Float)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    producto_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    socio_distribucion_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    perfil_riesgo_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class CotizacionIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    cliente_id: uuid.UUID = Field(alias="clienteId")
    producto_id: uuid.UUID = Field(alias="productoId")
    socio_distribucion_id: uuid.UUID | None = Field(default=None, alias="socioDistribucionId")


class CotizacionOut(BaseModel):
    id: uuid.UUID
    prima: float
    clienteId: uuid.UUID
    productoId: uuid.UUID
    perfilRiesgoId: uuid.UUID | None
    score: float


def get_db():
    with SessionLocal() as db:
        yield db


app = FastAPI(title="Solventa - Cotizacion")


@app.on_event("startup")
def iniciar() -> None:
    for intento in range(20):
        try:
            Base.metadata.create_all(engine)
            break
        except OperationalError:
            if intento == 19:
                raise
            time.sleep(2)
    with SessionLocal() as db:  # un producto demo para probar la cadena completa
        if db.get(Producto, PRODUCTO_DEMO) is None:
            db.add(Producto(id=PRODUCTO_DEMO, prima=150.0))
            db.commit()


@app.get("/health")
def health():
    # Liveness: no toca BD ni dependencias externas.
    return {"status": "ok", "servicio": SERVICE_NAME}


@app.post("/cotizaciones", response_model=CotizacionOut, status_code=201)
def cotizar(datos: CotizacionIn, db: Session = Depends(get_db)):
    producto = db.get(Producto, datos.producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Llamada sincrona a Perfilamiento. Sin proteccion adicional (base compartida).
    try:
        r = http.get(f"{PERFILAMIENTO_URL}/perfiles/{datos.cliente_id}")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Perfilamiento no disponible")
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Cliente sin perfil de riesgo")
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail="Error en Perfilamiento")
    perfil = r.json()

    score = float(perfil["score"])
    prima = round(producto.prima * (1 + (100 - score) / 200), 2)  # score 70 -> +15 %

    cot = Cotizacion(
        prima=prima,
        cliente_id=datos.cliente_id,
        producto_id=datos.producto_id,
        socio_distribucion_id=datos.socio_distribucion_id,
        perfil_riesgo_id=uuid.UUID(perfil["id"]),
    )
    db.add(cot)
    db.commit()
    return CotizacionOut(
        id=cot.id,
        prima=cot.prima,
        clienteId=cot.cliente_id,
        productoId=cot.producto_id,
        perfilRiesgoId=cot.perfil_riesgo_id,
        score=score,
    )

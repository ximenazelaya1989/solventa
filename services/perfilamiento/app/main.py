"""Microservicio de Perfilamiento (FastAPI).

Base compartida: devuelve el perfil de riesgo de un cliente desde su propia BD
(perfilamiento_db). Aqui NO hay timeout hacia Open Finance, circuit breaker,
bulkhead ni cache: esas tacticas las agrega EXP-009 en su propio trabajo.
"""
import os
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import JSON, Float, Uuid, create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

SERVICE_NAME = os.getenv("SERVICE_NAME", "perfilamiento")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/perfilamiento_db"
)

CLIENTE_DEMO = uuid.UUID("11111111-1111-1111-1111-111111111111")

engine = create_engine(DATABASE_URL, pool_size=int(os.getenv("DB_POOL_MAX", "10")), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class PerfilRiesgo(Base):
    __tablename__ = "perfiles_riesgo"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True)
    score: Mapped[float] = mapped_column(Float)
    senales_open_finance: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class PerfilIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    cliente_id: uuid.UUID = Field(alias="clienteId")
    score: float = Field(ge=0, le=100)
    senales_open_finance: dict | None = Field(default=None, alias="senalesOpenFinance")


class PerfilOut(BaseModel):
    id: uuid.UUID
    clienteId: uuid.UUID
    score: float
    senalesOpenFinance: dict | None = None


def a_salida(p: PerfilRiesgo) -> PerfilOut:
    return PerfilOut(
        id=p.id, clienteId=p.cliente_id, score=p.score, senalesOpenFinance=p.senales_open_finance
    )


def get_db():
    with SessionLocal() as db:
        yield db


app = FastAPI(title="Solventa - Perfilamiento")


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
    with SessionLocal() as db:  # un cliente demo para probar la cadena completa
        if db.scalar(select(PerfilRiesgo).where(PerfilRiesgo.cliente_id == CLIENTE_DEMO)) is None:
            db.add(PerfilRiesgo(cliente_id=CLIENTE_DEMO, score=70, senales_open_finance={"origen": "seed"}))
            db.commit()


@app.get("/health")
def health():
    # Liveness: no toca BD ni dependencias externas.
    return {"status": "ok", "servicio": SERVICE_NAME}


@app.get("/perfiles/{cliente_id}", response_model=PerfilOut)
def obtener_perfil(cliente_id: uuid.UUID, db: Session = Depends(get_db)):
    perfil = db.scalar(select(PerfilRiesgo).where(PerfilRiesgo.cliente_id == cliente_id))
    if perfil is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return a_salida(perfil)


@app.post("/perfiles", response_model=PerfilOut, status_code=201)
def crear_perfil(datos: PerfilIn, db: Session = Depends(get_db)):
    if db.scalar(select(PerfilRiesgo).where(PerfilRiesgo.cliente_id == datos.cliente_id)):
        raise HTTPException(status_code=409, detail="El cliente ya tiene perfil")
    perfil = PerfilRiesgo(
        cliente_id=datos.cliente_id, score=datos.score, senales_open_finance=datos.senales_open_finance
    )
    db.add(perfil)
    db.commit()
    return a_salida(perfil)

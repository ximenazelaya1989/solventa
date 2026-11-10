"""Microservicio de Consentimiento Open Finance (FastAPI).

Es el unico dueño del estado del consentimiento (database per service).

EXP-007 (revocacion efectiva, HU3.2.1) agrega:
  - otorgar, revocar y consultar el consentimiento vigente;
  - audit_log de otorgamientos, revocaciones y accesos negados. El cambio de
    estado y su registro de auditoria se guardan en la MISMA transaccion, asi
    que no puede quedar una revocacion sin registro;
  - JWT + RBAC en todos los endpoints de negocio (ver seguridad.py).
"""
import logging
import os
import time
import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Index, String, Uuid, create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from .seguridad import ROL_AUDITOR, ROL_CLIENTE, ROL_SERVICIO, Actor, requiere

SERVICE_NAME = os.getenv("SERVICE_NAME", "consentimiento")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/consentimiento_db"
)

ESTADO_ACTIVO = "activo"
ESTADO_REVOCADO = "revocado"
FUENTE_OPEN_FINANCE = "open_finance"

EVENTO_OTORGADO = "OTORGADO"
EVENTO_REVOCADO = "REVOCADO"
EVENTO_ACCESO_NEGADO = "ACCESO_NEGADO"

log = logging.getLogger("consentimiento")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

_opciones_engine = {"pool_pre_ping": True}
if not DATABASE_URL.startswith("sqlite"):
    _opciones_engine["pool_size"] = int(os.getenv("DB_POOL_MAX", "10"))
engine = create_engine(DATABASE_URL, **_opciones_engine)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def ahora() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Consentimiento(Base):
    __tablename__ = "consentimientos"
    __table_args__ = (Index("ix_consentimientos_cliente_fuente", "cliente_id", "fuente"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fuente: Mapped[str] = mapped_column(String)  # ej. open_finance
    alcance: Mapped[str] = mapped_column(String)  # scope de datos autorizados
    estado: Mapped[str] = mapped_column(String, default=ESTADO_ACTIVO)  # activo | revocado
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    fecha_otorgamiento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_revocacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RegistroAuditoria(Base):
    """Pista de auditoria (solo se inserta, nunca se actualiza ni se borra)."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora, index=True)
    evento: Mapped[str] = mapped_column(String)  # OTORGADO | REVOCADO | ACCESO_NEGADO
    cliente_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    consentimiento_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    actor: Mapped[str] = mapped_column(String)  # sub del JWT que hizo la accion
    detalle: Mapped[str | None] = mapped_column(String, nullable=True)


# ---------- DTOs ----------


class OtorgarIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    cliente_id: uuid.UUID = Field(alias="clienteId")
    fuente: str = FUENTE_OPEN_FINANCE
    alcance: str = "senales_financieras"


class ConsentimientoOut(BaseModel):
    id: uuid.UUID
    clienteId: uuid.UUID
    fuente: str
    alcance: str
    estado: str
    fechaOtorgamiento: datetime | None
    fechaRevocacion: datetime | None


class VigenteOut(BaseModel):
    clienteId: uuid.UUID
    fuente: str
    vigente: bool
    consentimientoId: uuid.UUID | None = None
    alcance: str | None = None


class AccesoNegadoIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    cliente_id: uuid.UUID = Field(alias="clienteId")
    motivo: str


class AuditoriaOut(BaseModel):
    id: uuid.UUID
    fecha: datetime
    evento: str
    clienteId: uuid.UUID
    consentimientoId: uuid.UUID | None
    actor: str
    detalle: str | None


def a_salida(c: Consentimiento) -> ConsentimientoOut:
    return ConsentimientoOut(
        id=c.id,
        clienteId=c.cliente_id,
        fuente=c.fuente,
        alcance=c.alcance,
        estado=c.estado,
        fechaOtorgamiento=c.fecha_otorgamiento,
        fechaRevocacion=c.fecha_revocacion,
    )


def get_db():
    with SessionLocal() as db:
        yield db


def exigir_dueno(actor: Actor, cliente_id: uuid.UUID) -> None:
    """Un cliente solo puede otorgar o revocar SUS consentimientos."""
    if actor.sub != str(cliente_id):
        raise HTTPException(403, "Solo el titular puede gestionar su consentimiento")


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


@app.post("/consentimientos", response_model=ConsentimientoOut, status_code=201)
def otorgar(
    datos: OtorgarIn,
    actor: Actor = Depends(requiere("consentimiento:write", ROL_CLIENTE)),
    db: Session = Depends(get_db),
):
    exigir_dueno(actor, datos.cliente_id)
    activo = db.scalar(
        select(Consentimiento).where(
            Consentimiento.cliente_id == datos.cliente_id,
            Consentimiento.fuente == datos.fuente,
            Consentimiento.estado == ESTADO_ACTIVO,
        )
    )
    if activo is not None:
        raise HTTPException(409, "El cliente ya tiene un consentimiento activo para esa fuente")
    c = Consentimiento(
        cliente_id=datos.cliente_id,
        fuente=datos.fuente,
        alcance=datos.alcance,
        estado=ESTADO_ACTIVO,
        fecha_otorgamiento=ahora(),
    )
    db.add(c)
    db.flush()
    db.add(
        RegistroAuditoria(
            evento=EVENTO_OTORGADO, cliente_id=c.cliente_id, consentimiento_id=c.id, actor=actor.sub,
            detalle=f"fuente={c.fuente} alcance={c.alcance}",
        )
    )
    db.commit()  # consentimiento + auditoria en una sola transaccion
    log.info("evento=OTORGADO cliente=%s consentimiento=%s", c.cliente_id, c.id)
    return a_salida(c)


@app.post("/consentimientos/{consentimiento_id}/revocacion", response_model=ConsentimientoOut)
def revocar(
    consentimiento_id: uuid.UUID,
    actor: Actor = Depends(requiere("consentimiento:write", ROL_CLIENTE)),
    db: Session = Depends(get_db),
):
    c = db.get(Consentimiento, consentimiento_id, with_for_update=True)
    if c is None:
        raise HTTPException(404, "Consentimiento no encontrado")
    exigir_dueno(actor, c.cliente_id)
    if c.estado == ESTADO_REVOCADO:
        return a_salida(c)  # idempotente: revocar dos veces no cambia nada ni duplica auditoria
    c.estado = ESTADO_REVOCADO
    c.fecha_revocacion = ahora()
    db.add(
        RegistroAuditoria(
            evento=EVENTO_REVOCADO, cliente_id=c.cliente_id, consentimiento_id=c.id, actor=actor.sub,
            detalle=f"fuente={c.fuente}",
        )
    )
    db.commit()  # el 200 solo sale cuando estado y auditoria ya estan guardados (t0 del experimento)
    log.info("evento=REVOCADO cliente=%s consentimiento=%s", c.cliente_id, c.id)
    return a_salida(c)


@app.get("/consentimientos/vigente", response_model=VigenteOut)
def consultar_vigente(
    cliente_id: uuid.UUID = Query(alias="clienteId"),
    fuente: str = FUENTE_OPEN_FINANCE,
    _: Actor = Depends(requiere("consentimiento:read", ROL_SERVICIO)),
    db: Session = Depends(get_db),
):
    """Conector "ConsultarConsentimientoVigente" que usa Perfilamiento."""
    c = db.scalar(
        select(Consentimiento).where(
            Consentimiento.cliente_id == cliente_id,
            Consentimiento.fuente == fuente,
            Consentimiento.estado == ESTADO_ACTIVO,
        )
    )
    if c is None:
        return VigenteOut(clienteId=cliente_id, fuente=fuente, vigente=False)
    return VigenteOut(
        clienteId=cliente_id, fuente=fuente, vigente=True, consentimientoId=c.id, alcance=c.alcance
    )


@app.get("/consentimientos", response_model=list[ConsentimientoOut])
def listar_del_cliente(
    cliente_id: uuid.UUID = Query(alias="clienteId"),
    actor: Actor = Depends(requiere("consentimiento:read", ROL_CLIENTE)),
    db: Session = Depends(get_db),
):
    exigir_dueno(actor, cliente_id)
    return [a_salida(c) for c in db.scalars(select(Consentimiento).where(Consentimiento.cliente_id == cliente_id))]


@app.post("/auditoria/accesos-negados", status_code=201)
def registrar_acceso_negado(
    datos: AccesoNegadoIn,
    actor: Actor = Depends(requiere("auditoria:write", ROL_SERVICIO)),
    db: Session = Depends(get_db),
):
    """Perfilamiento reporta aqui cada acceso que nego (fuera del camino de la respuesta)."""
    db.add(
        RegistroAuditoria(
            evento=EVENTO_ACCESO_NEGADO, cliente_id=datos.cliente_id, actor=actor.sub, detalle=datos.motivo
        )
    )
    db.commit()
    return {"registrado": True}


@app.get("/auditoria", response_model=list[AuditoriaOut])
def consultar_auditoria(
    cliente_id: uuid.UUID | None = Query(default=None, alias="clienteId"),
    evento: str | None = None,
    desde: datetime | None = None,
    limite: int = Query(default=500, le=5000),
    _: Actor = Depends(requiere("auditoria:read", ROL_AUDITOR)),
    db: Session = Depends(get_db),
):
    q = select(RegistroAuditoria).order_by(RegistroAuditoria.fecha).limit(limite)
    if cliente_id is not None:
        q = q.where(RegistroAuditoria.cliente_id == cliente_id)
    if evento is not None:
        q = q.where(RegistroAuditoria.evento == evento)
    if desde is not None:
        q = q.where(RegistroAuditoria.fecha >= desde)
    return [
        AuditoriaOut(
            id=r.id, fecha=r.fecha, evento=r.evento, clienteId=r.cliente_id,
            consentimientoId=r.consentimiento_id, actor=r.actor, detalle=r.detalle,
        )
        for r in db.scalars(q)
    ]

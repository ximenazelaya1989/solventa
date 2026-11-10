"""Mock de Open Finance (FastAPI), compartido por EXP-009 y EXP-007.

Simula al proveedor externo de señales financieras y deja inyectar fallas:

  GET  /senales/{clienteId}   señales del cliente (determinista por cliente)
  POST /admin/fail            cambia el modo: ok | error503 | lento2s
  GET  /admin/estado          modo actual y contadores (llamadasPorCliente)
  POST /admin/reset           limpia los contadores (no cambia el modo)
  GET  /health                liveness

Modos de /senales:
  ok        responde en ~MOCK_LATENCIA_NORMAL_MS (50 ms por defecto)
  error503  responde 503 de inmediato (proveedor caido)
  lento2s   responde 200 tras MOCK_LATENCIA_LENTA_MS (2000 ms por defecto)

Contrato que usan los experimentos:
  - EXP-007 (medir_revocacion.py) lee `llamadasPorCliente` de /admin/estado para
    comprobar que Perfilamiento no llama a Open Finance tras negar el acceso.
  - EXP-009 usa /admin/fail para tumbar y restaurar Open Finance, y
    `cambios` (con marca de tiempo) para calcular el tiempo de deteccion.
"""
import asyncio
import hashlib
import os
import random
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

SERVICE_NAME = os.getenv("SERVICE_NAME", "mock-open-finance")
LATENCIA_NORMAL_MS = float(os.getenv("MOCK_LATENCIA_NORMAL_MS", "50"))
LATENCIA_LENTA_MS = float(os.getenv("MOCK_LATENCIA_LENTA_MS", "2000"))

MODOS = ("ok", "error503", "lento2s")
ALIAS = {  # nombres alternativos aceptados en /admin/fail
    "normal": "ok", "restaurar": "ok", "503": "error503", "caida": "error503",
    "error": "error503", "latencia": "lento2s", "lento": "lento2s", "2s": "lento2s",
}


def ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Estado:
    def __init__(self) -> None:
        self.modo = "ok"
        self.llamadas_por_cliente: dict[str, int] = {}
        self.llamadas_total = 0
        self.cambios: list[dict] = [{"modo": "ok", "desde": ahora()}]

    def cambiar(self, modo: str) -> None:
        self.modo = modo
        self.cambios.append({"modo": modo, "desde": ahora()})
        del self.cambios[:-50]  # solo se guardan los ultimos 50


estado = Estado()
app = FastAPI(title="Solventa - Mock de Open Finance")


class FailIn(BaseModel):
    modo: str


def senales_de(cliente_id: uuid.UUID) -> dict:
    """Señales deterministas: el mismo cliente siempre devuelve lo mismo."""
    h = int(hashlib.sha256(str(cliente_id).encode()).hexdigest(), 16)
    return {
        "ingresoMensual": 1_500_000 + (h % 8_500_000),
        "endeudamiento": round(((h >> 16) % 70) / 100, 2),
        "mora30d": (h >> 24) % 4,
        "antiguedadMeses": 6 + (h >> 32) % 180,
        "origen": "mock-open-finance",
    }


@app.get("/health")
def health():
    return {"status": "ok", "servicio": SERVICE_NAME}


@app.get("/senales/{cliente_id}")
async def senales(cliente_id: uuid.UUID):
    # Se cuenta cada llamada que llega (tambien las que fallan o van lentas).
    clave = str(cliente_id)
    estado.llamadas_total += 1
    estado.llamadas_por_cliente[clave] = estado.llamadas_por_cliente.get(clave, 0) + 1

    if estado.modo == "error503":
        raise HTTPException(status_code=503, detail="Open Finance no disponible (simulado)")
    if estado.modo == "lento2s":
        await asyncio.sleep(LATENCIA_LENTA_MS / 1000)
    else:
        await asyncio.sleep(max(0.0, random.gauss(LATENCIA_NORMAL_MS, 8)) / 1000)
    return {"clienteId": clave, "senales": senales_de(cliente_id)}


@app.post("/admin/fail")
def fail(datos: FailIn):
    modo = ALIAS.get(datos.modo.strip().lower(), datos.modo.strip().lower())
    if modo not in MODOS:
        raise HTTPException(status_code=422, detail=f"modo invalido; usa uno de {list(MODOS)}")
    estado.cambiar(modo)
    return {"modo": estado.modo, "desde": estado.cambios[-1]["desde"]}


@app.get("/admin/estado")
def ver_estado():
    return {
        "modo": estado.modo,
        "llamadasTotal": estado.llamadas_total,
        "llamadasPorCliente": estado.llamadas_por_cliente,
        "cambios": estado.cambios,
    }


@app.post("/admin/reset")
def reset():
    estado.llamadas_por_cliente.clear()
    estado.llamadas_total = 0
    return {"ok": True}

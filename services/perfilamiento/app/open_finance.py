"""Cliente de Open Finance en Perfilamiento (EXP-009, HU10.1.3).

Modulo propio de EXP-009: toda la logica de la llamada a Open Finance vive aqui,
para que main.py solo la invoque y no choque con consentimiento.py (EXP-007).

Estado actual (base, sin tacticas): llamada directa al mock con un timeout
generico. Si Open Finance falla o tarda, la peticion falla con 502; esa es la
linea base A del experimento. Las tacticas (timeout de 120 ms, circuit breaker,
bulkhead, cache en Redis y perfil por defecto) se agregan en este archivo,
detras de CIRCUIT_BREAKER_ENABLED, sin tocar main.py.

Flags:
  OPEN_FINANCE_ENABLED=false  GET /perfiles devuelve solo lo guardado en la BD
  OPEN_FINANCE_ENABLED=true   ademas consulta Open Finance en cada peticion
"""
import logging
import os
import uuid

import httpx
from fastapi import HTTPException

log = logging.getLogger("perfilamiento.open_finance")

OPEN_FINANCE_ENABLED = os.getenv("OPEN_FINANCE_ENABLED", "false").lower() == "true"
OPEN_FINANCE_URL = os.getenv("OPEN_FINANCE_URL", "http://localhost:18009").rstrip("/")
OPEN_FINANCE_TIMEOUT_S = float(os.getenv("OPEN_FINANCE_TIMEOUT_S", "5.0"))

_http = httpx.Client(timeout=OPEN_FINANCE_TIMEOUT_S)


class OpenFinanceError(Exception):
    """Open Finance no respondio bien (error, timeout o respuesta invalida)."""


def _consultar(cliente_id: uuid.UUID) -> dict:
    try:
        r = _http.get(f"{OPEN_FINANCE_URL}/senales/{cliente_id}")
    except httpx.HTTPError as e:
        raise OpenFinanceError(f"error de red: {e.__class__.__name__}") from e
    if r.status_code != 200:
        raise OpenFinanceError(f"Open Finance respondio {r.status_code}")
    return r.json().get("senales") or {}


def senales_open_finance(cliente_id: uuid.UUID, guardadas: dict | None) -> dict | None:
    """Señales de Open Finance para el perfil del cliente.

    Apagado devuelve `guardadas` (lo que hay en perfilamiento_db). Encendido
    consulta Open Finance; sin tacticas, una falla se propaga como 502.
    """
    if not OPEN_FINANCE_ENABLED:
        return guardadas
    try:
        return _consultar(cliente_id)
    except OpenFinanceError as e:
        log.warning("open_finance fallo cliente=%s: %s", cliente_id, e)
        raise HTTPException(status_code=502, detail=f"Open Finance no disponible: {e}") from e

"""Autenticacion (JWT) y autorizacion (RBAC + scopes) de Consentimiento (EXP-007).

Tacticas: autenticar actores y autorizar actores.

Los tokens son JWT HS256 firmados con JWT_SECRET. En produccion los emitiria
Amazon Cognito; como AWS Academy no lo permite, en el experimento los emite el
script de prueba con la misma llave compartida.

Claims esperados:
  sub   -> id del actor (clienteId para un cliente, nombre del servicio para un servicio)
  rol   -> cliente | servicio | auditor
  scope -> scopes separados por espacio (ej. "consentimiento:read auditoria:write")
  exp   -> expiracion (obligatorio)
"""
import os
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = os.getenv("JWT_SECRET", "cambiar-en-despliegue")
JWT_ALGORITMO = "HS256"

ROL_CLIENTE = "cliente"
ROL_SERVICIO = "servicio"
ROL_AUDITOR = "auditor"

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Actor:
    sub: str
    rol: str
    scopes: frozenset[str]


def autenticar(credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Actor:
    if credenciales is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token Bearer")
    try:
        claims = jwt.decode(
            credenciales.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITMO],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token invalido: {e}") from e
    return Actor(
        sub=str(claims["sub"]),
        rol=str(claims.get("rol", "")),
        scopes=frozenset(str(claims.get("scope", "")).split()),
    )


def requiere(scope: str, *roles: str):
    """Dependencia RBAC: el actor debe tener uno de los roles y el scope indicado."""

    def _verificar(actor: Actor = Depends(autenticar)) -> Actor:
        if actor.rol not in roles or scope not in actor.scopes:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requiere rol {roles} y scope {scope}")
        return actor

    return _verificar

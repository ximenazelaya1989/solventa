"""EXP-009: prepara los datos de prueba.

  1. Crea 1.000 clientes sinteticos con su perfil en Perfilamiento (POST /perfiles).
     Los ids son deterministas (uuid5), asi Locust y este script usan los mismos.
       - clientes 0..799   -> "con cache" (80 %): se les calienta la cache
       - clientes 800..999 -> "sin cache" (20 %): ejercitan el perfil por defecto
  2. (Config B) Calienta la cache de los 800 primeros: un GET /perfiles con Open
     Finance sano guarda su perfil en Redis.
  3. (opcional) --redis URL borra antes las claves de perfiles de corridas anteriores.

Solo usa la libreria estandar (y `redis` si se pasa --redis).

Uso:
  python preparar_datos.py --perf http://localhost:18002 [--redis redis://localhost:16379/0]
"""
import argparse
import json
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor

NS = uuid.UUID("a1b2c3d4-0000-4000-8000-000000000009")  # mismo valor que locustfile.py


def cliente(i: int) -> str:
    return str(uuid.uuid5(NS, f"cliente-{i}"))


def http(url: str, metodo: str = "GET", cuerpo=None):
    data = json.dumps(cuerpo).encode() if cuerpo is not None else None
    r = urllib.request.Request(url, data=data, method=metodo, headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--perf", default="http://localhost:18002", help="URL de Perfilamiento")
    p.add_argument("--n", type=int, default=1000, help="clientes en total")
    p.add_argument("--con-cache", type=int, default=800, help="clientes cuya cache se calienta")
    p.add_argument("--redis", help="URL de Redis: borra las claves de perfiles antes de empezar")
    a = p.parse_args()
    perf = a.perf.rstrip("/")

    if a.redis:
        import redis

        r = redis.Redis.from_url(a.redis)
        borradas = 0
        for k in r.scan_iter("perfil:open-finance:*"):
            r.delete(k)
            borradas += 1
        print(f"Redis: {borradas} claves de perfiles borradas")

    def crear(i: int) -> int:
        score = 50 + (i * 7) % 41  # 50..90, determinista
        s, _ = http(f"{perf}/perfiles", "POST", {"clienteId": cliente(i), "score": score})
        return s

    with ThreadPoolExecutor(16) as pool:
        codigos = list(pool.map(crear, range(a.n)))
    print(f"Perfiles: {codigos.count(201)} creados, {codigos.count(409)} ya existian, "
          f"{len(codigos) - codigos.count(201) - codigos.count(409)} con error")

    estado = http(f"{perf}/admin/open-finance/estado")[1] or {}
    if not estado.get("circuitBreakerEnabled"):
        print("Config A (sin circuit breaker): no hay cache que calentar.")
        return

    def calentar(i: int):
        s, d = http(f"{perf}/perfiles/{cliente(i)}")
        return s, (d or {}).get("senalesOpenFinance", {}).get("origen") if s == 200 else None

    with ThreadPoolExecutor(8) as pool:
        res = list(pool.map(calentar, range(a.con_cache)))
    buenos = sum(1 for s, o in res if s == 200 and o == "mock-open-finance")
    print(f"Cache: {buenos}/{a.con_cache} perfiles calentados desde Open Finance")
    if buenos != a.con_cache:
        print("AVISO: el mock debe estar en modo ok y Redis disponible; revisa y vuelve a correr.")


if __name__ == "__main__":
    main()

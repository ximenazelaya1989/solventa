# Experimento H7.2.1 — Disponibilidad del servicio de desembolso

Prueba: enviar desembolsos de forma constante, detener una instancia a mitad de la corrida y comprobar que
no se pierde ni se duplica ningun pedido.

## Archivos

| Archivo | Para que sirve |
|---|---|
| `load_test.py` | El script de carga. Genera la salida en consola, `informe.html` con graficas y `tabla.html` |
| `requirements.txt` | Unica libreria necesaria: `aiohttp` |
| `verificar.sql` | Vaciar la tabla antes de cada corrida y contar filas / duplicados despues |

## Preparacion (una vez)

```bash
py -m pip install -r requirements.txt
```

## Una corrida

1. Vaciar la tabla: `TRUNCATE TABLE pagos;` (ver `verificar.sql`).
2. Ejecutar el script:

```bash
python load_test.py --url http://<DNS_DEL_ALB> --nombre B1 --descripcion "3 instancias, stop en min 3" \
  --users 60 --ramp-up 5 --duration 600 --tps 10
```

3. **Mientras corre**, cuando detengas la instancia en la consola de AWS, aprieta ENTER (o escribe
   `stop instancia` y ENTER). Repite al reiniciarla. Esas marcas salen en las graficas.
4. Al terminar, contar en la base de datos (`SELECT count(*) FROM pagos;`) y registrar el numero:

```bash
python load_test.py --completar B1 --filas-bd <N> --duplicados 0
```

Resultados en `resultados/`: `tabla.html` (todas las corridas), `resumen_corridas.csv` (la misma tabla para Excel)
y, por corrida, `<nombre>/informe.html`, `requests.csv` y `resumen.json`.

## Caso de idempotencia (F03)

```bash
python load_test.py --url http://127.0.0.1:3000 --modo idempotencia --nombre F03 --users 50
```

Todas las peticiones salen a la vez con el mismo `siniestroId`. Esperado: 0 errores y 1 sola fila en la BD.

## Parametros

| Parametro | Significado |
|---|---|
| `--users` | Usuarios (hilos) simultaneos |
| `--ramp-up` | Segundos en que entran todos los usuarios |
| `--duration` | Segundos de la prueba |
| `--tps` | Pedidos nuevos por segundo (0 = cada usuario va a su propio ritmo) |
| `--reintentos` | Intentos maximos por pedido, siempre con el mismo `siniestroId` (por defecto 3) |
| `--marca-auto` | Marcas planeadas, ej. `"180:stop instancia,360:reinicio"` |

## Consejos

- En tu computador usa `127.0.0.1` y no `localhost`: en Windows `localhost` prueba primero IPv6 y agrega ~250 ms
  a cada conexion, lo que falsea el connect time.
- Cada peticion abre una conexion nueva (asi se mide el connect time). Usa `--keepalive` para reusarlas.

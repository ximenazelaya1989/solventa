# Evidencia del experimento HU1.1.2 — Rolling update de reglas de rating sin downtime

## 1. Rolling update sano (v1 → v2)

== Publicando nueva version de reglas ==
{"id":"bb21f781-1a86-4ebd-973f-a73dd6233809","version":2,"factores":{"bajo":1,"medio":1.35,"alto":1.9},"fallaSanityCheck":false,"creadaEn":"2026-09-24T08:20:31.265Z"}
Nueva version publicada: v2

== [08:20:31] Aplicando v2 en 54.165.42.252:3000 ==
{"status":"ok","versionCargada":2,"saludable":true}
-- Health de 54.165.42.252:3000 --
{"status":"ok","versionCargada":2,"saludable":true}
Instancia 54.165.42.252:3000 lista. Esperando 5s antes de continuar...

== [08:20:36] Aplicando v2 en 3.208.25.175:3000 ==
{"status":"ok","versionCargada":2,"saludable":true}
-- Health de 3.208.25.175:3000 --
{"status":"ok","versionCargada":2,"saludable":true}
Instancia 3.208.25.175:3000 lista. Esperando 5s antes de continuar...

== Rolling update completo. Ambas instancias en v2 ==


**Resultado**: ambas instancias actualizadas de forma secuencial (instancia 1 primero, verificada saludable, luego instancia 2), sin ningún momento en que las dos estuvieran caídas a la vez.

## 2. Version defectuosa: deteccion de falla y rollback automatico

== Publicando version defectuosa (fallaSanityCheck=true) ==
{"id":"2131517e-6991-47b9-ab00-a0cd1d8ca374","version":3,"factores":{"bajo":1},"fallaSanityCheck":true,"creadaEn":"2026-09-24T08:22:17.183Z"}

== [08:22:17] Aplicando v3 (defectuosa) en 54.165.42.252:3000 ==
{"status":"unhealthy","versionCargada":3,"saludable":false,"motivo":"la version cargada no paso el self-test"}

== Monitoreando /rating/health cada 2s (hasta 90s) ==
t+0s [08:22:17] HTTP: 503
t+3s [08:22:20] HTTP: 503
t+5s [08:22:22] HTTP: 503
t+7s [08:22:24] HTTP: 503
t+9s [08:22:26] HTTP: 503
t+11s [08:22:28] HTTP: 503
t+14s [08:22:31] HTTP: 503
t+16s [08:22:33] HTTP: 503
t+18s [08:22:35] HTTP: 503
t+20s [08:22:37] HTTP: 503
t+22s [08:22:39] HTTP: 503
t+25s [08:22:42] HTTP: 503
t+27s [08:22:44] HTTP: 503
t+29s [08:22:46] HTTP: 503
t+31s [08:22:48] HTTP: 200

Recuperada (rollback automatico) en t+31s desde que se aplico la version defectuosa.


**Resultado**: deteccion de falla inmediata (t+0s), rollback automatico completo en 31 segundos — dentro del limite de 60s exigido por HU1.1.2.


## 3. Impacto en el cliente (k6, trafico constante 20 VUs durante 6 minutos)

THRESHOLDS
http_req_duration
✓ 'p(95)<1500' p(95)=114.84ms
http_req_failed
✗ 'rate<0.01' rate=2.75%

TOTAL RESULTS
checks_total.......: 6580
checks_succeeded...: 97.24% (6399/6580)
checks_failed......: 2.75% (181/6580)
http_req_duration..: avg=93.56ms p(95)=114.84ms
http_reqs..........: 6580 (18.23 req/s)


**Resultado real**: 181 de 6580 peticiones (2.75%) fallaron durante toda la ventana de 6 minutos.
Estas fallas se concentran en la ventana de deteccion del health check del ALB
(intervalo=15s, umbral=2 chequeos consecutivos), es decir, entre 15 y 30 segundos
en los que la instancia 1 seguia recibiendo trafico real del ALB a pesar de tener
una version de reglas invalida cargada. El calculo es consistente: a ~9 req/s
dirigidas a la instancia 1, una ventana de deteccion de ~20s explica las 181
peticiones fallidas observadas.

## Conclusion

La hipotesis original ("cero downtime perceptible") se cumple parcialmente: el
mecanismo de versionado, self-test y rollback automatico funciona correctamente
a nivel de instancia (deteccion inmediata, rollback en 31s, bien dentro del
limite de 60s de HU1.1.2). Sin embargo, el experimento revela que el downtime
END-TO-END percibido por el cliente no es literalmente cero: queda acotado por
la granularidad del health check del Load Balancer (intervalo x umbral = 15-30s),
durante la cual el ALB aun no ha retirado la instancia fallida de rotacion.

Esto sugiere una mejora de diseno concreta: bajar el intervalo del health check
(por ejemplo a 5s) y/o el umbral (a 1 chequeo) reduciria la ventana de exposicion,
a costa de mayor sensibilidad a falsos positivos (picos de latencia transitorios
que no son fallas reales). Es un trade-off explicito de arquitectura, no un
defecto de la implementacion.


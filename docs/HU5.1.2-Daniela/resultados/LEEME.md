# Resultados de EXP-008

- `corridas.json`: C, cuota y hora de inicio y fin (UTC) de cada corrida.
- `crudos/`: JTL de JMeter comprimidos (una fila por petición), planes `.jmx`, salida de JMeter y `progreso.log` del runner.
  - `calibracion` (escalones de 20) y `calibracion_2` (escalones de 10, la que fija C = 60).
  - `piloto_corrida_1_sin_C20`: corrida piloto con C = 20, detenida en el minuto 8.
  - `corrida_1_sin` a `corrida_6_con`: las 6 corridas del experimento.
- `cloudwatch_corrida_*.json`: CPU y memoria de las tareas ECS, CPU y conexiones de las RDS, CPU de Redis y de la EC2, cada minuto.
- `eventos_ecs.json`: eventos de los servicios ECS (reemplazos de tareas).
- `analisis/`: tablas, figuras y `veredicto.json` generados con `experimento/analisis/resumen_informe.py`.

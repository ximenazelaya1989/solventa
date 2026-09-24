-- ANTES de cada corrida: dejar la tabla vacia
TRUNCATE TABLE pagos;

-- DESPUES de cada corrida
-- 1) Filas guardadas (columna "Filas en BD" del Excel).
--    Debe ser igual a exitos_1er_intento + exitos_tras_reintento.
SELECT count(*) AS filas_en_bd FROM pagos;

-- 2) Duplicados (columna "Claves con mas de 1 fila"). Debe dar 0 filas.
SELECT "siniestroId", count(*) AS veces
FROM pagos
GROUP BY "siniestroId"
HAVING count(*) > 1;

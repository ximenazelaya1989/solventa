-- ============================================================================
-- Experimento HU2.1.1 · Reinicio de la BD a estado semilla (antes de CADA corrida)
-- Uso: psql -h <DB_HOST> -U solventa -d solventa -v n=12000 -f reset-y-semilla.sql
--   n = número de cotizaciones a generar (una por cliente). Debe ser mayor que
--       TPS x segundos de la corrida, porque cotizacionId es único en
--       suscripciones: cada petición necesita una cotización nueva.
-- Genera además cotizaciones.csv (id, decisión esperada) para el script k6.
-- ============================================================================
\set ON_ERROR_STOP on

BEGIN;

TRUNCATE suscripciones, pagos, polizas, cotizaciones, perfiles_riesgo,
         consentimientos, identidad_credenciales, clientes, productos
         RESTART IDENTITY CASCADE;

-- 20 productos con prima base entre 50.000 y 500.000
INSERT INTO productos (id, prima)
SELECT gen_random_uuid(), round((50000 + random() * 450000)::numeric, 2)
FROM generate_series(1, 20);

CREATE TEMP TABLE tmp_clientes ON COMMIT DROP AS
SELECT gen_random_uuid() AS id, g AS n, random() AS r
FROM generate_series(1, :n) AS g;

INSERT INTO clientes (id, nombre, "documentoIdentidad")
SELECT id, 'Cliente experimento ' || n, 'EXP' || lpad(n::text, 10, '0')
FROM tmp_clientes;

-- Identidad verificada y consentimiento activo: precondiciones del perfilamiento
INSERT INTO identidad_credenciales ("clienteId", "metodoKYC", "estadoVerificacion", "fechaVerificacion")
SELECT id, 'semilla', 'verificado', now() FROM tmp_clientes;

INSERT INTO consentimientos ("clienteId", fuente, alcance, estado)
SELECT id, 'open-finance', 'perfilamiento', 'activo' FROM tmp_clientes;

-- Distribución de scores (variable controlada):
--   70 % aprobación automática [0.70, 1.00]
--   20 % revisión asistida     [0.40, 0.70)
--   10 % rechazo               [0.00, 0.40)
INSERT INTO perfiles_riesgo (id, "clienteId", score, "señalesOpenFinance")
SELECT gen_random_uuid(), id,
       CASE WHEN r < 0.70 THEN 0.70 + random() * 0.30
            WHEN r < 0.90 THEN 0.40 + random() * 0.2999
            ELSE random() * 0.3999 END,
       '{"fuente": "semilla-experimento"}'::jsonb
FROM tmp_clientes;

-- Una cotización por cliente, con el perfil que la "califica"
WITH ps AS (SELECT array_agg(id ORDER BY id) AS ids, array_agg(prima ORDER BY id) AS primas FROM productos)
INSERT INTO cotizaciones (id, prima, "clienteId", "productoId", "perfilRiesgoId")
SELECT gen_random_uuid(),
       round((ps.primas[1 + c.n % 20] * (1.3 - 0.6 * pr.score))::numeric, 2),
       c.id, ps.ids[1 + c.n % 20], pr.id
FROM tmp_clientes c
JOIN perfiles_riesgo pr ON pr."clienteId" = c.id
CROSS JOIN ps;

COMMIT;

ANALYZE;

\echo 'Semilla lista. Exportando cotizaciones.csv ...'
\copy (SELECT c.id, CASE WHEN pr.score >= 0.7 THEN 'aprobada' WHEN pr.score >= 0.4 THEN 'revision' ELSE 'rechazada' END AS esperado FROM cotizaciones c JOIN perfiles_riesgo pr ON pr.id = c."perfilRiesgoId" ORDER BY random()) TO 'cotizaciones.csv' WITH CSV HEADER

SELECT (SELECT count(*) FROM cotizaciones) AS cotizaciones,
       (SELECT count(*) FROM perfiles_riesgo WHERE score >= 0.7) AS esperadas_aprobadas;

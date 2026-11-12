// EXP-010 (HU5.1.1, Génesis) - configuracion del experimento.
// Todo queda apagado por defecto: con JWT_VALIDATION_ENABLED=false el servicio
// se comporta como la base compartida (la ruta nueva responde 404).

export const EXP010_ACTIVO =
  (process.env.JWT_VALIDATION_ENABLED ?? 'false').toLowerCase() === 'true';

export const COTIZACION_URL = (
  process.env.COTIZACION_URL ?? 'http://localhost:8001'
).replace(/\/$/, '');

export const COTIZACION_TIMEOUT_MS = Number(
  process.env.COTIZACION_TIMEOUT_MS ?? 5000,
);

// Datos semilla del experimento: dos socios ficticios y un cliente de cada uno.
// El cliente del socio A es el cliente demo de la base (tiene perfil de riesgo).
export const SOCIO_A = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa';
export const SOCIO_B = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
export const CLIENTE_SOCIO_A = '11111111-1111-1111-1111-111111111111';
export const CLIENTE_SOCIO_B = '33333333-3333-3333-3333-333333333333';

// client_id de las aplicaciones de Cognito de cada socio, separados por coma.
// En AWS los pone la plantilla de CloudFormation; en local se usan valores fijos.
const lista = (valor: string | undefined) =>
  (valor ?? '')
    .split(',')
    .map((v) => v.trim())
    .filter(Boolean);

export const CLIENTES_COGNITO_SOCIO_A = lista(
  process.env.EXP010_COGNITO_CLIENTES_SOCIO_A ?? 'local-socio-a',
);
export const CLIENTES_COGNITO_SOCIO_B = lista(
  process.env.EXP010_COGNITO_CLIENTES_SOCIO_B ?? 'local-socio-b',
);

// Una linea JSON por evento: facilita contarlos en CloudWatch Logs Insights.
export function registrar(evento: string, datos: Record<string, unknown>) {
  console.log(
    JSON.stringify({
      exp: 'EXP-010',
      servicio: 'distribucion-socios',
      evento,
      ts: new Date().toISOString(),
      ...datos,
    }),
  );
}

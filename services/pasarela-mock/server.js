// Pasarela de pagos simulada (EXP-006, H7.2.1).
// Representa al sistema externo "Pasarelas de pago": aprueba cada desembolso y
// respeta la llave de idempotencia (encabezado Idempotency-Key). Si recibe dos
// veces la misma llave, devuelve la misma transaccion y no "paga" dos veces.
// Sin dependencias: solo el modulo http de Node.
//
// Rutas (se aceptan con y sin el prefijo /pasarela, que usa el ALB interno):
//   POST /desembolsos   -> { transaccionId, estado, repetida }
//   GET  /health
//   GET  /estadisticas  -> desembolsos unicos y repeticiones recibidas

const http = require('http');
const { randomUUID } = require('crypto');

const PUERTO = Number(process.env.PORT ?? 8080);
const LATENCIA_MS = Number(process.env.PASARELA_LATENCIA_MS ?? 50);

const transacciones = new Map(); // llave -> transaccion
let repeticiones = 0;

function responder(res, status, cuerpo) {
  res.writeHead(status, { 'content-type': 'application/json' });
  res.end(JSON.stringify(cuerpo));
}

const servidor = http.createServer((req, res) => {
  const ruta = (req.url ?? '/').replace(/^\/pasarela/, '') || '/';

  if (req.method === 'GET' && ruta === '/health') {
    return responder(res, 200, { status: 'ok', servicio: 'pasarela-mock' });
  }
  if (req.method === 'GET' && ruta === '/estadisticas') {
    return responder(res, 200, {
      desembolsosUnicos: transacciones.size,
      repeticionesRecibidas: repeticiones,
    });
  }
  if (req.method === 'POST' && ruta === '/desembolsos') {
    const llave = req.headers['idempotency-key'];
    if (!llave) {
      return responder(res, 400, { error: 'falta Idempotency-Key' });
    }
    req.resume();
    req.on('end', () => {
      setTimeout(() => {
        const previa = transacciones.get(llave);
        if (previa) {
          repeticiones++;
          return responder(res, 200, { ...previa, repetida: true });
        }
        const tx = { transaccionId: `TX-${randomUUID()}`, estado: 'aprobado' };
        transacciones.set(llave, tx);
        responder(res, 201, { ...tx, repetida: false });
      }, LATENCIA_MS);
    });
    return;
  }
  responder(res, 404, { error: 'ruta no encontrada' });
});

servidor.keepAliveTimeout = 65000; // mayor que el idle timeout del ALB (60 s)
servidor.listen(PUERTO, '0.0.0.0', () => {
  console.log(JSON.stringify({ evento: 'pasarela_iniciada', puerto: PUERTO }));
});

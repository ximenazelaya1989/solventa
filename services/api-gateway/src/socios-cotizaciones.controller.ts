import {
  Body,
  Controller,
  Headers,
  HttpException,
  NotFoundException,
  Post,
  Res,
} from '@nestjs/common';
import type { Response } from 'express';
import { timingSafeEqual } from 'crypto';

// EXP-010 (HU5.1.1, Génesis) - archivo propio del experimento.
//
// Diseno en dos niveles: el AWS API Gateway de borde (gateway de terceros)
// valida el JWT de Cognito y el scope ANTES de reenviar la peticion aqui. Este
// gateway interno NO valida tokens: solo reenvia POST /v1/socios/cotizaciones a
// Distribucion y socios. Como defensa contra peticiones que se salten el borde,
// exige el encabezado secreto x-origin-verify que solo agrega el borde.
//
// Con JWT_VALIDATION_ENABLED=false la ruta responde 404 (base compartida intacta).
// No toca el limitador por socio de EXP-008.
const ACTIVO =
  (process.env.JWT_VALIDATION_ENABLED ?? 'false').toLowerCase() === 'true';
const DISTRIBUCION_URL = (
  process.env.DISTRIBUCION_URL ?? 'http://localhost:3006'
).replace(/\/$/, '');
const SECRETO_ORIGEN = process.env.ORIGIN_VERIFY_SECRET ?? '';
const TIMEOUT_MS = Number(process.env.DISTRIBUCION_TIMEOUT_MS ?? 8000);

function mismoSecreto(recibido: string | undefined): boolean {
  if (!SECRETO_ORIGEN) return true; // sin secreto configurado (solo en local)
  if (!recibido) return false;
  const a = Buffer.from(recibido);
  const b = Buffer.from(SECRETO_ORIGEN);
  return a.length === b.length && timingSafeEqual(a, b);
}

function registrar(evento: string, datos: Record<string, unknown>) {
  console.log(
    JSON.stringify({ exp: 'EXP-010', servicio: 'api-gateway', evento, ts: new Date().toISOString(), ...datos }),
  );
}

@Controller('v1/socios/cotizaciones')
export class SociosCotizacionesController {
  @Post()
  async crear(
    @Body() body: unknown,
    @Headers('x-origin-verify') origen: string | undefined,
    @Headers('x-socio-client-id') clientId: string | undefined,
    @Headers('x-request-id') requestId: string | undefined,
    @Res({ passthrough: true }) res: Response,
  ) {
    if (!ACTIVO) throw new NotFoundException();

    const traza = { requestId: requestId ?? null, clientId: clientId ?? null };
    if (!mismoSecreto(origen)) {
      registrar('rechazada', { ...traza, codigo: 403, motivo: 'no_paso_por_gateway_de_borde' });
      throw new HttpException({ mensaje: 'Origen no autorizado' }, 403);
    }
    registrar('reenviada', traza);

    const encabezados: Record<string, string> = { 'content-type': 'application/json' };
    if (clientId) encabezados['x-socio-client-id'] = clientId;
    if (requestId) encabezados['x-request-id'] = requestId;

    let respuesta: globalThis.Response;
    try {
      respuesta = await fetch(`${DISTRIBUCION_URL}/socios/cotizaciones`, {
        method: 'POST',
        headers: encabezados,
        body: JSON.stringify(body ?? {}),
        signal: AbortSignal.timeout(TIMEOUT_MS),
      });
    } catch {
      throw new HttpException('Distribucion y socios no disponible', 502);
    }
    const datos = await respuesta.json().catch(() => ({}));
    if (!respuesta.ok) throw new HttpException(datos, respuesta.status);
    res.status(respuesta.status);
    return datos;
  }
}

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
import { DataSource } from 'typeorm';
import { ClienteSocio } from '../entities/cliente-socio.entity';
import { CredencialSocio } from '../entities/credencial-socio.entity';
import {
  COTIZACION_TIMEOUT_MS,
  COTIZACION_URL,
  EXP010_ACTIVO,
  registrar,
} from './exp010.config';

interface SolicitudCotizacionSocio {
  clienteId?: string;
  productoId?: string;
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// EXP-010 (HU5.1.1): un socio pide una cotizacion para uno de sus clientes.
//
// La autenticacion (firma, emisor y vencimiento del JWT) y el scope los valida
// el AWS API Gateway de borde ANTES de que la peticion llegue aqui. Este
// servicio aplica la tactica "autorizar actores" por pertenencia: identifica al
// socio con el client_id del token (encabezado x-socio-client-id que agrega el
// gateway de borde) y solo deja pasar clientes de ese socio. Despues llama a
// Cotizacion con su contrato existente (POST /cotizaciones), sin cambiarlo.
@Controller('socios/cotizaciones')
export class SociosCotizacionesController {
  constructor(private readonly ds: DataSource) {}

  @Post()
  async crear(
    @Body() body: SolicitudCotizacionSocio,
    @Headers('x-socio-client-id') clientIdCognito: string | undefined,
    @Headers('x-request-id') requestId: string | undefined,
    @Res({ passthrough: true }) res: Response,
  ) {
    if (!EXP010_ACTIVO) throw new NotFoundException();

    const traza = { requestId: requestId ?? null, clientId: clientIdCognito ?? null, clienteId: body?.clienteId ?? null };
    registrar('peticion_recibida', traza);

    if (!body?.clienteId || !UUID.test(body.clienteId) || !body?.productoId || !UUID.test(body.productoId)) {
      registrar('rechazada', { ...traza, codigo: 400, motivo: 'cuerpo_invalido' });
      throw new HttpException({ mensaje: 'clienteId y productoId deben ser UUID' }, 400);
    }

    // 1) Que socio es (por la aplicacion de Cognito que obtuvo el token).
    const credencial = clientIdCognito
      ? await this.ds.getRepository(CredencialSocio).findOneBy({ cognitoClientId: clientIdCognito })
      : null;
    if (!credencial) {
      registrar('rechazada', { ...traza, codigo: 403, motivo: 'socio_desconocido' });
      throw new HttpException({ mensaje: 'Socio no registrado' }, 403);
    }

    // 2) Autorizar por pertenencia: el cliente debe ser de ese socio.
    const pertenece = await this.ds
      .getRepository(ClienteSocio)
      .existsBy({ socioId: credencial.socioId, clienteId: body.clienteId });
    if (!pertenece) {
      registrar('rechazada', { ...traza, socioId: credencial.socioId, codigo: 403, motivo: 'cliente_de_otro_socio' });
      throw new HttpException({ mensaje: 'El cliente no pertenece al socio' }, 403);
    }

    // 3) Pedir la cotizacion a Cotizacion (contrato existente, sin cambios).
    let respuesta: globalThis.Response;
    try {
      respuesta = await fetch(`${COTIZACION_URL}/cotizaciones`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({
          clienteId: body.clienteId,
          productoId: body.productoId,
          socioDistribucionId: credencial.socioId,
        }),
        signal: AbortSignal.timeout(COTIZACION_TIMEOUT_MS),
      });
    } catch {
      registrar('error_cotizacion', { ...traza, socioId: credencial.socioId, codigo: 502 });
      throw new HttpException({ mensaje: 'Cotizacion no disponible' }, 502);
    }
    const datos = await respuesta.json().catch(() => ({}));
    registrar('cotizacion_respondida', { ...traza, socioId: credencial.socioId, codigo: respuesta.status });
    if (!respuesta.ok) throw new HttpException(datos, respuesta.status);
    res.status(respuesta.status);
    return { ...datos, socioId: credencial.socioId };
  }
}

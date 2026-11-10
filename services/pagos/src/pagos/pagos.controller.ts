import {
  Body,
  Controller,
  Get,
  Headers,
  HttpCode,
  NotFoundException,
  Param,
  Post,
  Res,
} from '@nestjs/common';
import type { Response } from 'express';
import { PagosService, SolicitudDesembolso } from './pagos.service';
import { instancia } from '../common/instancia';

@Controller('pagos')
export class PagosController {
  constructor(private readonly servicio: PagosService) {}

  // Desembolso de una indemnizacion (H7.2.1). La llave de idempotencia puede
  // venir en el cuerpo o en el encabezado Idempotency-Key.
  //   201: pago nuevo     200: reintento de un pago ya registrado
  //   503: falla transitoria (p. ej. failover de Aurora): el cliente reintenta
  @Post()
  @HttpCode(201)
  async desembolsar(
    @Body() body: Partial<SolicitudDesembolso>,
    @Headers('idempotency-key') llaveEncabezado: string | undefined,
    @Res({ passthrough: true }) res: Response,
  ) {
    const sol = this.servicio.validar({
      ...body,
      claveIdempotencia: body.claveIdempotencia ?? llaveEncabezado,
    });
    const { pago, idempotente } = await this.servicio.desembolsar(sol);
    if (idempotente) res.status(200);
    return {
      pagoId: pago.id,
      claveIdempotencia: pago.claveIdempotencia,
      estado: pago.estado,
      monto: pago.monto,
      moneda: pago.moneda,
      referenciaPasarela: pago.referenciaPasarela,
      idempotente,
      atendidoPor: instancia(),
    };
  }

  @Get(':claveIdempotencia')
  async consultar(@Param('claveIdempotencia') clave: string) {
    const pago = await this.servicio.buscarPorClave(clave);
    if (!pago) throw new NotFoundException();
    return pago;
  }
}

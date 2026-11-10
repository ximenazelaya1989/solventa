import { Body, Controller, Get, HttpCode, Param, Post } from '@nestjs/common';
import { IndemnizacionesService } from './indemnizaciones.service';
import type { SolicitudIndemnizacion } from './indemnizaciones.service';

@Controller('siniestros')
export class IndemnizacionesController {
  constructor(private readonly servicio: IndemnizacionesService) {}

  // Aprueba un siniestro y ordena el desembolso de su indemnizacion (H7.2.1).
  //   201: pago confirmado por Pagos   503: no se pudo completar el pago
  @Post('indemnizaciones')
  @HttpCode(201)
  aprobarYPagar(@Body() body: SolicitudIndemnizacion) {
    return this.servicio.aprobarYPagar(body ?? {});
  }

  @Get(':id')
  consultar(@Param('id') id: string) {
    return this.servicio.consultar(id);
  }
}

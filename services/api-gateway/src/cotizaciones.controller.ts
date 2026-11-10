import { Body, Controller, HttpException, Post } from '@nestjs/common';

// Ruta base: el gateway reenvia la cotizacion al microservicio de Cotizacion.
// Aqui todavia NO hay validacion de JWT ni cuota por socio: esas tacticas las
// agregan EXP-010 (JWT) y EXP-008 (cuota) detras de sus propios flags.
@Controller('v1/cotizaciones')
export class CotizacionesController {
  private readonly cotizacionUrl =
    process.env.COTIZACION_URL ?? 'http://localhost:8001';

  @Post()
  async crear(@Body() body: unknown) {
    let respuesta: Response;
    try {
      respuesta = await fetch(`${this.cotizacionUrl}/cotizaciones`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      });
    } catch {
      throw new HttpException('Cotizacion no disponible', 502);
    }
    const datos = await respuesta.json().catch(() => ({}));
    if (!respuesta.ok) throw new HttpException(datos, respuesta.status);
    return datos;
  }
}

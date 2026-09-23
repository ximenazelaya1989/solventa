import { Body, Controller, Get, Post, ServiceUnavailableException } from '@nestjs/common';
import { RatingService } from './rating.service';
import { PublicarReglaDto } from './dto/publicar-regla.dto';
import { AplicarReglaDto } from './dto/aplicar-regla.dto';

@Controller('rating')
export class RatingController {
  constructor(private readonly ratingService: RatingService) {}

  /** Health check sustantivo de ESTA instancia. Lo consulta el target group del ALB. */
  @Get('health')
  health() {
    const estado = this.ratingService.health();
    if (estado.status !== 'ok') {
      throw new ServiceUnavailableException(estado);
    }
    return estado;
  }

  @Get('reglas')
  listarVersiones() {
    return this.ratingService.listarVersiones();
  }

  /** Publica una nueva version en el almacen de configuracion (no la aplica a nadie todavia). */
  @Post('reglas')
  publicar(@Body() datos: PublicarReglaDto) {
    return this.ratingService.publicarNuevaVersion(datos.factores, datos.fallaSanityCheck ?? false);
  }

  /** Le dice A ESTA INSTANCIA que cargue una version especifica (paso del rolling update). */
  @Post('reglas/aplicar')
  aplicar(@Body() datos: AplicarReglaDto) {
    return this.ratingService.aplicarVersion(datos.version);
  }
}
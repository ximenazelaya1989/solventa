import { Body, Controller, Post } from '@nestjs/common';
import { CotizacionService } from './cotizacion.service';
import { CrearCotizacionDto } from './dto/crear-cotizacion.dto';

@Controller('cotizaciones')
export class CotizacionController {
  constructor(private readonly cotizacionService: CotizacionService) {}

  @Post()
  crear(@Body() datos: CrearCotizacionDto) {
    return this.cotizacionService.cotizar(datos);
  }
}
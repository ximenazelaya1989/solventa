import {
  Controller,
  Get,
  HttpCode,
  HttpStatus,
  NotFoundException,
  Param,
  ParseUUIDPipe,
  Post,
  Body,
} from '@nestjs/common';
import { SuscripcionService } from './suscripcion.service';
import { DecidirSuscripcionDto } from './dto/decidir-suscripcion.dto';

@Controller('suscripciones')
export class SuscripcionController {
  constructor(private readonly suscripcionService: SuscripcionService) {}

  @Post()
  @HttpCode(HttpStatus.CREATED)
  async decidir(@Body() datos: DecidirSuscripcionDto) {
    return this.suscripcionService.decidir(datos);
  }

  @Get(':id')
  async buscar(@Param('id', ParseUUIDPipe) id: string) {
    const suscripcion = await this.suscripcionService.buscar(id);
    if (!suscripcion) {
      throw new NotFoundException('Suscripcion no encontrada');
    }
    return suscripcion;
  }
}

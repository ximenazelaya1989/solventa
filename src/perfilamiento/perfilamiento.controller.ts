import { Body, Controller, HttpCode, Post } from '@nestjs/common';
import { ReprocesarPerfilDto } from './dto/reprocesar-perfil.dto';
import { PerfilamientoService } from './perfilamiento.service';

@Controller('perfilamiento')
export class PerfilamientoController {
  constructor(private readonly perfilamientoService: PerfilamientoService) {}

  @Post('reprocesar')
  @HttpCode(200)
  reprocesar(@Body() dto: ReprocesarPerfilDto) {
    return this.perfilamientoService.reprocesar(dto);
  }
}

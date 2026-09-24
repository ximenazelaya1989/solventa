import { Controller } from '@nestjs/common';
import { PerfilamientoService } from './perfilamiento.service';

// TODO(perfilamiento): definir endpoints (calcularPerfil, lectura de perfil) por el dueño del modulo
@Controller('perfilamiento')
export class PerfilamientoController {
  constructor(private readonly perfilamientoService: PerfilamientoService) {}
}

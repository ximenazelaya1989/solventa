import { Controller } from '@nestjs/common';
import { IdentidadService } from './identidad.service';

// TODO(identidad): definir endpoints (registrar, verificarKyc) por el dueño del modulo
@Controller('identidad')
export class IdentidadController {
  constructor(private readonly identidadService: IdentidadService) {}
}

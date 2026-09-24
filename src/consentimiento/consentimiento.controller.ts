import { Controller } from '@nestjs/common';
import { ConsentimientoService } from './consentimiento.service';

// TODO(consentimiento): definir endpoints (otorgar, revocar, consultar) por el dueño del modulo
@Controller('consentimientos')
export class ConsentimientoController {
  constructor(
    private readonly consentimientoService: ConsentimientoService,
  ) {}
}

import { Controller } from '@nestjs/common';
import { SiniestrosService } from './siniestros.service';

// TODO(siniestros): definir endpoints (reportar, asignarPerito, aprobar, eventoParametrico) por el dueño del modulo
@Controller('siniestros')
export class SiniestrosController {
  constructor(private readonly siniestrosService: SiniestrosService) {}
}

import { Controller } from '@nestjs/common';
import { ReporteriaService } from './reporteria.service';

// TODO(reporteria): definir endpoints (generar, enviar) por el dueño del modulo
@Controller('reporteria')
export class ReporteriaController {
  constructor(private readonly reporteriaService: ReporteriaService) {}
}

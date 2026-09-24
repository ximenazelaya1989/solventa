import { Controller } from '@nestjs/common';
import { AnaliticaFraudeService } from './analitica-fraude.service';

// TODO(analitica-fraude): definir endpoints (evaluarSiniestro, bloquearTransaccion) por el dueño del modulo
@Controller('analitica-fraude')
export class AnaliticaFraudeController {
  constructor(
    private readonly analiticaFraudeService: AnaliticaFraudeService,
  ) {}
}

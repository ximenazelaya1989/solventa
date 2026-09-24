import { Controller } from '@nestjs/common';
import { ReaseguroService } from './reaseguro.service';

// TODO(reaseguro): definir endpoints por el dueño del modulo
@Controller('reaseguro')
export class ReaseguroController {
  constructor(private readonly reaseguroService: ReaseguroService) {}
}

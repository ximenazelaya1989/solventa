import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { MotorDeteccionFraude } from './entities/motor-deteccion-fraude.entity';
import { PagosService } from '../pagos/pagos.service';

@Injectable()
export class AnaliticaFraudeService {
  constructor(
    @InjectRepository(MotorDeteccionFraude)
    private readonly motorDeteccionFraudeRepository: Repository<MotorDeteccionFraude>,
    private readonly pagosService: PagosService,
  ) {}

  // TODO(analitica-fraude): implementar por el dueño del modulo (debe responder
  // en menos de 1s, HU6.3.1; regla de deteccion sin definir)
  async evaluarSiniestro(siniestroId: string): Promise<MotorDeteccionFraude> {
    throw new Error('No implementado');
  }

  // TODO(analitica-fraude): implementar por el dueño del modulo (bloqueo <=1s, HU6.3.1)
  async bloquearTransaccion(pagoId: string): Promise<void> {
    throw new Error('No implementado');
  }
}

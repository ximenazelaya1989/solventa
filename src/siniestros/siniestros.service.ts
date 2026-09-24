import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Siniestro } from './entities/siniestro.entity';
import { SiniestroAsistido } from './entities/siniestro-asistido.entity';
import { SiniestroParametrico } from './entities/siniestro-parametrico.entity';
import { Perito } from './entities/perito.entity';
import { PolizasService } from '../polizas/polizas.service';
import { PagosService } from '../pagos/pagos.service';
import { AnaliticaFraudeService } from '../analitica-fraude/analitica-fraude.service';

@Injectable()
export class SiniestrosService {
  constructor(
    @InjectRepository(SiniestroAsistido)
    private readonly siniestroAsistidoRepository: Repository<SiniestroAsistido>,
    @InjectRepository(SiniestroParametrico)
    private readonly siniestroParametricoRepository: Repository<SiniestroParametrico>,
    @InjectRepository(Perito)
    private readonly peritoRepository: Repository<Perito>,
    private readonly polizasService: PolizasService,
    private readonly pagosService: PagosService,
    private readonly analiticaFraudeService: AnaliticaFraudeService,
  ) {}

  // TODO(siniestros): implementar por el dueño del modulo
  async reportar(
    polizaId: string,
    clienteId: string,
  ): Promise<Siniestro> {
    throw new Error('No implementado');
  }

  // TODO(siniestros): implementar por el dueño del modulo (asignacion trazable 100%)
  async asignarPerito(siniestroId: string, peritoId: string): Promise<Siniestro> {
    throw new Error('No implementado');
  }

  // TODO(siniestros): implementar por el dueño del modulo
  async aprobar(siniestroId: string): Promise<Siniestro> {
    throw new Error('No implementado');
  }

  // TODO(siniestros): implementar por el dueño del modulo (HU6.2.1/6.2.2: pago
  // parametrico automatico e idempotente via PagosService.pagarIndemnizacion)
  async eventoParametrico(
    siniestroId: string,
    datosEvento: Record<string, any>,
  ): Promise<Siniestro> {
    throw new Error('No implementado');
  }
}

import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { ReporteRegulatorio } from './entities/reporte-regulatorio.entity';
import { PolizasService } from '../polizas/polizas.service';

@Injectable()
export class ReporteriaService {
  constructor(
    @InjectRepository(ReporteRegulatorio)
    private readonly reporteRegulatorioRepository: Repository<ReporteRegulatorio>,
    private readonly polizasService: PolizasService,
  ) {}

  // TODO(reporteria): implementar por el dueño del modulo (formato ACORD, HU8.3.1/HU8.3.2)
  async generar(destinatario: string, periodoInicio: string, periodoFin: string): Promise<ReporteRegulatorio> {
    throw new Error('No implementado');
  }

  // TODO(reporteria): implementar por el dueño del modulo
  async enviar(reporteId: string): Promise<ReporteRegulatorio> {
    throw new Error('No implementado');
  }
}

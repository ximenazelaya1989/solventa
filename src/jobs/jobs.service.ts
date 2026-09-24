import { Injectable, Logger } from '@nestjs/common';
import { PerfilamientoService } from '../perfilamiento/perfilamiento.service';
import { ReaseguroService } from '../reaseguro/reaseguro.service';
import { ReporteriaService } from '../reporteria/reporteria.service';

@Injectable()
export class JobsService {
  private readonly logger = new Logger(JobsService.name);

  constructor(
    private readonly perfilamientoService: PerfilamientoService,
    private readonly reaseguroService: ReaseguroService,
    private readonly reporteriaService: ReporteriaService,
  ) {}

  // TODO(perfilamiento): recalcularTodos() esta pendiente de implementacion (HU4.3.1)
  async recalcularPerfiles(): Promise<void> {
    await this.perfilamientoService.recalcularTodos();
  }

  // TODO(reaseguro): registrarCesiones() esta pendiente de implementacion
  async generarCesionesReaseguro(): Promise<void> {
    await this.reaseguroService.registrarCesiones();
  }

  // TODO(reporteria): generar()/enviar() estan pendientes de implementacion;
  // definir aqui los parametros de periodo/destinatario por el dueño del modulo
  async generarReportesPeriodicos(): Promise<void> {
    throw new Error('No implementado');
  }

  async ejecutarTodos(): Promise<void> {
    await this.ejecutarJob('recalculo de perfiles', () =>
      this.recalcularPerfiles(),
    );
    await this.ejecutarJob('cesiones de reaseguro', () =>
      this.generarCesionesReaseguro(),
    );
    await this.ejecutarJob('reportes periodicos', () =>
      this.generarReportesPeriodicos(),
    );
  }

  private async ejecutarJob(
    nombre: string,
    job: () => Promise<void>,
  ): Promise<void> {
    this.logger.log(`Iniciando job: ${nombre}`);
    try {
      await job();
      this.logger.log(`Job completado: ${nombre}`);
    } catch (error) {
      this.logger.error(`Fallo el job "${nombre}"`, error as Error);
    }
  }
}

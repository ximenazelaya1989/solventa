import { Injectable } from '@nestjs/common';
import { InjectDataSource, InjectRepository } from '@nestjs/typeorm';
import { DataSource, Repository } from 'typeorm';
import {
  Suscripcion,
  DecisionSuscripcion,
} from './entities/suscripcion.entity';
import { PolizasService } from '../polizas/polizas.service';
import { PagosService } from '../pagos/pagos.service';
import { PerfilamientoService } from '../perfilamiento/perfilamiento.service';
import { Cotizacion } from '../cotizacion/entities/cotizacion.entity';
import { DecidirSuscripcionDto } from './dto/decidir-suscripcion.dto';

// TODO(suscripcion): umbrales configurables por entorno
// (SUSCRIPCION_UMBRAL_APROBACION / SUSCRIPCION_UMBRAL_REVISION) y el resto
// del flujo de decision (respuesta 201/404, GET /suscripciones/:id) se
// definen en el Paso 5
const UMBRAL_APROBADO = 0.8;
const UMBRAL_REVISION_ASISTIDA = 0.5;

const CODIGO_VIOLACION_UNICIDAD_POSTGRES = '23505';

@Injectable()
export class SuscripcionService {
  constructor(
    @InjectRepository(Suscripcion)
    private readonly suscripcionRepository: Repository<Suscripcion>,
    @InjectRepository(Cotizacion)
    private readonly cotizacionRepository: Repository<Cotizacion>,
    @InjectDataSource()
    private readonly dataSource: DataSource,
    private readonly polizasService: PolizasService,
    private readonly pagosService: PagosService,
    private readonly perfilamientoService: PerfilamientoService,
  ) {}

  async decidir(datos: DecidirSuscripcionDto) {
    const existente = await this.suscripcionRepository.findOneBy({
      cotizacionId: datos.cotizacionId,
    });
    if (existente) {
      return { suscripcion: existente, idempotente: true };
    }

    const cotizacion = await this.cotizacionRepository.findOneByOrFail({
      id: datos.cotizacionId,
    });

    const score = cotizacion.perfilRiesgoId
      ? await this.perfilamientoService.obtenerScore(cotizacion.perfilRiesgoId)
      : 0;
    const decision = this.evaluarUmbral(score);

    try {
      return await this.dataSource.transaction(async (manager) => {
        const suscripcionRepo = manager.getRepository(Suscripcion);
        const suscripcion = await suscripcionRepo.save(
          suscripcionRepo.create({
            decision,
            cotizacionId: datos.cotizacionId,
          }),
        );

        if (decision === DecisionSuscripcion.APROBADO) {
          const poliza = await this.polizasService.emitir(manager, {
            clienteId: cotizacion.clienteId,
            productoId: cotizacion.productoId,
          });
          suscripcion.poliza = poliza;
          await suscripcionRepo.save(suscripcion);
          await this.pagosService.cobrarPrima(
            manager,
            poliza.id,
            cotizacion.prima,
          );
          return { suscripcion, poliza, idempotente: false };
        }

        return { suscripcion, idempotente: false };
      });
    } catch (error: any) {
      if (error?.code === CODIGO_VIOLACION_UNICIDAD_POSTGRES) {
        const ganadora = await this.suscripcionRepository.findOneByOrFail({
          cotizacionId: datos.cotizacionId,
        });
        return { suscripcion: ganadora, idempotente: true };
      }
      throw error;
    }
  }

  private evaluarUmbral(score: number): DecisionSuscripcion {
    if (score >= UMBRAL_APROBADO) return DecisionSuscripcion.APROBADO;
    if (score >= UMBRAL_REVISION_ASISTIDA)
      return DecisionSuscripcion.REVISION_ASISTIDA;
    return DecisionSuscripcion.RECHAZADO;
  }
}

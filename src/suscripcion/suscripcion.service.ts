import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectDataSource, InjectRepository } from '@nestjs/typeorm';
import { DataSource, Repository } from 'typeorm';
import {
  Suscripcion,
  DecisionSuscripcion,
} from './entities/suscripcion.entity';
import { Poliza, EstadoPoliza } from '../polizas/entities/poliza.entity';
import { PolizasService } from '../polizas/polizas.service';
import { PagosService } from '../pagos/pagos.service';
import { PerfilamientoService } from '../perfilamiento/perfilamiento.service';
import { Cotizacion } from '../cotizacion/entities/cotizacion.entity';
import { DecidirSuscripcionDto } from './dto/decidir-suscripcion.dto';

const UMBRAL_APROBACION_POR_DEFECTO = 0.7;
const UMBRAL_REVISION_POR_DEFECTO = 0.4;

const CODIGO_VIOLACION_UNICIDAD_POSTGRES = '23505';

export interface RespuestaSuscripcion {
  id: string;
  decision: DecisionSuscripcion;
  polizaId: string | null;
}

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

  async decidir(
    datos: DecidirSuscripcionDto,
  ): Promise<RespuestaSuscripcion & { idempotente: boolean }> {
    const existente = await this.suscripcionRepository.findOne({
      where: { cotizacionId: datos.cotizacionId },
      relations: { poliza: true },
    });
    if (existente) {
      return { ...this.aRespuesta(existente), idempotente: true };
    }

    const cotizacion = await this.cotizacionRepository.findOneBy({
      id: datos.cotizacionId,
    });
    if (!cotizacion) {
      throw new NotFoundException('Cotizacion no encontrada');
    }

    const score = cotizacion.perfilRiesgoId
      ? await this.perfilamientoService.obtenerScore(cotizacion.perfilRiesgoId)
      : 0;
    const decision = this.evaluarUmbral(score);

    try {
      const suscripcion = await this.dataSource.transaction(async (manager) => {
        const suscripcionRepo = manager.getRepository(Suscripcion);
        const nueva = await suscripcionRepo.save(
          suscripcionRepo.create({
            decision,
            cotizacionId: datos.cotizacionId,
          }),
        );

        if (decision === DecisionSuscripcion.RECHAZADO) {
          return nueva;
        }

        if (decision === DecisionSuscripcion.APROBADO) {
          const poliza = await this.polizasService.emitir(manager, {
            clienteId: cotizacion.clienteId,
            productoId: cotizacion.productoId,
          });
          nueva.poliza = poliza;
          await suscripcionRepo.save(nueva);
          await this.pagosService.cobrarPrima(
            manager,
            poliza.id,
            cotizacion.prima,
          );
          return nueva;
        }

        // REVISION_ASISTIDA: poliza pendiente, sin cobro. PolizasService.emitir()
        // siempre deja la poliza EMITIDA, asi que aqui se crea directamente con
        // el estado PENDIENTE (explicito) sin pasar por ese metodo.
        const poliza = await manager.getRepository(Poliza).save(
          manager.getRepository(Poliza).create({
            estado: EstadoPoliza.PENDIENTE,
            clienteId: cotizacion.clienteId,
            productoId: cotizacion.productoId,
          }),
        );
        nueva.poliza = poliza;
        await suscripcionRepo.save(nueva);
        return nueva;
      });

      return { ...this.aRespuesta(suscripcion), idempotente: false };
    } catch (error: any) {
      if (error?.code === CODIGO_VIOLACION_UNICIDAD_POSTGRES) {
        const ganadora = await this.suscripcionRepository.findOneOrFail({
          where: { cotizacionId: datos.cotizacionId },
          relations: { poliza: true },
        });
        return { ...this.aRespuesta(ganadora), idempotente: true };
      }
      throw error;
    }
  }

  async buscar(id: string): Promise<RespuestaSuscripcion | null> {
    const suscripcion = await this.suscripcionRepository.findOne({
      where: { id },
      relations: { poliza: true },
    });
    return suscripcion ? this.aRespuesta(suscripcion) : null;
  }

  private aRespuesta(suscripcion: Suscripcion): RespuestaSuscripcion {
    return {
      id: suscripcion.id,
      decision: suscripcion.decision,
      polizaId: suscripcion.poliza?.id ?? null,
    };
  }

  private evaluarUmbral(score: number): DecisionSuscripcion {
    const umbralAprobacion = this.leerUmbral(
      'SUSCRIPCION_UMBRAL_APROBACION',
      UMBRAL_APROBACION_POR_DEFECTO,
    );
    const umbralRevision = this.leerUmbral(
      'SUSCRIPCION_UMBRAL_REVISION',
      UMBRAL_REVISION_POR_DEFECTO,
    );
    if (score >= umbralAprobacion) return DecisionSuscripcion.APROBADO;
    if (score >= umbralRevision) return DecisionSuscripcion.REVISION_ASISTIDA;
    return DecisionSuscripcion.RECHAZADO;
  }

  // Se lee en cada llamada (no como constante de modulo) porque ConfigModule
  // carga el .env durante el bootstrap de Nest, despues de que este archivo ya
  // se importo -- una constante de modulo siempre veria process.env vacio.
  private leerUmbral(nombreVariable: string, valorPorDefecto: number): number {
    const valor = Number(process.env[nombreVariable]);
    return Number.isFinite(valor) ? valor : valorPorDefecto;
  }
}

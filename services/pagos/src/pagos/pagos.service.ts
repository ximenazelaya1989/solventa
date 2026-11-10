import {
  BadRequestException,
  ConflictException,
  Injectable,
  ServiceUnavailableException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { QueryFailedError, Repository } from 'typeorm';
import { EstadoPago, Pago, TipoPago } from '../entities/pago.entity';
import { PasarelaClient } from './pasarela.client';
import { instancia } from '../common/instancia';

export interface SolicitudDesembolso {
  claveIdempotencia: string;
  siniestroId: string;
  polizaId?: string | null;
  monto: number;
  moneda?: string;
}

export interface ResultadoDesembolso {
  pago: Pago;
  // true cuando la llave ya existia: es un reintento y se devuelve el pago
  // original en lugar de crear otro (tactica de idempotencia, H7.2.1).
  idempotente: boolean;
}

const UNIQUE_VIOLATION = '23505';

// Errores de red o de la BD que indican una falla transitoria (p. ej. la
// conmutacion por error de Aurora): se responden 503 para que Siniestros
// reintente, y no 500.
function esFallaTransitoria(err: unknown): boolean {
  const texto = String((err as Error)?.message ?? err).toLowerCase();
  return [
    'connection',
    'timeout',
    'terminat',
    'econnrefused',
    'econnreset',
    'enotfound',
    'read only',
    'read-only',
    'shutdown',
    'the database system is',
  ].some((p) => texto.includes(p));
}

@Injectable()
export class PagosService {
  // Mismo flag que Siniestros: apagado en la prueba de control.
  private readonly idempotencia =
    process.env.RETRY_IDEMPOTENCY_ENABLED === 'true';

  constructor(
    @InjectRepository(Pago) private readonly pagos: Repository<Pago>,
    private readonly pasarela: PasarelaClient,
  ) {}

  validar(body: Partial<SolicitudDesembolso>): SolicitudDesembolso {
    const { claveIdempotencia, siniestroId, monto } = body;
    if (!claveIdempotencia || typeof claveIdempotencia !== 'string') {
      throw new BadRequestException('claveIdempotencia es obligatoria');
    }
    if (!siniestroId || typeof siniestroId !== 'string') {
      throw new BadRequestException('siniestroId es obligatorio');
    }
    if (typeof monto !== 'number' || !(monto > 0)) {
      throw new BadRequestException('monto debe ser un numero positivo');
    }
    return {
      claveIdempotencia,
      siniestroId,
      polizaId: body.polizaId ?? null,
      monto,
      moneda: body.moneda ?? 'USD',
    };
  }

  async desembolsar(sol: SolicitudDesembolso): Promise<ResultadoDesembolso> {
    try {
      return await this.procesar(sol);
    } catch (err) {
      if (esFallaTransitoria(err)) {
        throw new ServiceUnavailableException(
          `falla transitoria: ${(err as Error).message}`,
        );
      }
      throw err;
    }
  }

  private async procesar(sol: SolicitudDesembolso): Promise<ResultadoDesembolso> {
    // 1. Si la llave ya existe, es un reintento de una orden que este u otra
    //    replica ya recibio.
    if (this.idempotencia) {
      const existente = await this.pagos.findOneBy({
        claveIdempotencia: sol.claveIdempotencia,
      });
      if (existente) return this.completarExistente(existente);
    }

    // 2. Registrar el pago como pendiente. La restriccion UNIQUE decide entre
    //    dos replicas que reciben la misma llave al mismo tiempo.
    let pago: Pago;
    try {
      pago = await this.pagos.save(
        this.pagos.create({
          tipo: TipoPago.INDEMNIZACION,
          monto: sol.monto,
          moneda: sol.moneda ?? 'USD',
          estado: EstadoPago.PENDIENTE,
          claveIdempotencia: sol.claveIdempotencia,
          siniestroId: sol.siniestroId,
          polizaId: sol.polizaId ?? null,
          atendidoPor: instancia(),
        }),
      );
    } catch (err) {
      const codigo = (err as QueryFailedError & { driverError?: { code?: string } })
        .driverError?.code;
      if (codigo === UNIQUE_VIOLATION) {
        if (!this.idempotencia) {
          throw new ConflictException('claveIdempotencia repetida');
        }
        const ganador = await this.pagos.findOneByOrFail({
          claveIdempotencia: sol.claveIdempotencia,
        });
        return this.completarExistente(ganador);
      }
      throw err;
    }

    // 3. Desembolsar en la pasarela (con la misma llave) y confirmar.
    return { pago: await this.confirmar(pago), idempotente: false };
  }

  // Un pago que quedo PENDIENTE (la replica se cayo entre el registro y la
  // confirmacion) se completa ahora; la pasarela, por la llave, no paga doble.
  private async completarExistente(pago: Pago): Promise<ResultadoDesembolso> {
    if (pago.estado === EstadoPago.PENDIENTE) {
      return { pago: await this.confirmar(pago), idempotente: true };
    }
    return { pago, idempotente: true };
  }

  private async confirmar(pago: Pago): Promise<Pago> {
    const tx = await this.pasarela.desembolsar(
      pago.claveIdempotencia,
      pago.monto,
      pago.moneda,
    );
    pago.estado = EstadoPago.PROCESADO;
    pago.referenciaPasarela = tx.transaccionId;
    pago.fechaProcesado = new Date();
    pago.atendidoPor = instancia();
    return this.pagos.save(pago);
  }

  buscarPorClave(claveIdempotencia: string): Promise<Pago | null> {
    return this.pagos.findOneBy({ claveIdempotencia });
  }
}

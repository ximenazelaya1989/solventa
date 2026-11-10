import {
  BadRequestException,
  Injectable,
  NotFoundException,
  ServiceUnavailableException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { randomUUID } from 'crypto';
import { EstadoSiniestro } from '../entities/siniestro.entity';
import { SiniestroAsistido } from '../entities/siniestro-asistido.entity';
import { PagosClient } from './pagos.client';

export interface SolicitudIndemnizacion {
  clienteId?: string;
  polizaId?: string;
  monto?: number;
  moneda?: string;
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

@Injectable()
export class IndemnizacionesService {
  constructor(
    @InjectRepository(SiniestroAsistido)
    private readonly siniestros: Repository<SiniestroAsistido>,
    private readonly pagos: PagosClient,
  ) {}

  // Flujo del experimento: el siniestro se aprueba y se ordena el desembolso.
  // 1. Se registra el siniestro APROBADO con su llave de idempotencia.
  // 2. Se pide el pago a Pagos (con reintentos si el flag esta activo).
  // 3. Solo si Pagos confirma, el siniestro pasa a PAGADO (confirmacion
  //    recibida): es la referencia para verificar cero perdidas.
  async aprobarYPagar(sol: SolicitudIndemnizacion) {
    const clienteId = sol.clienteId ?? randomUUID();
    const polizaId = sol.polizaId ?? randomUUID();
    if (!UUID.test(clienteId) || !UUID.test(polizaId)) {
      throw new BadRequestException('clienteId y polizaId deben ser UUID');
    }
    const monto = sol.monto ?? 1000;
    if (typeof monto !== 'number' || !(monto > 0)) {
      throw new BadRequestException('monto debe ser un numero positivo');
    }
    const moneda = sol.moneda ?? 'USD';

    const id = randomUUID();
    const clave = `IND-${id}`;
    await this.siniestros.insert({
      id,
      clienteId,
      polizaId,
      estado: EstadoSiniestro.APROBADO,
      montoIndemnizacion: monto,
      claveIdempotenciaPago: clave,
    });

    const r = await this.pagos.pagar({
      claveIdempotencia: clave,
      siniestroId: id,
      polizaId,
      monto,
      moneda,
    });

    if (!r.ok || !r.confirmacion) {
      await this.siniestros.update(id, { intentosPago: r.intentos });
      throw new ServiceUnavailableException({
        siniestroId: id,
        claveIdempotencia: clave,
        estado: EstadoSiniestro.APROBADO,
        intentos: r.intentos,
        error: r.ultimoError,
        mensaje: 'No se pudo completar el desembolso',
      });
    }

    await this.siniestros.update(id, {
      estado: EstadoSiniestro.PAGADO,
      fechaPago: new Date(),
      pagoId: r.confirmacion.pagoId,
      intentosPago: r.intentos,
    });

    return {
      siniestroId: id,
      claveIdempotencia: clave,
      estado: EstadoSiniestro.PAGADO,
      pagoId: r.confirmacion.pagoId,
      intentos: r.intentos,
      duracionMs: r.duracionMs,
      atendidoPor: r.confirmacion.atendidoPor,
      reintentosActivos: this.pagos.reintentosActivos,
    };
  }

  async consultar(id: string) {
    const s = await this.siniestros.findOneBy({ id });
    if (!s) throw new NotFoundException();
    return s;
  }
}

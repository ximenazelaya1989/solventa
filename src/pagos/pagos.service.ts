import { Injectable } from '@nestjs/common';
import { EntityManager } from 'typeorm';
import { Pago, TipoPago, EstadoPago } from './entities/pago.entity';

@Injectable()
export class PagosService {
  // TODO(pagos): procesar() y conciliar() (llamada a la pasarela fuera de la
  // transaccion) se definen en el Paso 5
  async cobrarPrima(
    manager: EntityManager,
    polizaId: string,
    monto: number,
  ): Promise<Pago> {
    return this.insertarIdempotente(manager, {
      tipo: TipoPago.COBRO_PRIMA,
      monto,
      polizaId,
      siniestroId: null,
      claveIdempotencia: `prima:${polizaId}`,
    });
  }

  async pagarIndemnizacion(
    manager: EntityManager,
    siniestroId: string,
    monto: number,
  ): Promise<Pago> {
    return this.insertarIdempotente(manager, {
      tipo: TipoPago.INDEMNIZACION,
      monto,
      polizaId: null,
      siniestroId,
      claveIdempotencia: `indem:${siniestroId}`,
    });
  }

  private async insertarIdempotente(
    manager: EntityManager,
    datos: {
      tipo: TipoPago;
      monto: number;
      polizaId: string | null;
      siniestroId: string | null;
      claveIdempotencia: string;
    },
  ): Promise<Pago> {
    await manager
      .createQueryBuilder()
      .insert()
      .into(Pago)
      .values({
        ...datos,
        moneda: 'USD', // TODO(pagos): definir moneda por el dueño del modulo
        estado: EstadoPago.PENDIENTE,
      })
      .orIgnore()
      .execute();

    return manager
      .getRepository(Pago)
      .findOneByOrFail({ claveIdempotencia: datos.claveIdempotencia });
  }
}

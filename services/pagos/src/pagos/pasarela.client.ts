import { Injectable } from '@nestjs/common';

export interface RespuestaPasarela {
  transaccionId: string;
  repetida: boolean;
}

// Cliente de la pasarela de pagos externa (en el experimento, un mock).
// Envia la misma llave de idempotencia de la orden: si Pagos se cae despues de
// que la pasarela pago pero antes de confirmar, el reintento no cobra dos veces.
@Injectable()
export class PasarelaClient {
  private readonly url = process.env.PASARELA_URL;
  private readonly timeoutMs = Number(process.env.PASARELA_TIMEOUT_MS ?? 2000);

  async desembolsar(
    claveIdempotencia: string,
    monto: number,
    moneda: string,
  ): Promise<RespuestaPasarela> {
    // Sin PASARELA_URL (p. ej. con el docker-compose general del equipo) se
    // simula la aprobacion para que el servicio siga funcionando solo.
    if (!this.url) {
      return { transaccionId: `sim-${claveIdempotencia}`, repetida: false };
    }
    const res = await fetch(`${this.url}/desembolsos`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'idempotency-key': claveIdempotencia,
      },
      body: JSON.stringify({ monto, moneda }),
      signal: AbortSignal.timeout(this.timeoutMs),
    });
    if (!res.ok) {
      throw new Error(`pasarela respondio ${res.status}`);
    }
    return (await res.json()) as RespuestaPasarela;
  }
}
